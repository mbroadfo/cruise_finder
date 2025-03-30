import unittest
from src.trip_parser import TripParser

class TestTripParser(unittest.TestCase):

    def setUp(self):
        """Set up sample JSON response before each test."""
        self.sample_json = {
            "trip_name": "The Panama Canal, Pearl Islands and Darién Jungle",
            "destination": "Central America > South America > New and Noteworthy",
            "duration": "8 days"
        }

    def test_parse_trip_attributes(self):
        """Test that the parser correctly extracts basic trip details."""
        parser = TripParser()
        result = parser.parse_trip_list(self.sample_json)  # This method will process the JSON
        expected = self.sample_json  # Expected result should match the sample JSON
        self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()
