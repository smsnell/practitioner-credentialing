import unittest

from credentialing.dates import (
    UnsupportedBoundary,
    appointment_cycle_end,
    first_received_window,
    inclusive_days,
    overlaps_window,
    peer_current,
    peer_followups,
    request_deadline,
    uncovered_intervals,
    worked_recently,
)


class DateRulesTests(unittest.TestCase):
    def test_inclusive_days_and_invalid_intervals(self):
        self.assertEqual(inclusive_days("2026-01-01", "2026-01-01"), 1)
        self.assertEqual(inclusive_days("2024-02-28", "2024-03-01"), 3)
        with self.assertRaises(ValueError):
            inclusive_days("2026-01-02", "2026-01-01")
        with self.assertRaises(ValueError):
            inclusive_days("20260101", "2026-01-01")

    def test_gap_29_30_and_179_180_boundaries(self):
        for end, days in (("2026-01-30", 29), ("2026-01-31", 30),
                          ("2026-06-29", 179), ("2026-06-30", 180)):
            with self.subTest(days=days):
                gaps = uncovered_intervals("2026-01-01", [], end)
                self.assertEqual(gaps, [] if days < 30 else [
                    {"start": "2026-01-02", "end": end, "days": days}
                ])

    def test_overlap_adjacent_open_and_unsorted_entries(self):
        self.assertEqual(uncovered_intervals("2025-12-31", [
            ("2026-02-01", None), ("2026-01-16", "2026-01-31"),
            ("2025-12-01", "2026-01-20"),
        ], "2026-04-01"), [])

    def test_internal_and_final_gaps_preserve_actual_boundaries(self):
        self.assertEqual(uncovered_intervals("2025-12-31", [
            ("2026-02-01", "2026-02-28"),
            ("2026-06-01", None),
        ], "2026-03-31"), [
            {"start": "2026-01-01", "end": "2026-01-31", "days": 31},
            {"start": "2026-03-01", "end": "2026-03-31", "days": 31},
        ])
        self.assertEqual(uncovered_intervals("2026-06-01", [], "2026-03-31"), [])
        self.assertEqual(uncovered_intervals("2025-12-31", [
            ("2025-12-01", "2027-01-01"),
        ], "2026-03-31"), [])
        with self.assertRaises(ValueError):
            uncovered_intervals("2025-12-31", [("2026-03-01", "2026-02-01")], "2026-03-31")

    def test_five_year_anchor_and_any_overlap(self):
        self.assertEqual(first_received_window("2026-03-16"), "2021-03-16")
        self.assertTrue(overlaps_window("2020-01-01", "2021-03-16", "2021-03-16", "2026-03-16"))
        self.assertFalse(overlaps_window("2020-01-01", "2021-03-15", "2021-03-16", "2026-03-16"))
        self.assertTrue(overlaps_window("2026-03-16", None, "2021-03-16", "2026-03-16"))
        self.assertFalse(overlaps_window("2026-03-17", None, "2021-03-16", "2026-03-16"))

    def test_recorded_deadline_and_peer_day_64(self):
        self.assertEqual(request_deadline("2026-02-18"), "2026-03-20")
        self.assertEqual(request_deadline("2026-03-06"), "2026-04-05")
        self.assertEqual(peer_followups("2026-01-01"), ["2026-01-22", "2026-02-12", "2026-03-06"])

    def test_peer_currency_through_second_anniversary(self):
        self.assertTrue(peer_current("2024-03-16", "2026-03-16"))
        self.assertFalse(peer_current("2024-03-16", "2026-03-17"))
        self.assertFalse(peer_current("2026-03-17", "2026-03-16"))

    def test_worked_together_at_signature(self):
        self.assertTrue(worked_recently(None, "2026-03-16"))
        self.assertTrue(worked_recently("", "2026-03-16"))
        self.assertTrue(worked_recently("2024-03-16", "2026-03-16"))
        self.assertFalse(worked_recently("2024-03-15", "2026-03-16"))
        self.assertFalse(worked_recently("2026-03-17", "2026-03-16"))

    def test_appointment_year_minus_one_day(self):
        self.assertEqual(appointment_cycle_end("2026-05-01"), "2027-04-30")
        self.assertEqual(appointment_cycle_end("2023-03-01"), "2024-02-29")

    def test_no_invented_leap_anniversary_policy(self):
        calls = (
            lambda: first_received_window("2024-02-29"),
            lambda: peer_current("2024-02-29", "2026-02-28"),
            lambda: worked_recently("2024-02-29", "2026-02-28"),
            lambda: appointment_cycle_end("2024-02-29"),
        )
        for call in calls:
            with self.subTest(call=call), self.assertRaisesRegex(UnsupportedBoundary, "Q10"):
                call()


if __name__ == "__main__":
    unittest.main()
