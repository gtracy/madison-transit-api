import sys
import os

import webapp2
import webtest
import unittest
from google.appengine.ext import testbed
sys.path.append(os.path.realpath('../../v2/parking'))

from api.v2.parking.parking import ParkingHandler


class AppTest(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        # declare the service stubs
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()

        app = webapp2.WSGIApplication([('/parking/v2/lots', ParkingHandler)])
        self.testapp = webtest.TestApp(app)

    # Test the handler.
    def testParkingHandler(self):
        response = self.testapp.get('/parking/v2/lots')
        self.assertEqual(response.status_int, 200)
        #self.assertEqual(response.normal_body, 'Hello World!')
        self.assertEqual(response.content_type, 'application/json')


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