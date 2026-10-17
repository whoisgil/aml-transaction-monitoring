import pytest

from classes.db_connect import DB_Connect
from functions.alert_functions import persistAlerts
from functions.case_functions import (
    addCaseNote, linkAlertToCase, recordDisposition, 
    groupAlertsIntoCases, updateCaseStatus
)


DB_USERNAME = "root"
DB_PASSWORD = ""
DB_NAME = "sar_project"

# A distinct test identity keeps cleanup isolated from genuine alerts and cases.
TEST_RULE_CODE = "TEST-RULE-CASE-WORKFLOW"
TEST_RULE_VERSION = "test-1.0"
TEST_ACCOUNT = "TEST-CASE-ACCOUNT"
TEST_ANALYST = "test-analyst"


def insertTestAlerts(passed_db, passed_steps):
    """Inserts one test alert per step and returns their ids."""

    # Each alert uses a different step because step is part of the alert unique key.
    for step in passed_steps:
        persistAlerts(
            passed_db,
            [{
                "matched_account": TEST_ACCOUNT,
                "matching_tx_ids": [1, 2, 3],
                "rule_code": TEST_RULE_CODE,
                "reason": "Test evidence for case workflow",
                "threshold": 3,
                "observed_value": 3,
            }],
            TEST_RULE_VERSION,
            step,
        )

    rows = passed_db.executeSelectQuery(
        """
            SELECT id
            FROM alerts
            WHERE matched_account = %s
                AND rule_code = %s
                AND rule_version = %s
            ORDER BY id
        """,
        (
            TEST_ACCOUNT,
            TEST_RULE_CODE,
            TEST_RULE_VERSION,
        ),
    )

    return [row["id"] for row in rows]


def cleanupTestData(passed_db):
    """Deletes test rows in foreign-key order."""

    case_ids_sql = "SELECT id FROM cases WHERE matched_account = %s"

    # Child rows are removed first because they reference cases and alerts.
    passed_db.executeQuery(
        f"DELETE FROM case_notes WHERE case_id IN ({case_ids_sql})",
        (TEST_ACCOUNT,),
    )
    passed_db.executeQuery(
        f"DELETE FROM case_alerts WHERE case_id IN ({case_ids_sql})",
        (TEST_ACCOUNT,),
    )
    passed_db.executeQuery(
        "DELETE FROM cases WHERE matched_account = %s", (TEST_ACCOUNT,)
    )
    passed_db.executeQuery(
        """
            DELETE FROM alerts
            WHERE matched_account = %s
                AND rule_code = %s
                AND rule_version = %s
        """,
        (
            TEST_ACCOUNT,
            TEST_RULE_CODE,
            TEST_RULE_VERSION,
        ),
    )
    passed_db.conn.commit()


def test_valid_alerts_for_same_account_share_one_case():
    """Verifies alerts for the same account share one active case."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        first_id, second_id = insertTestAlerts(db, [-1, -2])

        first_case = linkAlertToCase(db, first_id)
        second_case = linkAlertToCase(db, second_id)

        alerts = db.executeSelectQuery(
            """
                SELECT id, status
                FROM alerts
                WHERE id IN (%s, %s)
                ORDER BY id
            """,
            (first_id, second_id),
        )

        cases = db.executeSelectQuery(
            "SELECT * FROM cases WHERE matched_account = %s",
            (TEST_ACCOUNT,),
        )

        links = db.executeSelectQuery(
            """
                SELECT case_id, alert_id
                FROM case_alerts
                WHERE case_id = %s
                ORDER BY alert_id
            """,
            (first_case,),
        )

        assert first_case is not None
        assert first_case == second_case
        assert all(alert["status"] == "CASED" for alert in alerts)

        assert len(cases) == 1
        assert cases[0]["status"] == "OPEN"
        assert cases[0]["opened_at"] is not None

        assert len(links) == 2
        assert {link["alert_id"] for link in links} == {
            first_id,
            second_id,
        }
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()


def test_invalid_alert_cannot_be_linked_twice():
    """Verifies an already linked alert is not linked again."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        alert_id = insertTestAlerts(db, [-1])[0]

        first_link = linkAlertToCase(db, alert_id)
        second_link = linkAlertToCase(db, alert_id)

        links = db.executeSelectQuery(
            "SELECT case_id FROM case_alerts WHERE alert_id = %s",
            (alert_id,),
        )

        assert first_link is not None
        assert second_link is None
        assert len(links) == 1
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()


