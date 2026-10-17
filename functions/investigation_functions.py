import json


def collectEvidenceTxIds(passed_alerts):
    """Returns the unique transaction ids cited by a list of alerts."""

    tx_ids = set()

    for alert in passed_alerts:
        tx_ids.update(alert["matching_tx_ids"])

    return sorted(tx_ids)


def collectSendingAccounts(passed_transactions):
    """Returns the distinct sending accounts in a case's evidence transactions."""

    return sorted({row["nameOrig"] for row in passed_transactions})


def fetchCaseQueue(passed_db, passed_include_closed=False):
    """Returns cases with alert counts for the review queue."""

    # The include flag is passed as a value so the query stays parameterized.
    # Active cases sort first, then the cases with the most supporting alerts.
    return passed_db.executeSelectQuery(
        """
            SELECT c.id, c.matched_account, c.status, c.disposition,
                    c.opened_at,
                    COUNT(ca.alert_id) AS alert_count,
                    MAX(a.observed_value) AS peak_observed
            FROM cases c
            LEFT JOIN case_alerts ca ON ca.case_id = c.id
            LEFT JOIN alerts a ON a.id = ca.alert_id
            WHERE %s OR c.status != 'CLOSED'
            GROUP BY c.id, c.matched_account, c.status, c.disposition,
                    c.opened_at
            ORDER BY c.status = 'CLOSED', alert_count DESC,
                    peak_observed DESC, c.opened_at, c.id
        """,
        (passed_include_closed,),
    )


def fetchCase(passed_db, passed_case_id):
    """Returns one case, or None if the id does not exist."""

    rows = passed_db.executeSelectQuery(
        "SELECT * FROM cases WHERE id = %s",
        (passed_case_id,),
    )

    if not rows:
        return None

    return rows[0]


def fetchCaseAlerts(passed_db, passed_case_id):
    """Returns the alerts linked to a case with decoded rule evidence."""

    rows = passed_db.executeSelectQuery(
        """
            SELECT a.id, a.rule_code, a.rule_version, a.as_of_step,
                    a.reason, a.threshold, a.observed_value,
                    a.matching_tx_ids, a.created_at
            FROM case_alerts ca
            JOIN alerts a ON a.id = ca.alert_id
            WHERE ca.case_id = %s
            ORDER BY a.id
        """,
        (passed_case_id,),
    )

    # Evidence is stored as JSON text, so it is decoded once here for every caller.
    for row in rows:
        row["matching_tx_ids"] = json.loads(row["matching_tx_ids"])

    return rows


def fetchCaseTransactions(passed_db, passed_case_id):
    """Returns every transaction cited as evidence by a case's alerts."""

    tx_ids = collectEvidenceTxIds(fetchCaseAlerts(passed_db, passed_case_id))

    if not tx_ids:
        return []

    # One placeholder per id keeps the IN list parameterized.
    placeholders = ", ".join(["%s"] * len(tx_ids))

    return passed_db.executeSelectQuery(
        f"""
            SELECT id, step, type, amount, nameOrig, nameDest
            FROM transactions
            WHERE id IN ({placeholders})
            ORDER BY step, id
        """,
        tuple(tx_ids),
    )


def fetchCaseNotes(passed_db, passed_case_id):
    """Returns a case's analyst notes, oldest first."""

    # Notes saved within the same second share a timestamp, so id breaks the tie.
    return passed_db.executeSelectQuery(
        """
            SELECT analyst, note, created_at
            FROM case_notes
            WHERE case_id = %s
            ORDER BY created_at, id
        """,
        (passed_case_id,),
    )