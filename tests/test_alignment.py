import unittest
import pandas as pd
from alignment import classify_window, add_alignment


class AlignmentTests(unittest.TestCase):
    def test_early_throw_without_window_is_unknown(self):
        self.assertEqual(classify_window([], clock=2.6, release=1.7), 'unresolved')

    def test_observed_window_counts_even_if_throw_ends_early(self):
        self.assertEqual(classify_window([[.9, 1.5]], clock=2.6, release=2.2), 'window_observed')

    def test_only_window_before_cutoff_counts(self):
        self.assertEqual(classify_window([[2.5, 3.1]], clock=2.6, release=3.2), 'no_window_observed')

    def test_full_observation_without_window_is_explicit(self):
        self.assertEqual(classify_window([], clock=2.6, release=3.2), 'no_window_observed')
        self.assertEqual(classify_window([], clock=2.6, release=3.2, complete_tracking=False), 'unresolved')

    def test_no_reference_is_not_a_receiver_failure(self):
        self.assertEqual(classify_window([], clock=None, release=3.2), 'no_reference')

    def test_reference_excludes_the_entire_current_game(self):
        plays = pd.DataFrame([dict(gameId=game, playId=i, qbId=1, playAction=False,
                                   coverageType='Zone', depth='short', ttt=duration)
                              for game, duration in [(1, 2.), (2, 4.)] for i in range(3)])
        routes = pd.DataFrame([dict(gameId=1, playId=0, nflId=10, passDepth='short',
                                    ttt=2., windowsJson='[]', validFrameShare=1., continuousTracking=True)])
        sample, _ = add_alignment(plays, routes, min_reference=3)
        self.assertEqual(sample.iloc[0].clock, 4.)
        self.assertEqual(sample.iloc[0].referenceCount, 3)
        self.assertEqual(sample.iloc[0].alignmentStatus, 'unresolved')


if __name__ == '__main__':
    unittest.main()
