# Day 6 — complete. Next up: Day 7.

Day 6 objective (`objectives_list.txt`, row "6 | Investigation interface")
is fully done. Full detail lives in `notes/Day_6_101726.txt`:

- Chose Streamlit and added a case-first review queue with optional visibility
  for closed cases.
- Added case detail views showing grouped alerts, decoded rule evidence,
  involved accounts, related evidence transactions, and analyst history.
- Added persisted analyst actions for moving cases into review, saving notes,
  and recording confirmed SAR_FILED or NO_SAR dispositions.
- Status changes and their named audit notes commit or roll back together.
- Updated detection runs to group open alerts into cases automatically, while
  allowing an interrupted grouping run to resume safely.
- Added pinned dependencies and expanded the automated suite to 34 tests
  covering detection, persistence, case workflow, and investigation queries.

## Next session — Day 7 (`objectives_list.txt` row 7): Additional rules

1. Add two or three typologies through the same structured detection and alert
   persistence interfaces used by RULE-001-VELOCITY.
2. Add focused matching, non-matching, and boundary tests for each rule.
3. Evaluate rule results against PaySim's fraud labels without using those
   labels as detection inputs.
4. Tune thresholds from the evaluation and document expected false positives
   and dataset limitations.
