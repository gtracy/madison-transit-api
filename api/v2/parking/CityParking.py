import logging
import datetime
import json
import re

from google.appengine.api import urlfetch
from pytz.gae import pytz

from api.BeautifulSoup import BeautifulSoup
from api.v2 import api_utils


# Handles fetch, parse and combine of cityparking data
class CityParkingService():
    def __init__(self, cityparking=None):  # allow injection of parking data
        if cityparking:
            self.lots = cityparking.lots
        else:
            self.lots = CityParkingData().lots

    #  orchestrate the heavy lifting
    def get_cityparking_data(self):
        parking_availability_html = self.fetch_cityparking_availability_html()
        parking_availabilities = self.parse_cityparking_availability_html(parking_availability_html)

        # a little logic to deal if spec event call failed. we can still return availability
        special_events_html = self.fetch_cityparking_special_events_html()
        special_events = None
        if special_events_html:
            special_events = self.parse_cityparking_special_events_html(special_events_html)

        self.fill_cityparking_data(parking_availabilities, special_events)

        return self.lots

    ## end get_cityparking_data

    def fetch_cityparking_availability_html(self):
        url = 'http://www.cityofmadison.com/parkingUtility/garagesLots/availability/'
        try:
            result = urlfetch.fetch(url)
        except urlfetch.DownloadError:
            logging.error('Error fetching %s' % url)
            raise urlfetch.DownloadError  # die hard

        return result.content

    def parse_cityparking_availability_html(self, cityparking_avail_html):
        results = []
        lot_spots = -1

        try:
            city_lot_soup = BeautifulSoup(cityparking_avail_html)
            # get all children of the availability div whose class name starts with dataRow
            lot_rows = city_lot_soup.find('div', {'id': 'availability'})\
                .findAll('div', {'class': re.compile('^dataRow')})

            for row in lot_rows:
                for detail in row:
                    if detail.string is not None and detail.string.isdigit():
                        lot_spots = detail.string

                lot_details = {
                    'name': row.div.a.string,
                    'openSpots': lot_spots
                }
                results.append(lot_details)

            logging.debug(json.dumps(results))

        except ValueError:
            # bad error. cannot parse html perhaps due to html change.
            logging.error('Error parsing scraped content from city special events page.')
            raise ValueError

        return results

    ## end parse_cityparking_availability_html

    def fetch_cityparking_special_events_html(self):
        special_events_url = 'http://www.cityofmadison.com/parkingUtility/calendar/index.cfm'

        try:
            #grab the city parking html page - what an awesome API!!! :(
            result = urlfetch.fetch(special_events_url).content

        except urlfetch.DownloadError:
            # problem fetching url
            logging.error('Error loading page (%s).' % special_events_url)
            result = None

        return result

    ## end fetch_parking_special_events_html

    def parse_cityparking_special_events_html(self, special_events_html, is_test=None):
        if not special_events_html:
            return

        special_events = dict()
        special_events['specialEvents'] = []

        try:
            soup = BeautifulSoup(special_events_html)

            # special_event_rows is array of <tr>'s.
            special_event_rows = soup.find('table', {'id': 'calendar'}).findAll('tr')
            # loop table rows, starting with 3rd row (excludes 2 header rows)
            for row_index in range(2, len(special_event_rows)):
                # table_cells is array in the current row
                table_cells = special_event_rows[row_index].findAll('td')

                parking_location = table_cells[1].string
                event_venue = table_cells[4].string
                event = table_cells[3].string

                # transform provided event_time (Central Time)
                event_time = datetime.datetime.strptime(
                    table_cells[0].string + table_cells[5].string.replace(' ', ''),
                    '%m/%d/%Y%I:%M%p'
                ).strftime('%Y-%m-%dT%H:%M:%S')

                # split '00:00 pm - 00:00 pm' into start and end strings
                time_parts = table_cells[2].string.split(' - ')

                # clean up whitespace to avoid errors due to inconsistent format
                time_parts[0] = time_parts[0].replace(' ', '')
                time_parts[1] = time_parts[1].replace(' ', '')

                # transform provided parking_start_time (Central Time)
                parking_start_time = datetime.datetime.strptime(
                    table_cells[0].string + time_parts[0],
                    '%m/%d/%Y%I:%M%p'
                ).strftime('%Y-%m-%dT%H:%M:%S')

                # transform provided parking_end_time (Central Time)
                parking_end_time = datetime.datetime.strptime(
                    table_cells[0].string + time_parts[1],
                    '%m/%d/%Y%I:%M%p'
                ).strftime('%Y-%m-%dT%H:%M:%S')

                central_tz = pytz.timezone('US/Central')

                # hack for testing - sets timestamp of events start:now-1min, end:now+60days
                #if is_test:
                #    parking_start_time = (datetime.datetime.now(central_tz) -
                #                          datetime.timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%S')
                #    parking_end_time = (datetime.datetime.now(central_tz) +
                #                        datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%S')

                # we only care about special_events that are happening now
                #if api_utils.datetimeNowIsInRange(
                #        datetime.datetime.strptime(parking_start_time, '%Y-%m-%dT%H:%M:%S'),
                #        datetime.datetime.strptime(parking_end_time, '%Y-%m-%dT%H:%M:%S'),
                #        datetime.datetime.now(central_tz).replace(tzinfo=None)
                #):
                    # add this special event info to the specialEvents collection
                special_events['specialEvents'].append(
                    {
                        'parkingLocation': parking_location,
                        'eventVenue': event_venue,
                        'eventTime': event_time,
                        'eventName': event,
                        'parkingStartTime': parking_start_time,
                        'parkingEndTime': parking_end_time
                    }
                )

        except ValueError:
            # bad error. cannot parse html perhaps due to html change.
            logging.error('Error parsing scraped content from city special events page.')
            special_events['specialEvents'] = []
            raise ValueError

        return special_events

    ## end parse_cityparking_special_events_html

    def fill_cityparking_data(self, parking_availabilities, special_events):
        for lot in self.lots:
            for availability in parking_availabilities:
                if availability['name'].lower().find(lot['shortName']) >= 0:
                    lot['openSpots'] = availability['openSpots']

            if special_events and (special_events['specialEvents']) > 0:
                for special_event in special_events['specialEvents']:
                    if special_event['parkingLocation'].lower().find(lot['shortName']) >= 0:
                        lot['specialEvents'].append(special_event)

    ## end merge_availability_with_special_events


