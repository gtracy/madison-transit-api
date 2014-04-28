import logging
import time
import datetime
import webapp2 as webapp
import json
import re

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext.webapp.util import run_wsgi_app

from api.BeautifulSoup import BeautifulSoup, Tag

from api.v1 import api_utils
from stats import stathat



# api/v1/getparking?specialevent

# This class represents all static parking lot data. In considering the tradeoff between
# maintaining this in-app, vs. getting it via dynamic scraping of site, going with in-app to buffer 
# potential issues due to city and UW site changes. The downside is lot info (i.e. total_spots, name)
# could change and the API wouldn't reflect it.
class ParkingLots:
    def __init__(self):
        self.city_lots = [
            {
                'name':'State Street Campus Garage',
                'address':['430 N. Frances St.','415 N. Lake St.'],
                'total_spots':243,
                'open_spots':-1,
                'SpecialEventNotice':{}
            }
        ];

    

class MainHandler(webapp.RequestHandler, ParkingLots):
    def post(self):
        logging.info(ParkingLots.city_lots)
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.headers['Allow'] = 'GET'
        self.response.status = 405 #method not allowed
        self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','The API does not support POST requests')))

    def get(self):

        city_lots = self.get_city_parking_data(ParkingLots().city_lots)
        logging.debug('API: city_lots json response %s' %  city_lots)

        uw_lots = {}
        logging.debug('API: uw_lots json response %s' %  uw_lots)

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


    def append_special_events(self, events, json_response):
        for lot in json_response:
            if lot['name'] == 'Brayton Lot':
                lot['address'] = '1 South Butler St.'
                lot['total_spots'] = '243'
                if events['Brayton Lot']:
                    lot['SpecialEventNotice'] = events['Brayton Lot']
                    #lot['url'] = 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/brayton.cfm'
            elif lot['name'] == 'Capitol Square North Garage':
                lot['address'] = '218 East Mifflin St.'
                lot['total_spots'] = '613'
                if events['Capitol Square North Garage']:
                    lot['SpecialEventNotice'] = events['Capitol Square North Garage']
                    #lot['url'] = 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/capSquareNorth.cfm'
            elif lot['name'] == 'Government East Garage':
                lot['address'] = '215 S. Pinckney St.'
                lot['total_spots'] = '516'
                if events['Government East Garage']:
                    lot['SpecialEventNotice'] = events['Government East Garage']
                    #lot['url'] = 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/govtEast.cfm'
            elif lot['name'] == 'Overture Center Garage':
                lot['address'] = '318 W. Mifflin St.'
                lot['total_spots'] = '620'
                if events['Overture Center Garage']:
                    lot['SpecialEventNotice'] = events['Overture Center Garage']
                    #lot['url'] = 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/overture.cfm'
            elif lot['name'] == 'State Street Campus Garage':
                lot['address'] = ['430 N. Frances St.', '415 N. Lake St.']
                lot['total_spots'] = '1066'
                if events['State Street Campus Garage']:
                    lot['SpecialEventNotice'] = events['State Street Campus Garage']
                    #lot['url'] = 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/stateStCampus.cfm'
            elif lot['name'] == 'State Street Capitol Garage':
                lot['address'] = '214 N. Carroll St.'
                lot['total_spots'] = '855'
                if events['State Street Capitol Garage']:
                    lot['SpecialEventNotice'] = events['State Street Capitol Garage']
                    #lot['url'] = 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/stateStCapitol.cfm'

    def get_city_parking_availability_html(self):
        loop = 0
        done = False
        result = None
        while not done and loop < 3:
            try:
                result = urlfetch.fetch('http://www.cityofmadison.com/parkingUtility/garagesLots/availability/')
                done = True;
            except urlfetch.DownloadError:
                logging.error("Error loading page (%s)... sleeping" % loop)
                if result:
                    logging.debug("Error status: %s" % result.status_code)
                    logging.debug("Error header: %s" % result.headers)
                    logging.debug("Error content: %s" % result.content)
                time.sleep(6)
                loop = loop + 1

        if result is None or result.status_code != 200:
            err_desc = 'Error retrieving city parking data'
            logging.error(err_desc)
            self.response.headers['Content-Type'] = 'application/javascript'
            self.response.status = 500
            self.response.out.write(json.dumps(api_utils.buildErrorResponse('500', err_desc)))

        return result.content

    def get_special_events(self):
        #
        # TODO - rework this section to load the realtime data using the
        # async calls in parallel with the scraped event data
        # Because we can cache it, don't worry about it for now, though
        #
        specialEvents = memcache.get('ParkingEvents')
        if specialEvents is None:
            eventsResult = None
            specialEventsWarning = memcache.get('ParkingEventsServiceStatus')
            if ((specialEventsWarning < 3) or specialEventsWarning is None):
                eventsResult = get_parking_special_events_html()
                if eventsResult is None or eventsResult.status_code != 200:
                    logging.error("Error fetching special events URL: " + eventsResult.status_code)
                    specialEvents = []
                    # Ignore race condition - we're not wiping out anything serious if we hit the race anyway
                    # and the atomic incr API doesn't let you set cache expiration times
                    memcache.set('ParkingEventsServiceStatus',
                                 0 if specialEventsWarning is None else specialEventsWarning + 1, 6 * 3600)
                else:
                    specialEvents = json.loads(eventsResult.content)
                    cacheexpiretime = datetime.datetime.strptime(specialEvents['CacheUntil'], "%Y-%m-%dT%H:%M:%S")
                    diff = cacheexpiretime - datetime.datetime.now()
                    seconds = (diff.days * 86400) + diff.seconds
                    if seconds < 0:
                        # if the data from scraper is stale we need to ignore it
                        logging.debug('API parking: Special events feed is stale')
                        memcache.set('ParkingEventsServiceStatus',
                                     0 if specialEventsWarning is None else specialEventsWarning + 1, 6 * 3600)
                        specialEvents = {}
                    else:
                        logging.info("API: Caching Special Events Parking for %d more seconds" % seconds)
                        memcache.set('ParkingEvents', specialEvents, seconds)
        return specialEvents

    def add_availability_to_city_lots(self, static_city_lot_data, parking_availability, special_events):
        return ''

    #  This will handle complete build up of city lot collection (availability and special events)
    def get_city_parking_data(self, static_city_lot_data):

        parking_availability_html = self.get_city_parking_availability_html()
        parking_availability = self.transform_city_parking_availability_html_to_dict(parking_availability_html)

        special_events_html = get_parking_special_events_html()
        special_events = transform_city_parking_special_events_html_to_dict(special_events_html)

        city_lots = self.add_availability_to_city_lots(static_city_lot_data, parking_availability, special_events)

        return {}


    def transform_city_parking_availability_html_to_dict(self, city_parking_avail_html):
        city_lot_soup = BeautifulSoup(city_parking_avail_html)
        results = []

        # get all children of the availability div whose class name starts with dataRow
        lot_rows = city_lot_soup.find("div", {"id":"availability"}).findAll("div", {"class":re.compile('^dataRow')})

        for row_index in range(1, len(lot_rows)):
            for detail in lot_rows[row_index]:
                if detail.string is not None and detail.string.isdigit():
                    lot_spots = detail.string

            lot_details = {
                'name' : lot_rows[row_index].div.a.string,
                'open_spots' : lot_spots
            }
            results.append(lot_details)

        logging.debug(json.dumps(results))
        return results

    ## end


