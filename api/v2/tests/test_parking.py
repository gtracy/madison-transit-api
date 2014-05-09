import os
import sys

# there has to be a better way to do this.
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/'))
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/api/'))
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/api/v2'))
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/api/v2/parking'))


import unittest

from api.v2.parking.cityparking import CityParkingService
from api.v2.parking.campusparking import CampusParkingService


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
        parking_results = CityParkingService().get_data()
        self.assertIsNotNone(parking_results)

    def test_cityparking_result_len(self):
        parking_results = CityParkingService().get_data()
        self.assertEquals(len(parking_results), 6)

    def test_cityparking_spot_availability_val(self):
        parking_results = CityParkingService().get_data()
        failure = False
        for result in parking_results:
            result_num = int(result['openSpots'])
            if result_num < 0:
                failure = True

        self.assertEqual(failure, False)

    # this one could fail without a software bug if there
    # are no events
    def test_cityparking_special_event_exists(self):
        spec_events_html = CityParkingService().fetch_special_events_html()
        special_events = CityParkingService().parse_special_events_html(
            spec_events_html)

        self.assertGreater(len(special_events), 0)

    def test_campusparking_html_not_none(self):
        parking_html = CampusParkingService().fetch_availability_html()
        self.assertIsNotNone(parking_html)

    def test_campusparking_not_none(self):
        parking_results = CampusParkingService().get_data()
        self.assertIsNotNone(parking_results)

    def test_campusparking_spot_availability_val(self):
        parking_html = CampusParkingService().fetch_availability_html()
        parking_results = CampusParkingService().parse_availability_html(parking_html)
        failure = False
        for result in parking_results:
            result_num = int(result['openSpots'])
            if result_num < 0:
                failure = True

        self.assertEqual(failure, False)

    def test_campusparking_special_events_html_not_none(self):
        parking_html = CampusParkingService().fetch_special_events_html()
        self.assertIsNotNone(parking_html)

    def test_campusparking_special_event_has_parkinglocation(self):
        spec_events_html = CampusParkingService().fetch_special_events_html()
        special_events = CampusParkingService().parse_special_events_html(
            spec_events_html)

        self.assertNotEqual(special_events['specialEvents'][0]['parkingLocations'], '')

    def test_campusparking_special_events_complete_data(self):
        data = CampusParkingService().get_data()
        self.assertIsNotNone(data)
        self.assertGreater(len(data), 0)
        self.assertIsNotNone(data[0]['openSpots'])

    def tearDown(self):
        self.testbed.deactivate()

if __name__ == '__main__':
    unittest.main()