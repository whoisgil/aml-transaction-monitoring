from functions.detection_functions import detectVelocityRule, THRESHOLD, WINDOW_STEPS


def test_valid_threshold_met():
    rows = [{"id": i, "step": 10, "nameDest": "C1"} for i in range(THRESHOLD)]
    results = detectVelocityRule(rows, passed_as_of_step=10)

    assert len(results) == 1
    assert results[0]["matched_account"] == "C1"
    assert results[0]["observed_value"] == THRESHOLD


def test_invalid_below_threshold():
    rows = [{"id": i, "step": 10, "nameDest": "C1"} for i in range(THRESHOLD - 1)]
    results = detectVelocityRule(rows, passed_as_of_step=10)

    assert results == []


def test_valid_at_window_boundary():
    rows = [
        {"id": i, "step": 10 - WINDOW_STEPS, "nameDest": "C1"}
        for i in range(THRESHOLD)
    ]
    results = detectVelocityRule(rows, passed_as_of_step=10)

    assert len(results) == 1


def test_invalid_outside_window_boundary():
    rows = [
        {"id": i, "step": 10 - WINDOW_STEPS - 1, "nameDest": "C1"}
        for i in range(THRESHOLD)
    ]
    results = detectVelocityRule(rows, passed_as_of_step=10)

    assert results == []


def test_invalid_nameOrig_side_ignored():
    # C1 sends many transactions but does not receive enough to meet the rule
    rows = [{"id": i, "step": 10, "nameDest": "C2"} for i in range(THRESHOLD - 1)]
    results = detectVelocityRule(rows, passed_as_of_step=10)

    assert results == []