def transform_city_parking_special_events_html_to_dict(special_events_html):

    cache_hours = 24
    special_events = dict()
    special_events['CacheUntil'] = datetime.datetime.strftime(api_utils.getLocalDatetime() + datetime.timedelta(hours=+cache_hours), '%Y-%m-%dT%H:%M:%S')
    special_events['ParkingSpecialEvents'] = []
    special_events['LastScraped'] = datetime.datetime.strftime(api_utils.getLocalDatetime(), '%Y-%m-%dT%H:%M:%S')

    #invoke soup to parse html
    soup = BeautifulSoup(special_events_html)

    try:
        # find the calendar table containing special event info.
        # returns array of <tr>'s.
        special_event_rows = soup.find("table", {"id": "calendar"}).findAll('tr')
        # loop table rows, starting with 3rd row (excludes 2 header rows)
        for row_index in range(2, len(special_event_rows)):
            # grab the array of cells in the current row
            table_cells = special_event_rows[row_index].findAll('td')

            parking_location = table_cells[1].string
            event_venue = table_cells[4].string
            event = table_cells[3].string

            # take the event time strings (already central time), create datetime obj, then convert back to correct string
            event_time_obj = datetime.datetime.strptime(table_cells[0].string + table_cells[5].string.replace(' ', ''),
                                                      '%m/%d/%Y%I:%M%p')
            event_time = datetime.datetime.strftime(event_time_obj, '%Y-%m-%dT%H:%M:%S')

            # split '00:00 pm - 00:00 pm' into start and end strings
            time_parts = table_cells[2].string.split(' - ')

            # clean up whitespace to avoid errors due to inconsistent format
            time_parts[0] = time_parts[0].replace(' ', '')
            time_parts[1] = time_parts[1].replace(' ', '')

            parking_start_time_obj = datetime.datetime.strptime(table_cells[0].string + time_parts[0], '%m/%d/%Y%I:%M%p')
            parking_start_time = datetime.datetime.strftime(parking_start_time_obj, '%Y-%m-%dT%H:%M:%S')

            parking_end_time_obj = datetime.datetime.strptime(table_cells[0].string + time_parts[1], '%m/%d/%Y%I:%M%p')
            parking_end_time = datetime.datetime.strftime(parking_start_time_obj, '%Y-%m-%dT%H:%M:%S')

            ###############testing data ##############   Comment this out!!!!  ######################################################
            parking_start_time = '2014-04-25T01:00:00'
            parking_end_time = '2014-04-25T23:00:00'

            # add this special event info to the ParkingSpecialEvents collection
            special_events['ParkingSpecialEvents'].append(
                {"ParkingLocation": parking_location, "EventVenue": event_venue, "EventTime": event_time, "Event": event,
                 "ParkingStartTime": parking_start_time, "ParkingEndTime": parking_end_time})

    except ValueError:
        # This is bad. Some data may be in a different format due to
        # either unexpected data entry or *gulp* site redesign.
        # Likely require code change to fix. Still, not throwing 500
        # as special events data is less critical than parking availability
        logging.error("Error parsing scraped content from city special events page.")
        special_events['ParkingSpecialEvents'] = []

        # setting content var to keep contract with caller exactly in-tact (for now).
    return special_events


