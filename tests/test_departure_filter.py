import unittest

class TestDepartureFiltering(unittest.TestCase):
    def test_mutating_during_iteration_causes_duplicates(self):
        original = [{'id': 1}, {'id': 2}]
        # Mistakenly append to the list you're iterating
        for item in original:
            if item['id'] == 1:
                original.append({'id': 3})
        ids = [x['id'] for x in original]
        self.assertIn(3, ids)
        self.assertGreaterEqual(ids.count(3), 1)  # It might show up multiple times if you loop further

    def test_safe_departure_filtering(self):
        original = [
            {'id': 1, 'keep': True},
            {'id': 2, 'keep': False},
            {'id': 3, 'keep': True}
        ]
        filtered = [d for d in original if d['keep']]
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]['id'], 1)
        self.assertEqual(filtered[1]['id'], 3)

if __name__ == '__main__':
    unittest.main()
