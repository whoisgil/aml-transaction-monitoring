from classes.db_connect import DB_Connect
from functions.alert_functions import persistAlerts
from functions.case_functions import (
    addCaseNote, linkAlertToCase, recordDisposition
)
from functions.investigation_functions import (
    collectEvidenceTxIds, collectSendingAccounts, fetchCase,
    fetchCaseAlerts, fetchCaseNotes, fetchCaseQueue,
    fetchCaseTransactions
)


DB_USERNAME = "root"
DB_PASSWORD = ""
DB_NAME = "sar_project"

# A distinct test identity keeps cleanup isolated from genuine alerts and cases.
TEST_RULE_CODE = "TEST-RULE-INVESTIGATION"
TEST_RULE_VERSION = "test-1.0"
TEST_ACCOUNT = "TEST-INVEST-ACCT"
TEST_ANALYST = "test-analyst"
TEST_TX_ORIGIN = "TEST-INVEST-SENDER"


def insertTestAlerts(passed_db, passed_steps, passed_tx_ids=None):
    """Inserts one test alert per step and returns their ids."""

    matching_tx_ids = passed_tx_ids or [1, 2, 3]

    # Each alert uses a different step because step is part of the alert unique key.
    for step in passed_steps:
        persistAlerts(
            passed_db,
            [{
                "matched_account": TEST_ACCOUNT,
                "matching_tx_ids": matching_tx_ids,
                "rule_code": TEST_RULE_CODE,
                "reason": "Test evidence for investigation queries",
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


def insertTestTransactions(passed_db):
    """Inserts two isolated evidence transactions and returns their ids."""

    tx_ids = []

    for step, amount in [(-100, "10.00"), (-101, "20.00")]:
        passed_db.executeQuery(
            """
                INSERT INTO transactions
                    (step, type, amount, nameOrig, nameDest,
                    isFraud, isFlaggedFraud)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                step,
                "TRANSFER",
                amount,
                TEST_TX_ORIGIN,
                TEST_ACCOUNT,
                0,
                0,
            ),
        )
        tx_ids.append(passed_db.conn.insert_id())

    passed_db.conn.commit()
    return tx_ids


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
    passed_db.executeQuery(
        """
            DELETE FROM transactions
            WHERE nameOrig = %s AND nameDest = %s
        """,
        (TEST_TX_ORIGIN, TEST_ACCOUNT),
    )
    passed_db.conn.commit()


def test_valid_evidence_ids_merge_without_duplicates():
    """Verifies overlapping alert evidence returns each transaction id once."""

    alerts = [
        {"matching_tx_ids": [3, 1, 2]},
        {"matching_tx_ids": [2, 4]},
    ]

    assert collectEvidenceTxIds(alerts) == [1, 2, 3, 4]


def test_valid_no_alerts_produce_no_evidence_ids():
    """Verifies an empty alert list returns no transaction ids."""

    assert collectEvidenceTxIds([]) == []


def test_valid_sending_accounts_are_unique():
    """Verifies sending accounts are the distinct nameOrig values."""

    transactions = [
        {"nameOrig": "C2"},
        {"nameOrig": "C1"},
        {"nameOrig": "C2"},
    ]

    assert collectSendingAccounts(transactions) == ["C1", "C2"]


def test_valid_queue_counts_linked_alerts():
    """Verifies the queue reports every alert linked to a case."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        first_id, second_id = insertTestAlerts(db, [-1, -2])

        case_id = linkAlertToCase(db, first_id)
        linkAlertToCase(db, second_id)

        queue = fetchCaseQueue(db)
        case_rows = [row for row in queue if row["id"] == case_id]

        assert len(case_rows) == 1
        assert case_rows[0]["matched_account"] == TEST_ACCOUNT
        assert case_rows[0]["alert_count"] == 2
        assert case_rows[0]["peak_observed"] == 3
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()


def test_valid_case_alerts_return_decoded_evidence():
    """Verifies alert evidence is returned as a list rather than JSON text."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        alert_id = insertTestAlerts(db, [-1])[0]
        case_id = linkAlertToCase(db, alert_id)

        alerts = fetchCaseAlerts(db, case_id)

        assert len(alerts) == 1
        assert alerts[0]["id"] == alert_id
        assert alerts[0]["matching_tx_ids"] == [1, 2, 3]
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()


def test_valid_fetch_case_returns_case_and_missing_id_returns_none():
    """Verifies case lookup returns one case or None when it does not exist."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        alert_id = insertTestAlerts(db, [-1])[0]
        case_id = linkAlertToCase(db, alert_id)

        case = fetchCase(db, case_id)

        assert case["id"] == case_id
        assert case["matched_account"] == TEST_ACCOUNT
        assert fetchCase(db, 0) is None
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()


def test_valid_case_transactions_return_unique_evidence_in_step_order():
    """Verifies shared evidence transactions appear once in investigation order."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        first_tx_id, second_tx_id = insertTestTransactions(db)
        first_alert_id, second_alert_id = insertTestAlerts(
            db,
            [-1, -2],
            [first_tx_id, second_tx_id],
        )
        case_id = linkAlertToCase(db, first_alert_id)
        linkAlertToCase(db, second_alert_id)

        transactions = fetchCaseTransactions(db, case_id)

        assert [row["id"] for row in transactions] == [
            second_tx_id,
            first_tx_id,
        ]
        assert len(transactions) == 2
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()


def test_invalid_closed_case_excluded_from_default_queue():
    """Verifies closed cases appear only when explicitly requested."""

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

        default_ids = [row["id"] for row in fetchCaseQueue(db)]
        all_ids = [
            row["id"]
            for row in fetchCaseQueue(db, passed_include_closed=True)
        ]

        assert case_id not in default_ids
        assert case_id in all_ids
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()


def test_valid_close_without_open_connection():
    """Verifies closing an unused database wrapper is safe."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    db.close_connection()

    assert db.conn is None


def test_valid_case_notes_return_oldest_first():
    """Verifies notes are returned in the order analysts wrote them."""

    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    try:
        cleanupTestData(db)
        alert_id = insertTestAlerts(db, [-1])[0]
        case_id = linkAlertToCase(db, alert_id)

        addCaseNote(db, case_id, TEST_ANALYST, "First review note.")
        addCaseNote(db, case_id, TEST_ANALYST, "Second review note.")

        notes = fetchCaseNotes(db, case_id)

        assert [note["note"] for note in notes] == [
            "First review note.",
            "Second review note.",
        ]
    finally:
        if db.conn:
            cleanupTestData(db)
            db.close_connection()
