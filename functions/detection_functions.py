# velocity detection rule
RULE_CODE = "RULE-001-VELOCITY"
WINDOW_STEPS = 24
THRESHOLD = 10


def fetchTransactionsForVelocityRule(passed_db):
    """Fetches transactions needed for the velocity rule."""

    select_sql = """
        SELECT id, step, type, amount, nameDest
        FROM transactions
        ORDER BY step
    """

    return passed_db.executeSelectQuery(select_sql)


def detectVelocityRule(passed_transactions, passed_as_of_step=None):
    """Checks for accounts with multiple incoming transactions."""

    if not passed_transactions:
        return []

    if passed_as_of_step is None:
        passed_as_of_step = max(row["step"] for row in passed_transactions)

    window_start = passed_as_of_step - WINDOW_STEPS

    accounts = {}
    for row in passed_transactions:
        if row["step"] < window_start or row["step"] > passed_as_of_step:
            continue
        accounts.setdefault(row["nameDest"], []).append(row)


    results = []
    for name_dest, rows in accounts.items():
        observed_value = len(rows)
        if observed_value < THRESHOLD:
            continue
        results.append({
            "matched_account": name_dest,
            "matching_tx_ids": [row["id"] for row in rows],
            "rule_code": RULE_CODE,
            "reason": f"{observed_value} incoming transactions to {name_dest} within {WINDOW_STEPS} steps",
            "threshold": THRESHOLD,
            "observed_value": observed_value,
        })

    return results

    