import os
import sys

# there has to be a better way to do this.
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/api/'))
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/api/v2/'))
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/'))

import unittest
from api.v2.parking import CityParking
from api.v2.parking import CityParkingLotsService

from google.appengine.ext import testbed

# These are integration tests as they include external fetch
class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        #self.city_parking_service = CityParkingLotsService(CityParking)

        # declare the service stubs
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()


    # todo exception tests.

    def test_parking_result_not_none(self):
        parking_results = CityParkingLotsService(CityParking()).get_city_parking_data()
        self.assertIsNotNone(parking_results)

    def test_parking_result_len(self):
        parking_results = CityParkingLotsService(CityParking()).get_city_parking_data()
        self.assertEquals(len(parking_results), 6)

    def test_spot_availability_val(self):
        parking_results = CityParkingLotsService(CityParking()).get_city_parking_data()
        failure = False
        for result in parking_results:
            resultNum = int(result['openSpots'])
            if resultNum < 0:
                failure = True

        self.assertEqual(failure, False)

    # this one could fail without a software bug if there
    # are no events for 60 days
    def test_special_event_exists(self):
        spec_events_html = CityParkingLotsService(CityParking()).fetch_parking_special_events_html()
        special_events = CityParkingLotsService(CityParking()
                                                ).transform_city_parking_special_events_html_to_dict(
                                                    spec_events_html, True)

        self.assertGreater(len(special_events), 0)

    def tearDown(self):
        self.testbed.deactivate()

if __name__ == '__main__':
    unittest.main()