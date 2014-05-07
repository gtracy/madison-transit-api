import logging
import time
import datetime
import json
import re

from google.appengine.api import urlfetch
from pytz.gae import pytz

from api.BeautifulSoup import BeautifulSoup
from api.v2 import api_utils


# Handles fetch, parse and combine of cityparking data
class CampusParkingService():
    def __init__(self, campusparking=None):  # allow injection of parking data
        if campusparking:
            self.lots = campusparking
        else:
            self.lots = CampusParkingData()

    def get_campusparking_data(self):
        parking_availability_html = self.fetch_campusparking_availability_html()
        parking_availabilities = self.parse_campusparking_availability_html(parking_availability_html)

        special_events_html = self.fetch_campusparking_special_events_html()
        special_events = self.parse_campusparking_special_events_html(special_events_html)

        self.fill_cityparking_data(parking_availabilities, special_events)
        return None

    def fetch_campusparking_availability_html(self):
        availability_url = 'http://transportation.wisc.edu/parking/lotinfo_occupancy.aspx'

        return None

    def parse_campusparking_availability_html(self, cityparking_avail_html):
        return None

    def fetch_campusparking_special_events_html(self):
        return None

    def parse_campusparking_special_events_html(self, special_events_html):
        return None

    def fill_cityparking_data(self, parking_availabilities, special_events):
        return None



# CityParkingData.lots pre-populates static props and later fills dynamic props
class CampusParkingData:
    def __init__(self):

        # define lots with mostly initial data to minimize potential for breakage.
        self.lots = [
            {
                'id':'1',
                'shortName': '020',
                'name': 'State Street Campus Garage',
                'address': {
                    'street': '1390 University Avenue',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    {'street': None}
                ],
                'totalSpots': 220,
                'openSpots': None,
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': [
                    {
                        'eventVenue':'',
                        'eventTime': '',
                        'eventName': '',
                        'parkingStartTime': '',
                        'parkingEndTime': '',
                        'webUrl': None,
                    }
                ]
            }
        ]