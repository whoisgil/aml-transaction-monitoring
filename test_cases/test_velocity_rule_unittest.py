import unittest

from functions.detection_functions import detectVelocityRule, THRESHOLD, WINDOW_STEPS


class TestDetectVelocityRule(unittest.TestCase):

    def test_valid_threshold_met(self):
        rows = [{"id": i, "step": 10, "nameDest": "C1"} for i in range(THRESHOLD)]

        results = detectVelocityRule(rows, passed_as_of_step=10)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["matched_account"], "C1")
        self.assertEqual(results[0]["observed_value"], THRESHOLD)

    def test_invalid_below_threshold(self):
        rows = [{"id": i, "step": 10, "nameDest": "C1"} for i in range(THRESHOLD - 1)]

        results = detectVelocityRule(rows, passed_as_of_step=10)

        self.assertEqual(results, [])

    def test_valid_at_window_boundary(self):
        boundary_step = 10 - WINDOW_STEPS
        rows = [{"id": i, "step": boundary_step, "nameDest": "C1"} for i in range(THRESHOLD)]

        results = detectVelocityRule(rows, passed_as_of_step=10)

        self.assertEqual(len(results), 1)

    def test_invalid_outside_window_boundary(self):
        outside_step = 10 - WINDOW_STEPS - 1
        rows = [{"id": i, "step": outside_step, "nameDest": "C1"} for i in range(THRESHOLD)]

        results = detectVelocityRule(rows, passed_as_of_step=10)

        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()