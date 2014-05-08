import logging
import datetime
import json
import re

from google.appengine.api import urlfetch

from api.v2.parking.parkingdata import ParkingData
from api.BeautifulSoup import BeautifulSoup


# Handles fetch, parse and combine of cityparking data
class CityParkingService():
    def __init__(self, cityparking=None):  # allow injection of parking data
        if cityparking:
            self.lots = cityparking.city_lots
        else:
            self.lots = ParkingData().city_lots

    #  orchestrate the heavy lifting
    def get_data(self):
        parking_availability_html = self.fetch_availability_html()
        parking_availabilities = self.parse_availability_html(parking_availability_html)

        # a little logic to deal if spec event call failed. we can still return availability
        special_events_html = self.fetch_special_events_html()
        special_events = None
        if special_events_html:
            special_events = self.parse_special_events_html(special_events_html)

        self.fill_cityparking_data_obj(parking_availabilities, special_events)

        return self.lots

    ## end get_data

    def fetch_availability_html(self):
        url = 'http://www.cityofmadison.com/parkingUtility/garagesLots/availability/'
        try:
            result = urlfetch.fetch(url)
        except urlfetch.DownloadError:
            logging.error('Error fetching %s' % url)
            raise urlfetch.DownloadError  # die hard

        return result.content

    def parse_availability_html(self, cityparking_avail_html):
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

    def fetch_special_events_html(self):
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

    def parse_special_event_datetimes(self, table_cells):
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

        return event_time, parking_end_time, parking_start_time

    ## end parse_special_event_datetimes

    def parse_special_events_html(self, special_events_html, is_test=None):
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

                event_time, parking_end_time, parking_start_time = self.parse_special_event_datetimes(table_cells)

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

    def fill_cityparking_data_obj(self, parking_availabilities, special_events):
        for lot in self.lots:
            for availability in parking_availabilities:
                if availability['name'].lower().find(lot['shortName']) >= 0:
                    lot['openSpots'] = availability['openSpots']

            if special_events and (special_events['specialEvents']) > 0:
                for special_event in special_events['specialEvents']:
                    if special_event['parkingLocation'].lower().find(lot['shortName']) >= 0:
                        lot['specialEvents'].append(special_event)

    ## end merge_availability_with_special_events