import logging
import json
import datetime

from google.appengine.api import urlfetch
from google.appengine.api import memcache

from api.BeautifulSoup import BeautifulSoup
from api.v2.parking.parkingdata import ParkingData


# Handles fetch, parse and combine of cityparking data
class CampusParkingService():
    def __init__(self):
        self.parking_data = ParkingData().campus_data

    def get_data(self, include_special_events):
        parking_availability_html = self.fetch_availability_html()
        parking_availabilities = self.parse_availability_html(parking_availability_html)

        if include_special_events:
            special_events = memcache.get('campus_special_events')
            if special_events is None:
                special_events_url = self.parking_data['special_events_url']
                special_events_html = self.fetch_special_events_html(special_events_url)
                special_events = None
                if special_events_html:
                    special_events = self.parse_special_events_html(special_events_html)
                    memcache.set('campus_special_events', special_events, 86400)  # cache for a day

            self.fill_campusparking_data_obj(parking_availabilities, special_events)

            # lot #'s needed for prior "fill" method but don't make sense in payload
            self.remove_locations_from_special_events()
        else:
            self.fill_campusparking_data_obj(parking_availabilities)

        return self.parking_data['lots']

    def fetch_availability_html(self, url=None):
        if not url:
            url = self.parking_data['availability_url']
        try:
            result = urlfetch.fetch(url)
        except urlfetch.DownloadError:
            logging.error('Error fetching %s' % url)
            raise urlfetch.DownloadError  # die hard

        return result.content

    def parse_availability_html(self, campusparking_avail_html):
        results = []
        lot_spots = None

        try:
            campus_lot_soup = BeautifulSoup(campusparking_avail_html)
            # get all children of the availability div whose class name starts with dataRow
            lot_rows = campus_lot_soup.find(
                'table', {'id': 'ctl00_ctl00_central_block_right_navi_cnt_gvName'}
            ).findAll('tr')

            # loop table rows, starting with 2bd row (excludes header row)
            for row_index in range(1, len(lot_rows)):

                # grab the array of cells in the current row
                table_cells = lot_rows[row_index].findAll('td')

                short_name = table_cells[1].string.split(' ')[0].strip()

                spots_cell = table_cells[2].string.strip()
                if spots_cell is not None and spots_cell.isdigit():
                    lot_spots = spots_cell

                lot_details = {
                    'shortName': short_name,
                    'openSpots': int(lot_spots)
                }
                results.append(lot_details)

            logging.debug(json.dumps(results))

        except ValueError:
            # Cannot parse html perhaps due to html change.
            logging.error('ValueError parsing scraped content from campus parking page.')
            logging.info(short_name)
            raise ValueError

        except AttributeError:
            # HTML doesn't include expected elements
            logging.error('AttributeError parsing scraped content from campus parking page.')
            logging.info(AttributeError)
            raise AttributeError

        except TypeError:
            # Html is probably None
            logging.error('TypeError parsing scraped content from campus parking page.')
            raise TypeError

        except IndexError:
            # Html is probably None
            logging.error('IndexError parsing scraped content from campus parking page.')
            raise IndexError

        return results

    def fetch_special_events_html(self, special_events_url=None):
        if not special_events_url:
            special_events_url = self.parking_data['special_events_url']
        try:
            #grab the city parking html page
            result = urlfetch.fetch(special_events_url).content

        except urlfetch.DownloadError as e:
            # problem fetching url. Do log and move on as parking availability still valuable
            logging.error('Error loading page (%s).' % special_events_url + str(e))
            result = None

        return result

    def parse_special_events_html(self, special_events_html):
        special_events = dict()
        special_events['specialEvents'] = []

        if not special_events_html:
            return special_events

        try:
            soup = BeautifulSoup(special_events_html)
            event_tables = soup.findAll('table', {'class': 'event-item'})

            for event_table in event_tables:
                rows = event_table.findAll('tr')
                event_time = ''
                event_date = ''
                lot_num_array = []
                event_name = ''
                for row_index in range(0, 3):
                    if row_index == 0:  # we're on the header row
                        header_content = rows[row_index].find('th').string
                        header_array = header_content.split(':')
                        event_date = header_array[0]
                        event_name = header_array[1].replace('&nbsp;', '')
                    elif row_index == 1:  # time row
                        cells = rows[row_index].findAll('td')
                        cell_content = cells[1].string
                        event_time_arr = cell_content.split(' ', 2)
                        event_time = event_time_arr[0] + event_time_arr[1].replace('.', '').upper()
                    elif row_index == 2:  # lots row
                        cells = rows[row_index].findAll('td')
                        cell_content = cells[1].string
                        lot_num_array = cell_content.replace(' ', '').split(',')

                        # strip leading 0's out of lot number array
                        for index, item in enumerate(lot_num_array):
                            lot_num_array[index] = self.strip_leading_zeros_from_short_name(item)

                try:  # the most brittle part of the parse
                    if len(event_time) == 1:
                        event_time = '0' + event_time
                    event_datetime_tmp = event_date + ' ' + event_time
                    event_datetime_str = datetime.datetime.strptime(
                        event_datetime_tmp, '%m/%d/%Y %I:%M%p'
                    ).strftime('%Y-%m-%dT%H:%M:%S')

                except ValueError:
                    logging.error('Error parsing campus special event date')
                    event_datetime_str = None

                # Rather than exclude props not currently available via uw lots, going with "None"
                # This will manifest in the json as "property":null which should be easily detectable via client JS
                special_event = {
                    'eventName': event_name,
                    'parkingLocations': lot_num_array,
                    'eventDatetime': event_datetime_str,
                    'parkingStartDatetime': None,
                    'parkingEndDatetime': None,
                    'eventVenue': None,
                    'webUrl': self.parking_data['special_events_url']
                }
                special_events['specialEvents'].append(special_event)

        except (ValueError, AttributeError, TypeError, IndexError) as e:
            # unlike availability, we eat this error. availability is still useful w/out events
            logging.error('Error parsing scraped content from campus special events page.' + str(e))
            special_events['specialEvents'] = []

        return special_events

    def fill_campusparking_data_obj(self, parking_availabilities, special_events=None):
        for lot in self.parking_data['lots']:
            for park_availability in parking_availabilities:
                if lot['shortName'] == self.strip_leading_zeros_from_short_name(park_availability['shortName']):
                    lot['openSpots'] = park_availability['openSpots']

            if special_events and (special_events['specialEvents']) > 0:
                lot['specialEvents'] = []
                for special_event in special_events['specialEvents']:
                    if lot['shortName'] in special_event['parkingLocations']:
                        lot['specialEvents'].append(special_event)

    def remove_locations_from_special_events(self):
        for lot in self.parking_data['lots']:
            if lot['specialEvents'] and len(lot['specialEvents']) > 0:
                for se in lot['specialEvents']:
                    se.pop('parkingLocations', None)

    def strip_leading_zeros_from_short_name(self, short_name):
        return short_name.lstrip('0')