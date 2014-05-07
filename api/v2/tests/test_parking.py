import os
import sys

# there has to be a better way to do this.
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/'))
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/api/'))
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/api/v2'))
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/api/v2/parking'))


import unittest

from api.v2.parking.CityParking import CityParkingService
from api.v2.parking.CampusParking import CampusParkingService


from google.appengine.ext import testbed

# These are integration tests as they include external fetch
class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        # declare the service stubs
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()


    # todo exception tests.

    def test_cityparking_result_not_none(self):
        parking_results = CityParkingService().get_cityparking_data()
        self.assertIsNotNone(parking_results)

    def test_cityparking_result_len(self):
        parking_results = CityParkingService().get_cityparking_data()
        self.assertEquals(len(parking_results), 6)

    def test_cityparking_spot_availability_val(self):
        parking_results = CityParkingService().get_cityparking_data()
        failure = False
        for result in parking_results:
            result_num = int(result['openSpots'])
            if result_num < 0:
                failure = True

        self.assertEqual(failure, False)

    # this one could fail without a software bug if there
    # are no events for 60 days
    def test_cityparking_special_event_exists(self):
        spec_events_html = CityParkingService().fetch_cityparking_special_events_html()
        special_events = CityParkingService().parse_cityparking_special_events_html(
            spec_events_html, True)

        self.assertGreater(len(special_events), 0)

    def test_campusparking_html_not_none(self):
        parking_html = CampusParkingService().fetch_campusparking_availability_html()
        self.assertIsNotNone(parking_html)

    def test_campusparking_not_none(self):
        parking_results = CampusParkingService().get_campusparking_data()
        self.assertIsNotNone(parking_results)



    def tearDown(self):
        self.testbed.deactivate()

if __name__ == '__main__':
    unittest.main()