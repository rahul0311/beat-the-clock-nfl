"""Checks for errors that would change the football interpretation."""
import unittest
import numpy as np
from analyze import alias, identify_target, pass_depth, separation_windows


class MeasurementTests(unittest.TestCase):
    def test_named_target_matches_full_roster_name(self):
        roster = {46206: {'displayName': 'Dalton Schultz'}}
        description = 'D.Prescott pass short middle to D.Schultz to DAL 39 for 5 yards.'
        self.assertEqual(identify_target(description, [46206], roster), 46206)
        self.assertEqual(alias('Odell Beckham Jr.'), 'obeckham')

    def test_ambiguous_names_do_not_assign_a_target(self):
        roster = {1: {'displayName': 'Dalton Schultz'}, 2: {'displayName': 'David Schultz'}}
        self.assertIsNone(identify_target('pass short middle to D.Schultz.', [1, 2], roster))

    def test_pass_label_does_not_use_yards_gained(self):
        self.assertEqual(pass_depth('pass short left to C.Lamb for 22 yards, TOUCHDOWN.'), 'short')
        self.assertEqual(pass_depth('pass incomplete deep right to M.Evans.'), 'deep')
        self.assertEqual(pass_depth('pass incomplete right.'), 'unclassified')

    def test_window_stops_at_last_observation(self):
        times = np.array([0., .1, .2, .3])
        self.assertEqual(separation_windows(times, np.ones(4, dtype=bool)), [[0., .3]])
        self.assertEqual(separation_windows(times[:3], np.ones(3, dtype=bool)), [])

    def test_missing_frames_do_not_create_a_sustained_window(self):
        times = np.array([0., .1, .3, .4])
        self.assertEqual(separation_windows(times, np.ones(4, dtype=bool)), [])


if __name__ == '__main__':
    unittest.main()