def get_parking_special_events_html():
    loop = 0
    done = False
    result = None
    special_events_url = 'http://www.cityofmadison.com/parkingUtility/calendar/index.cfm'

    # Looping in case fetch flaky.
    while not done and loop < 3:
        try:
            #grab the city parking html page - what an awesome API!!! :(
            result = urlfetch.fetch(special_events_url)
            done = True;


        except urlfetch.DownloadError:
            # problem hiting url, try a few times
            logging.error("Error loading page (%s)... sleeping" % loop)
            if result:
                logging.debug("Error status: %s" % result.status_code)
                logging.debug("Error header: %s" % result.headers)
                logging.debug("Error content: %s" % result.content)
            time.sleep(6)
            loop = loop+1

    return result.content

def parseSpecialEvents(se, searchwindow, providedtime=None):
    ramps = {}

    # Erik is a crappy python programmer, exhibit A
    # We're going to hand this array back to the caller
    # It should probably just look and see if there's a key
    # defined for a ramp rather than trusting that
    # it was explicitly set to none. 
    #
    # Someday, make these lists of events
    #

    ramps['Brayton Lot'] = None
    ramps['Capitol Square North Garage'] = None
    ramps['Government East Garage'] = None
    ramps['Overture Center Garage'] = None
    ramps['State Street Campus Garage'] = None
    ramps['State Street Capitol Garage'] = None
    
    # bale if the the special events map is empty
    if not se:
        return ramps

    # for testing purposes, we allow for the notion
    # of "current time" to be provided at by the API
    if providedtime is None:
        ltime = datetime.datetime.now()
    else:
        ltime = providedtime

    # GAE stores times in UTC, but the scraper stores them in central time.
    ltime += datetime.timedelta(hours = -6)

    logging.debug("API: searchiwindow is %d" % searchwindow)
    logging.debug("API: It is %s" % ltime.strftime('%m/%d/%Y %H:%M:%S %Z'))
    for e in se['ParkingSpecialEvents']:
         warntime = datetime.datetime.strptime(e['ParkingStartTime'], "%Y-%m-%dT%H:%M:%S") + datetime.timedelta(hours=-searchwindow)
         endtime = datetime.datetime.strptime(e['ParkingEndTime'], "%Y-%m-%dT%H:%M:%S") 
         if(ltime > warntime and ltime < endtime):
             logging.debug("API: Considering %s starting at time %s in ramp %s " % (e['Event'], e['ParkingStartTime'], e['ParkingLocation']))
             if(e['ParkingLocation'].lower().find("brayton") >= 0):
                 logging.debug("Assigned it to brayton")
                 ramps['Brayton Lot'] = e
             elif(e['ParkingLocation'].lower().find("north") >= 0):
                 logging.debug("Assigned it to cap north")
                 ramps['Capitol Square North Garage'] = e
             elif(e['ParkingLocation'].lower().find("east") >= 0):
                 logging.debug("Assigned it to assigned it to gov east")
                 ramps['Government East Garage'] = e
             elif(e['ParkingLocation'].lower().find("overture") >= 0):
                 logging.debug("Assigned it to overture")
                 ramps['Overture Center Garage'] = e 
             elif(e['ParkingLocation'].lower().find("campus") >= 0):
                 logging.debug("Assigned it to state st campus")
                 ramps['State Street Campus Garage'] = e 
             elif(e['ParkingLocation'].lower().find("capitol") >= 0):
                 logging.debug("Assigned it to state st capitol")
                 ramps['State Street Capitol Garage'] = e
             del e['ParkingLocation'] # at this point, it's dupliciative
    return ramps

application = webapp.WSGIApplication([('/v1/getparking', MainHandler),
                                      ],
                                     debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)
  #wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
