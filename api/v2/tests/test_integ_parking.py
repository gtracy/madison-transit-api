import sys
import os

import webapp2
import webtest
import unittest
import datetime
from google.appengine.ext import testbed

# set up relative paths to app dependencies
sys.path.append(os.path.realpath('../../../'))
sys.path.append(os.path.realpath('../../'))
sys.path.append(os.path.realpath('../../v2'))
sys.path.append(os.path.realpath('../../v2/parking'))


from api.v2.parking.parking import ParkingHandler


class ParkingIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        # declare the service stubs
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()

        app = webapp2.WSGIApplication([('/parking/v2/lots', ParkingHandler)])
        self.testapp = webtest.TestApp(app)

    def test_parking_lots_len(self):
        response = self.testapp.get('/parking/v2/lots')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = response.json['lots']
        self.assertEquals(len(data), 18)

    def test_parking_lots_avail_set(self):
        response = self.testapp.get('/parking/v2/lots')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = response.json['lots']
        # test all openSpots got set
        for lot in data:
            self.assertIsNotNone(lot['openSpots'])

    def test_parking_include_special_events(self):
        response = self.testapp.get('/parking/v2/lots?expand=specialevents')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = response.json['lots']
        hit = False
        for lot in data:
            if len(lot['specialEvents']) > 0:
                hit = True
        self.assertTrue(hit)

    def test_parking_valid_uw_special_event(self):
        response = self.testapp.get('/parking/v2/lots?expand=specialevents')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = response.json['lots']
        hitRecord = False
        for lot in data:
            if len(lot['specialEvents']) > 0 and lot['operatedBy'] == 'uw':
                hitRecord = lot
                break

        thedatetime = datetime.datetime.strptime(hitRecord['specialEvents'][0]['eventDatetime'],'%Y-%m-%dT%H:%M:%S')
        self.assertIsInstance(thedatetime,datetime.datetime)

    def test_parking_valid_city_special_event(self):
        response = self.testapp.get('/parking/v2/lots?expand=specialevents')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = response.json['lots']
        hitRecord = False
        for lot in data:
            if len(lot['specialEvents']) > 0 and lot['operatedBy'] == 'city':
                hitRecord = lot
                break

        thedatetime = datetime.datetime.strptime(hitRecord['specialEvents'][0]['eventDatetime'],'%Y-%m-%dT%H:%M:%S')
        self.assertIsInstance(thedatetime,datetime.datetime)