# CityParkingData.lots pre-populates static props and later fills dynamic props
class CityParkingData:
    def __init__(self):

        # to be added to payload of each special event to allow
        # consumers to link to page for
        self.event_url = 'http://www.cityofmadison.com/parkingUtility/calendar/'

        # define lots with mostly initial data to minimize potential for breakage.
        self.lots = [
            {
                'name': 'State Street Campus Garage',
                'shortName': 'campus',  # minimum reliable unique string
                'address': {
                    'street': '430 N. Frances St.',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '400 N. Frances St.',
                    '400 N. Lake St.'
                ],
                'totalSpots': 243,
                'openSpots': None,
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            },
            {
                'name': 'Brayton Lot',
                'shortName': 'brayton',  # minimum reliable unique string
                'address': {
                    'street': '1 South Butler St.',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    {'street': '10 S. Butler St.'}
                ],
                'totalSpots': 247,
                'openSpots': None,
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            },
            {
                'name': 'Capitol Square North Garage',
                'shortName': 'north',  # minimum reliable unique string
                'address': {
                    'street': '218 East Mifflin St.',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '100 N. Butler St.', '200 E. Mifflin St.', '100 N. Webster St.'
                ],
                'totalSpots': 613,
                'openSpots': None,
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            },
            {
                'name': 'Government East Garage',
                'shortName': 'east',  # minimum reliable unique string
                'address': {
                    'street': '215 S. Pinckney St.',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '200 S. Pinckney St.', '100 E. Wilson St.'
                ],
                'totalSpots': 516,
                'openSpots': None,
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            },
            {
                'name': 'Overture Center Garage',
                'shortName': 'overture',  # minimum reliable unique string
                'address': {
                    'street': '318 W. Mifflin St.',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '300 W. Dayton St.', '300 W. Mifflin St.'
                ],
                'totalSpots': 620,
                'openSpots': None,
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            },
            {
                'name': 'State Street Capitol Garage',
                'shortName': 'state street capitol',  # minimum reliable unique string
                'address': {
                    'street': '214 N. Carroll St.',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '200 N. Carroll St.', '100 W. Dayton St.', '100 W. Johnson St. '
                ],
                'totalSpots': 850,
                'openSpots': None,
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            }
        ]