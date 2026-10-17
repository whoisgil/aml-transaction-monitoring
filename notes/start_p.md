# Day 3 — complete. Next up: Day 4.

Day 3 objective (`objectives_list.txt`, row "3 | Detection Rule #1 + tests")
is fully done. Full detail lives in `notes/Day_3_091226.txt`:

- `RULE-001-VELOCITY` implemented in `functions/detection_functions.py`:
  `fetchTransactionsForVelocityRule` (rule-owned query, no window filtering)
  and `detectVelocityRule` (rolling 24-step window, inclusive boundary,
  >= 10 threshold, structured evidence result per the Day 2 spec).
- Tests in `test_cases/test_velocity_rule.py` (pytest style) and
  `test_cases/test_velocity_rule_unittest.py` (unittest.TestCase style) —
  matching, non-matching, boundary-in, boundary-out, direction guard.
  9/9 passing.
- PaySim's `isFraud`/`isFlaggedFraud` are not read anywhere in the rule
  logic, per the objective's requirement.

## Next session — Day 4 (`objectives_list.txt` row 4): Alert persistence

1. Add an `ALERT` table: status, timestamps, rule code/version, and the
   supporting evidence fields `detectVelocityRule` already returns
   (matched_account, matching_tx_ids, reason, threshold, observed_value).
2. Persist each `RULE-001-VELOCITY` result from a detection run into
   `ALERT`.
3. Prevent the same detection run from creating duplicate alerts —
   likely a uniqueness check similar in spirit to the duplicate-load
   guard already built in `sar_main.py` for transactions.
4. Add an integration test covering the persistence + duplicate-prevention
   path.

# Day 5 — complete. Next up: Day 6.

Day 5 objective (`objectives_list.txt`, row "5 | Case and analyst workflow")
is fully done. Full detail lives in `notes/Day_5_100726.txt`:

- Added `cases`, `case_alerts`, and `case_notes` for grouping alerts and
  preserving analyst review history.
- Alerts for the same matched account share one active case. Alert assignment
  and the CASED status commit together so failed attempts do not leave partial
  workflow data.
- Added OPEN, IN_REVIEW, and CLOSED case statuses, named analyst notes, and
  SAR_FILED or NO_SAR dispositions.
- Closed cases reject later notes and preserve the original disposition.
- Full automated test suite: 24 tests passing.

## Next session — Day 6 (`objectives_list.txt` row 6): Investigation interface

Choose Flask or Streamlit and build a case-first review queue and detail view
showing grouped alerts, involved accounts, related transactions, rule evidence,
and persisted analyst actions.
