import logging
import time
import datetime
import webapp2 as webapp
import json
import re

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext.webapp.util import run_wsgi_app
from pytz.gae import pytz

from api.BeautifulSoup import BeautifulSoup

from api.v2 import api_utils
from stats import stathat


class ParkingHandler(webapp.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.headers['Allow'] = 'GET'
        self.response.status = 405  # method not allowed
        self.response.out.write(
            json.dumps(
                api_utils.buildErrorResponse('-1', 'The API does not support POST requests')
            )
        )

    def get(self):
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.headers['Allow'] = 'GET'
        try:
            city_parking = CityParking()
            city_lots = CityParkingLotsService(city_parking).get_city_parking_data()
            logging.debug('API: city_lots json response %s' % city_lots)
        except urlfetch.DownloadError:
            logging.error('Failed to retrieve city data')
            self.response.status = 500  # method not allowed
            self.response.out.write(
                json.dumps(
                    api_utils.buildErrorResponse('-1', 'Failed to retrieve city data')
                )
            )
            return

        uw_lots = {}
        logging.debug('API: uw_lots json response %s' % uw_lots)

        #  encapsulate response in json or jsonp
        callback = self.request.get('callback')
        if callback is not '':
            self.response.headers['Content-Type'] = 'application/javascript'
            self.response.headers['Access-Control-Allow-Origin'] = '*'
            self.response.headers['Access-Control-Allow-Methods'] = 'GET'
            response = callback + '(' + json.dumps(city_lots) + ');'
        else:
            self.response.headers['Content-Type'] = 'application/json'
            response = json.dumps(city_lots)

        #stathat.apiStatCount()
        self.response.out.write(response)


## end MainHandler

# CityParking.lots pre-populates static props and later fills dynamic props
class CityParking:
    def __init__(self):

        # define lots with mostly initial data to minimize potential for breakage.
        self.lots = [
            {
                'name': 'State Street Campus Garage',
                'shortName': 'campus',  # minimum reliable unique string
                'address': ['430 N. Frances St.', '415 N. Lake St.'],
                'totalSpots': 243,
                'openSpots': -1,
                'specialEvent': {}
            },
            {
                'name': 'Brayton Lot',
                'shortName': 'brayton',  # minimum reliable unique string
                'address': ['10 S. Butler St.'],
                'totalSpots': 247,
                'openSpots': -1,
                'specialEvent': {}
            },
            {
                'name': 'Capitol Square North Garage',
                'shortName': 'north',  # minimum reliable unique string
                'address': ['100 N. Butler St.', '200 E. Mifflin St.', '100 N. Webster St.'],
                'totalSpots': 613,
                'openSpots': -1,
                'specialEvent': {}
            },
            {
                'name': 'Government East Garage',
                'shortName': 'east',  # minimum reliable unique string
                'address': ['200 S. Pinckney St.', '100 E. Wilson St.'],
                'totalSpots': 516,
                'openSpots': -1,
                'specialEvent': {}
            },
            {
                'name': 'Overture Center Garage',
                'shortName': 'overture',  # minimum reliable unique string
                'address': ['300 W. Dayton St.', '300 W. Mifflin St.'],
                'totalSpots': 620,
                'openSpots': -1,
                'specialEvent': {}
            },
            {
                'name': 'State Street Capitol Garage',
                'shortName': 'state street capitol',  # minimum reliable unique string
                'address': ['200 N. Carroll St.', '100 W. Dayton St.', '100 W. Johnson St.'],
                'totalSpots': 850,
                'openSpots': -1,
                'specialEvent': {}
            }
        ]


class CityParkingLotsService():
    def __init__(self, city_parking):
        self.lots = city_parking.lots

    def fetch_city_parking_availability_html(self):
        loop = 0
        done = False
        result = None
        retry = 3
        url = 'http://www.cityofmadison.com/parkingUtility/garagesLots/availability/'
        while not done and loop < retry:
            try:
                result = urlfetch.fetch(url)
                done = True
            except urlfetch.DownloadError:
                logging.error("Error fetching url on loop %s. Retry" % loop)
                if (loop + 1) == retry:
                    logging.error("Error fetching %s. Aborting" % url)
                    raise urlfetch.DownloadError
                time.sleep(3)
                loop += 1

        return result.content

    def merge_availability_with_special_events(self, parking_availabilities, special_events):
        for lot in self.lots:
            for availability in parking_availabilities:
                if availability['name'].lower().find(lot['shortName']) >= 0:
                    lot['openSpots'] = availability['openSpots']

            if len(special_events['parkingSpecialEvents']) > 0:
                for special_event in special_events['parkingSpecialEvents']:
                    if special_event['parkingLocation'].lower().find(lot['shortName']) >= 0:
                        lot['specialEvent'] = special_event

        #return {}
    ## end merge_availability_with_special_events

    #  get_city_parking_data builds up lot collection (availability and special events)
    def get_city_parking_data(self):
        parking_availability_html = self.fetch_city_parking_availability_html()
        parking_availabilities = self.transform_city_parking_availability_html_to_dict(parking_availability_html)

        special_events_html = self.fetch_parking_special_events_html()
        special_events = self.transform_city_parking_special_events_html_to_dict(special_events_html)

        self.merge_availability_with_special_events(parking_availabilities, special_events)

        return self.lots

    def transform_city_parking_availability_html_to_dict(self, city_parking_avail_html):
        city_lot_soup = BeautifulSoup(city_parking_avail_html)
        results = []
        lot_spots = -1

        # get all children of the availability div whose class name starts with dataRow
        lot_rows = city_lot_soup.find("div", {"id": "availability"}).findAll("div", {"class": re.compile('^dataRow')})


        #for row_index in range(0, len(lot_rows)):
        #    for detail in lot_rows[row_index]:
        #        if detail.string is not None and detail.string.isdigit():
        #            lot_spots = detail.string

        #    lot_details = {
        #        'name': lot_rows[row_index].div.a.string,
        #        'openSpots': lot_spots
        #    }
        #    results.append(lot_details)

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
        return results

    ## end transform_city_parking_availability_html_to_dict

    def transform_city_parking_special_events_html_to_dict(self, special_events_html, is_test=None):
        special_events = dict()
        special_events['parkingSpecialEvents'] = []

        #invoke soup to parse html
        soup = BeautifulSoup(special_events_html)

        try:
            # special_event_rows is array of <tr>'s.
            special_event_rows = soup.find("table", {"id": "calendar"}).findAll('tr')
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

                # todo - not happy with this whole business of conversion and date math.
                # should be able to optimize
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

                # test-only - sets timestamp of events start:now-1min, end:now+60days
                if is_test:
                    parking_start_time = (datetime.datetime.now(central_tz) -
                                        datetime.timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%S')
                    parking_end_time = (datetime.datetime.now(central_tz) +
                                        datetime.timedelta(days=60)).strftime('%Y-%m-%dT%H:%M:%S')

                # we only care about special_events that are happening now
                if api_utils.datetimeNowIsInRange(
                        datetime.datetime.strptime(parking_start_time, '%Y-%m-%dT%H:%M:%S'),
                        datetime.datetime.strptime(parking_end_time, '%Y-%m-%dT%H:%M:%S'),
                        datetime.datetime.now(central_tz).replace(tzinfo=None)
                ):
                    # add this special event info to the parkingSpecialEvents collection
                    special_events['parkingSpecialEvents'].append(
                        {"parkingLocation": parking_location,
                         "eventVenue": event_venue,
                         "eventTime": event_time,
                         "eventName": event,
                         "parkingStartTime": parking_start_time,
                         "parkingEndTime": parking_end_time})

        except ValueError:
            # bad error. cannot parse html perhaps due to html change.
            logging.error("Error parsing scraped content from city special events page.")
            special_events['parkingSpecialEvents'] = []

        return special_events

    def fetch_parking_special_events_html(self):
        loop = 0
        done = False
        result = None
        special_events_url = 'http://www.cityofmadison.com/parkingUtility/calendar/index.cfm'

        # Looping in case fetch flaky.
        while not done and loop < 3:
            try:
                #grab the city parking html page - what an awesome API!!! :(
                result = urlfetch.fetch(special_events_url)
                done = True

            except urlfetch.DownloadError:
                # problem hitting url, try a few times
                logging.error("Error loading page (%s)... sleeping" % loop)
                if result:
                    logging.debug("Error status: %s" % result.status_code)
                    logging.debug("Error header: %s" % result.headers)
                    logging.debug("Error content: %s" % result.content)
                time.sleep(6)
                loop += 1

        return result.content


application = webapp.WSGIApplication(
    [('/v2/parking', ParkingHandler), ], debug=True
)


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
