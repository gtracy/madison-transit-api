import os, sys

# there has to be a better way to do this.
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/api/'))
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/api/v1/'))
sys.path.append(os.path.dirname('/Users/chriss/code/me/madison-transit-api/'))

import unittest
import getparking

#from google.appengine.api import memcache
from google.appengine.ext import testbed


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        # declare the service stubs
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub()

    def test_special_event_not_none(self):
        specEvents = getparking.getParkingSpecialEvents()
        self.assertIsNotNone(specEvents)

    def test_get(self):
        specEvents = getparking.getParkingSpecialEvents()
        self.assertIsNotNone(specEvents)

    def tearDown(self):
        self.testbed.deactivate()

if __name__ == '__main__':
    unittest.main()