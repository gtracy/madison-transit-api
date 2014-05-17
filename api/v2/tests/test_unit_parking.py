import os
import sys

from google.appengine.api import urlfetch

# set up relative paths to app dependencies
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


class ParkingUnitTests(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        # declare the service stubs
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()

    def test_cityparking_bad_city_avail_url(self):
        with self.assertRaises(urlfetch.DownloadError):
            CityParkingService().fetch_availability_html('http://www.cityofmadisonbaddomain.com')

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

    def test_cityparking_html_parse_html_spots(self):
        html = '<html><body><div id="availability">' \
               '<div class="dataRow"><div class="carParkName"><a href="../facilities/brayton.cfm">Brayton Lot</a></div><div class="spotsOpen">131</div></div>' \
               '<div class="dataRow rowShade"><div class="carParkName"><a href="../facilities/capSquareNorth.cfm">Capitol Square North Garage</a></div><div class="spotsOpen">345</div></div>' \
               '</div></body></html>'
        lot_details = CityParkingService().parse_availability_html(html)
        self.assertEquals(lot_details[1]['openSpots'], '345')

    def test_cityparking_html_parse_html_lotname(self):
        html = '<html><body><div id="availability">' \
               '<div class="dataRow"><div class="carParkName"><a href="../facilities/brayton.cfm">Brayton Lot</a></div><div class="spotsOpen">131</div></div>' \
               '<div class="dataRow rowShade"><div class="carParkName"><a href="../facilities/capSquareNorth.cfm">Capitol Square North Garage</a></div><div class="spotsOpen">345</div></div>' \
               '</div></body></html>'
        lot_details = CityParkingService().parse_availability_html(html)
        self.assertEquals(lot_details[0]['name'], 'Brayton Lot')

    def test_cityparking_bad_city_special_events_url(self):
        html = CityParkingService().fetch_special_events_html('http://cityofmadison---bad.com')
        self.assertIsNone(html)

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

    def test_cityparking_special_events_parse_html(self):
        html = '<html><body><table id="calendar"><tr></tr><tr></tr><tr class="rowshade"><td>5/16/2014</td><td> Overture Center Garage, State Street Capitol Garage</td><td>6:00 pm - 8:05 pm</td><td>Million Dollar Quartet</td><td>Overture Center - Overture Hall</td><td>8:00 pm</td></tr></table></body></html>'
        se_data = CityParkingService().parse_special_events_html(html)
        self.assertEquals(se_data['specialEvents'][0]['eventDatetime'], '2014-05-16T20:00:00')

    def test_fill_city_parking_no_special_events(self):
        city_parking_service = CityParkingService()
        parking_avails = [{'name': 'State Street Campus Garage', 'openSpots': '5'}]
        city_parking_service.fill_cityparking_data_obj(parking_avails)
        with self.assertRaises(KeyError):
            spec = city_parking_service.parking_data['lots'][0]['specialEvents']
        self.assertEquals(city_parking_service.parking_data['lots'][0]['openSpots'], '5')

    def test_fill_city_parking_with_special_events(self):
        city_parking_service = CityParkingService()
        parking_avails = [{'name': 'State Street Campus Garage', 'openSpots': '5'}]
        spec_events = {'specialEvents': [{'parkingLocation': 'State Street Campus Garage',
                        'eventVenue': 'blah',
                        'eventDatetime': None,
                        'eventName': None,
                        'parkingStartDatetime': None,
                        'parkingEndDatetime': None,
                        'webUrl': 'http://'}]}
        city_parking_service.fill_cityparking_data_obj(parking_avails, spec_events)
        self.assertEquals(city_parking_service.parking_data['lots'][0]['openSpots'], '5')
        self.assertEquals(city_parking_service.parking_data['lots'][0]['specialEvents'][0]['eventVenue'], 'blah')

    def test_remove_locations_from_special_events(self):
        city_parking_service = CityParkingService()

        for lot in city_parking_service.parking_data['lots']:
            lot['specialEvents'] = []
        city_parking_service.parking_data['lots'][0]['specialEvents'].append(
            {
                'parkingLocation': 'State Street Campus Garage',
                'eventVenue': 'blah',
                'eventDatetime': None,
                'eventName': None,
                'parkingStartDatetime': None,
                'parkingEndDatetime': None,
                'webUrl': 'http://',
            }
        )

        city_parking_service.remove_locations_from_special_events()
        self.assertEquals(city_parking_service.parking_data['lots'][0]['specialEvents'][0]['eventVenue'], 'blah')
        with self.assertRaises(KeyError):
            self.assertEquals(city_parking_service.parking_data['lots'][0]['specialEvents'][0]['parkingLocation'], 'State Street Campus Garage')

######## Start Campus Parking Unit Tests #########
    def test_campusparking_bad_campus_avail_url(self):
        with self.assertRaises(urlfetch.DownloadError):
            CampusParkingService().fetch_availability_html('http://www.campusofmadisonbaddomain.com')

    def test_campusparking_bad_avail_html_none(self):
        with self.assertRaises(TypeError):
            CampusParkingService().parse_availability_html(None)

    def test_campusparking_bad_avail_html_empty_html(self):
        with self.assertRaises(AttributeError):
            CampusParkingService().parse_availability_html('')

    def test_campusparking_bad_html_bad_avail_parse_html(self):
        bad_html = '<html><body><table id="ctl00_ctl00_central_block_right_navi_cnt_gvName"><tr></tr><tr><td></td></tr></table></body></html>'
        with self.assertRaises(IndexError):
            CampusParkingService().parse_availability_html(bad_html)

    def test_campusparking_html_parse_html_spots(self):
        html = '<html><body><table id="ctl00_ctl00_central_block_right_navi_cnt_gvName"><tr></tr><tr><td></td><td>020 UNIVERSITY AVE RAMP</td><td>5</td></tr></table></body></html>'
        lot_details = CampusParkingService().parse_availability_html(html)
        self.assertEquals(lot_details[0]['openSpots'], '5')

    def test_campusparking_html_parse_html_lotname(self):
        html = '<html><body><table id="ctl00_ctl00_central_block_right_navi_cnt_gvName"><tr></tr><tr><td></td><td>020 UNIVERSITY AVE RAMP</td><td>5</td></tr></table></body></html>'
        lot_details = CampusParkingService().parse_availability_html(html)
        self.assertEquals(lot_details[0]['shortName'], '020')

    def test_campusparking_bad_city_special_events_url(self):
        html = CampusParkingService().fetch_special_events_html('http://campus---bad.com')
        self.assertIsNone(html)

    def test_campusparking_bad_special_events_html_none(self):
        se_data = CampusParkingService().parse_special_events_html(None)
        self.assertEquals(se_data['specialEvents'], [])

    def test_campusparking_bad_special_events_html_empty_html(self):
        se_data = CampusParkingService().parse_special_events_html('')
        self.assertEquals(se_data['specialEvents'], [])

    def test_campusparking_bad_special_events_bad_parse_html(self):
        bad_html = '<html><body><table class="event-item"></body></html>'
        se_data = CampusParkingService().parse_special_events_html(bad_html)
        self.assertEquals(se_data['specialEvents'], [])

    def test_campusparking_special_events_parse_html(self):
        html = '<table id="event2" class="event-item" border="0" cellspacing="0">' \
               '<tbody><tr><th class="event-head">06/12/2014:&nbsp;&nbsp;WIAA Softball</th></tr>' \
               '<tr><td>Times lots will be impacted:</td><td>7:00 a.m. </td></tr>' \
               '<tr><td>Event Parking Available in Lots:</td><td>60, 76</td></tr>' \
               '</tbody></table>'
        se_data = CampusParkingService().parse_special_events_html(html)
        self.assertEquals(se_data['specialEvents'][0]['eventDatetime'], '2014-06-12T07:00:00')

    def test_fill_campusparking_no_special_events(self):
        campus_parking_service = CampusParkingService()
        parking_avails = [{'name': 'University Avenue Ramp', 'openSpots': '5', 'shortName': '020'}]
        campus_parking_service.fill_campusparking_data_obj(parking_avails)
        with self.assertRaises(KeyError):  # special events should be None
            spec = campus_parking_service.parking_data['lots'][0]['specialEvents']
        self.assertEquals(campus_parking_service.parking_data['lots'][0]['openSpots'], '5')


    def test_fill_campusparking_with_special_events(self):
        campus_parking_service = CampusParkingService()
        parking_avails = [{'name': 'University Avenue Ramp', 'openSpots': '5', 'shortName': '020'}]
        spec_events = {
            'specialEvents': [
                {
                    'parkingLocations': ['20'],
                    'eventVenue': 'blah',
                    'eventDatetime': None,
                    'eventName': None,
                    'parkingStartDatetime': None,
                    'parkingEndDatetime': None,
                    'webUrl': 'http://'
                }
            ]
        }
        campus_parking_service.fill_campusparking_data_obj(parking_avails, spec_events)
        self.assertEquals(campus_parking_service.parking_data['lots'][0]['openSpots'], '5')
        self.assertEquals(campus_parking_service.parking_data['lots'][0]['specialEvents'][0]['eventVenue'], 'blah')

    def test_remove_campus_locations_from_special_events(self):
        campus_parking_service = CampusParkingService()

        for lot in campus_parking_service.parking_data['lots']:
            lot['specialEvents'] = []
        campus_parking_service.parking_data['lots'][0]['specialEvents'].append(
            {
                'parkingLocations': ['20'],
                'eventVenue': 'blah',
                'eventDatetime': None,
                'eventName': None,
                'parkingStartDatetime': None,
                'parkingEndDatetime': None,
                'webUrl': 'http://'
            }
        )

        campus_parking_service.remove_locations_from_special_events()
        self.assertEquals(campus_parking_service.parking_data['lots'][0]['specialEvents'][0]['eventVenue'], 'blah')
        with self.assertRaises(KeyError):
            self.assertEquals(campus_parking_service.parking_data['lots'][0]['specialEvents'][0]['parkingLocations'], ['20'])

    def tearDown(self):
        self.testbed.deactivate()