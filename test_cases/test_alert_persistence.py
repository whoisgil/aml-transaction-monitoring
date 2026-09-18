import json

from classes.db_connect import DB_Connect
from functions.alert_functions import persistAlerts


DB_USERNAME = "root"
DB_PASSWORD = ""
DB_NAME = "sar_project"

TEST_RULE_CODE = "TEST-RULE-ALERT-PERSIST"
TEST_RULE_VERSION = "test-1.0"
TEST_AS_OF_STEP = -1
TEST_MATCHED_ACCOUNT = "TEST-ACCOUNT"

SAMPLE_RESULT = [{
    "matched_account": TEST_MATCHED_ACCOUNT,
    "matching_tx_ids": [1, 2, 3],
    "rule_code": TEST_RULE_CODE,
    "reason": "Test evidence for alert persistence",
    "threshold": 3,
    "observed_value": 3,
}]


def test_valid_alert_persistence_prevents_duplicate_run():
    db = DB_Connect(DB_USERNAME, DB_PASSWORD, DB_NAME)

    cleanup_sql = """
        DELETE FROM alerts
        WHERE rule_code = %s
        AND rule_version = %s
        AND as_of_step = %s
        AND matched_account = %s
    """
    alert_identity = (
        TEST_RULE_CODE,
        TEST_RULE_VERSION,
        TEST_AS_OF_STEP,
        TEST_MATCHED_ACCOUNT,
    )

    # A distinct test identity keeps cleanup isolated from genuine rule alerts.
    try:
        db.executeQuery(cleanup_sql, alert_identity)
        db.conn.commit()

        first_inserted = persistAlerts(
            db,
            SAMPLE_RESULT,
            TEST_RULE_VERSION,
            TEST_AS_OF_STEP,
        )
        duplicate_inserted = persistAlerts(
            db,
            SAMPLE_RESULT,
            TEST_RULE_VERSION,
            TEST_AS_OF_STEP,
        )

        rows = db.executeSelectQuery(
            """
                SELECT rule_code, rule_version, as_of_step, matched_account,
                        matching_tx_ids, reason, threshold, observed_value,
                        status, created_at, updated_at
                FROM alerts
                WHERE rule_code = %s
                    AND rule_version = %s
                    AND as_of_step = %s
                    AND matched_account = %s
            """,
            alert_identity,
        )

        assert first_inserted == 1
        assert duplicate_inserted == 0
        assert len(rows) == 1

        alert = rows[0]
        assert alert["rule_code"] == TEST_RULE_CODE
        assert alert["rule_version"] == TEST_RULE_VERSION
        assert alert["as_of_step"] == TEST_AS_OF_STEP
        assert alert["matched_account"] == TEST_MATCHED_ACCOUNT
        assert json.loads(alert["matching_tx_ids"]) == [1, 2, 3]
        assert alert["reason"] == SAMPLE_RESULT[0]["reason"]
        assert alert["threshold"] == 3
        assert alert["observed_value"] == 3
        assert alert["status"] == "OPEN"
        assert alert["created_at"] is not None
        assert alert["updated_at"] is not None
    finally:
        if db.conn:
            db.executeQuery(cleanup_sql, alert_identity)
            db.conn.commit()
            db.close_connection()