def test_valid_disposition_records_analyst_and_closes_case():
    """Verifies a disposition records the analyst and closes the case."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        alert_id = insertTestAlerts(db, [-1])[0]
        case_id = linkAlertToCase(db, alert_id)

        addCaseNote(db, case_id, TEST_ANALYST, "Reviewed incoming velocity.")
        recordDisposition(db, case_id, TEST_ANALYST, "NO_SAR")

        case = db.executeSelectQuery(
            "SELECT * FROM cases WHERE id = %s", (case_id,)
        )[0]
        notes = db.executeSelectQuery(
            "SELECT * FROM case_notes WHERE case_id = %s", (case_id,)
        )

        assert case["status"] == "CLOSED"
        assert case["disposition"] == "NO_SAR"
        assert case["disposition_by"] == TEST_ANALYST
        assert case["closed_at"] is not None
        assert len(notes) == 1
        assert notes[0]["analyst"] == TEST_ANALYST
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()


def test_invalid_disposition_rejected():
    """Verifies an unknown disposition raises ValueError."""

    # No database is needed because validation runs before any query.
    with pytest.raises(ValueError):
        recordDisposition(None, 1, TEST_ANALYST, "MAYBE")

def test_valid_grouping_processes_all_open_alerts(monkeypatch):
    """Verifies batch grouping processes each selected alert once."""

    class FakeDB:
        def __init__(self):
            """Initializes the number of simulated alert queries."""

            self.query_count = 0

        def executeSelectQuery(self, passed_query):
            """Returns open alerts only for the first simulated query."""

            self.query_count += 1

            if self.query_count == 1:
                return [{"id": 101}, {"id": 102}]

            return []

    linked_alert_ids = []

    def fakeLinkAlertToCase(passed_db, passed_alert_id):
        """Records each alert selected for simulated case grouping."""

        linked_alert_ids.append(passed_alert_id)
        return 1

    monkeypatch.setattr(
        "functions.case_functions.linkAlertToCase",
        fakeLinkAlertToCase,
    )

    fake_db = FakeDB()

    first_count = groupAlertsIntoCases(fake_db)
    second_count = groupAlertsIntoCases(fake_db)

    assert first_count == 2
    assert second_count == 0
    assert linked_alert_ids == [101, 102]

def test_valid_status_moves_case_into_review():
    """Verifies an active case can move into analyst review."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        alert_id = insertTestAlerts(db, [-1])[0]
        case_id = linkAlertToCase(db, alert_id)

        status_changed = updateCaseStatus(
            db,
            case_id,
            "IN_REVIEW",
            TEST_ANALYST,
        )

        case = db.executeSelectQuery(
            "SELECT status FROM cases WHERE id = %s",
            (case_id,),
        )[0]
        notes = db.executeSelectQuery(
            """
                SELECT analyst, note
                FROM case_notes
                WHERE case_id = %s
            """,
            (case_id,),
        )

        assert status_changed is True
        assert case["status"] == "IN_REVIEW"
        assert notes == [{
            "analyst": TEST_ANALYST,
            "note": "Changed case status to IN_REVIEW.",
        }]
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()

@pytest.mark.parametrize("invalid_note", ["", "   "])
def test_invalid_blank_note_rejected(invalid_note):
    """Verifies an analyst cannot add an empty case note."""

    with pytest.raises(ValueError):
        addCaseNote(None, 1, TEST_ANALYST, invalid_note)

@pytest.mark.parametrize("invalid_analyst", ["", "   "])
def test_invalid_blank_note_analyst_rejected(invalid_analyst):
    """Verifies every case note identifies its analyst."""

    with pytest.raises(ValueError):
        addCaseNote(None, 1, invalid_analyst, "Reviewed alert evidence.")

def test_invalid_second_disposition_does_not_overwrite_first():
    """Verifies a closed case keeps its original disposition."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        alert_id = insertTestAlerts(db, [-1])[0]
        case_id = linkAlertToCase(db, alert_id)

        first_recorded = recordDisposition(
            db,
            case_id,
            TEST_ANALYST,
            "NO_SAR",
        )
        second_recorded = recordDisposition(
            db,
            case_id,
            "second-analyst",
            "SAR_FILED",
        )

        case = db.executeSelectQuery(
            """
                SELECT status, disposition, disposition_by
                FROM cases
                WHERE id = %s
            """,
            (case_id,),
        )[0]

        assert first_recorded is True
        assert second_recorded is False
        assert case["status"] == "CLOSED"
        assert case["disposition"] == "NO_SAR"
        assert case["disposition_by"] == TEST_ANALYST
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()

def test_valid_new_alert_after_closure_opens_new_case():
    """Verifies later activity opens a new case after closure."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)

        first_alert_id = insertTestAlerts(db, [-1])[0]
        first_case_id = linkAlertToCase(db, first_alert_id)

        disposition_recorded = recordDisposition(
            db,
            first_case_id,
            TEST_ANALYST,
            "NO_SAR",
        )

        alert_ids = insertTestAlerts(db, [-2])
        second_alert_id = alert_ids[-1]
        second_case_id = linkAlertToCase(db, second_alert_id)

        assert disposition_recorded is True
        assert second_case_id is not None
        assert second_case_id != first_case_id
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()

def test_invalid_closed_case_rejects_new_note():
    """Verifies a closed case cannot receive another analyst note."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        alert_id = insertTestAlerts(db, [-1])[0]
        case_id = linkAlertToCase(db, alert_id)

        recordDisposition(
            db,
            case_id,
            TEST_ANALYST,
            "NO_SAR",
        )

        note_added = addCaseNote(
            db,
            case_id,
            TEST_ANALYST,
            "Attempted note after closure.",
        )

        notes = db.executeSelectQuery(
            "SELECT id FROM case_notes WHERE case_id = %s",
            (case_id,),
        )

        assert note_added is False
        assert notes == ()
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()

def test_valid_closed_case_alerts_remain_cased():
    """Verifies closing a case does not change its alert assignment."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        alert_id = insertTestAlerts(db, [-1])[0]
        case_id = linkAlertToCase(db, alert_id)

        recordDisposition(
            db,
            case_id,
            TEST_ANALYST,
            "NO_SAR",
        )

        alert = db.executeSelectQuery(
            "SELECT status FROM alerts WHERE id = %s",
            (alert_id,),
        )[0]

        case = db.executeSelectQuery(
            "SELECT status FROM cases WHERE id = %s",
            (case_id,),
        )[0]

        assert alert["status"] == "CASED"
        assert case["status"] == "CLOSED"
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()
