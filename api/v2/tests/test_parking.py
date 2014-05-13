import os
import sys

from google.appengine.api import urlfetch

# set up relative paths to system-under-test dependencies.
# tested only on Mac OS X
sys.path.append(os.path.realpath('../../../'))
sys.path.append(os.path.realpath('../../'))
sys.path.append(os.path.realpath('../../v2'))
sys.path.append(os.path.realpath('../../v2/parking'))

import unittest

from api.v2.parking.parkingdata import ParkingData
from api.v2.parking.cityparking import CityParkingService
from api.v2.parking.campusparking import CampusParkingService

from google.appengine.ext import testbed


if __name__ == '__main__':
    unittest.main()


class TestCityParking(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        # declare the service stubs
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()

    def test_cityparking_bad_city_avail_url(self):
        parking_data = ParkingData().city_data
        parking_data['availability_url'] = \
            'http://www.cityofmadisonbaddomain.com'
        with self.assertRaises(urlfetch.DownloadError):
            CityParkingService(parking_data).get_data()

    def test_cityparking_bad_html_none(self):
        with self.assertRaises(TypeError):
            CityParkingService().parse_availability_html(None)

    def test_cityparking_bad_html_empty_html(self):
        with self.assertRaises(AttributeError):
            CityParkingService().parse_availability_html('')

    def test_cityparking_bad_html_bad_parse_html(self):
        bad_html = '<html><body><div id="availability"><div class="datadRow"></div></div></body></html>'
        with self.assertRaises(ValueError):
            CityParkingService().parse_availability_html(bad_html)

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

    def test_cityparking_bad_city_special_events_url(self):
        parking_data = ParkingData().city_data
        parking_data['availability_url'] = \
            'http://www.cityofmadisonbaddomain.com'
        with self.assertRaises(urlfetch.DownloadError):
            CityParkingService(parking_data).get_data()

    def test_cityparking_bad_special_events_html_none(self):
        se_data = CityParkingService().parse_special_events_html(None)
        self.assertEquals(se_data['specialEvents'], [])

    def test_cityparking_bad_special_events_html_empty_html(self):
        se_data = CityParkingService().parse_special_events_html('')
        self.assertEquals(se_data['specialEvents'], [])

    def test_cityparking_bad_special_events_bad_parse_html(self):
        bad_html = '<html><body><div id="availability"><div class="garbage"></div></div></body></html>'
        se_data = CityParkingService().parse_special_events_html(bad_html)
        self.assertEquals(se_data['specialEvents'], [])

    # this one could fail without a software bug if there
    # are no events
    def test_cityparking_special_event_exists(self):
        parking_data = ParkingData().city_data
        url = parking_data['special_events_url']
        spec_events_html = CityParkingService().fetch_special_events_html(url)
        special_events = CityParkingService().parse_special_events_html(
            spec_events_html)

        self.assertGreater(len(special_events), 0)

    def tearDown(self):
        self.testbed.deactivate()


class TestCampusParking(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        # declare the service stubs
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()



    def test_campusparking_bad_campus_avail_url(self):
        parking_data = ParkingData().campus_data
        parking_data['availability_url'] = \
            'http://www.campusbaddomainsdfsd.com'
        with self.assertRaises(urlfetch.DownloadError):
            CampusParkingService(parking_data).get_data()


    def test_campusparking_html_not_none(self):
        avail_url = ParkingData().campus_data['availability_url']
        parking_html = CampusParkingService().fetch_availability_html(avail_url)
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

    def test_campusparking_bad_special_events_url(self):
        campus_special_events_url = 'http://www.campusmadisonbaddomain.com'
        result = CampusParkingService().fetch_special_events_html(campus_special_events_url)
        self.assertEquals(result, None)

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