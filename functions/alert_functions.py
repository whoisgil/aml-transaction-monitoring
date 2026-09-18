import json


def persistAlerts(passed_db, passed_results, passed_rule_version, passed_as_of_step):
    """Persists detection results once per logical rule run."""

    if not passed_results:
        return 0

    insert_sql = """
        INSERT INTO alerts
            (rule_code, rule_version, as_of_step, matched_account,
            matching_tx_ids, reason, threshold, observed_value)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE id = id
    """

    rows_to_insert = [
        (
            result["rule_code"],
            passed_rule_version,
            passed_as_of_step,
            result["matched_account"],
            json.dumps(result["matching_tx_ids"]),
            result["reason"],
            result["threshold"],
            result["observed_value"],
        )
        for result in passed_results
    ]

    inserted_count = passed_db.executeManyQuery(insert_sql, rows_to_insert)
    passed_db.conn.commit()

    return inserted_count