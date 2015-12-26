import logging
import time
import datetime
import webapp2 as webapp
import json

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext.webapp.util import run_wsgi_app

from api.v1 import api_utils
from stats_and_maps.stats import stathat


class MainHandler(webapp.RequestHandler):
    # POST not support by the API
    def post(self):
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','The API does not support POST requests')))
        return

    def get(self):
        events = {}

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
              loop = loop+1

        if result is None or result.status_code != 200:
            logging.error("Exiting early: error fetching URL: " + result.status_code)
            return

        #
        # TODO - rework this section to load the realtime data using the
        # async calls in parallel with the scraped event data
        # Because we can cache it, don't worry about it for now, though
        #
        specialEvents = memcache.get('ParkingEvents')
        if specialEvents is None:
            eventsResult = None
            specialEventsWarning = memcache.get('ParkingEventsServiceStatus')
            if((specialEventsWarning < 3) or specialEventsWarning is None):
                eventsResult = getParkingSpecialEvents()
                if eventsResult is None or eventsResult.status_code != 200:
                    logging.error("Error fetching special events URL: " + eventsResult.status_code)
                    specialEvents = []
                    # Ignore race condition - we're not wiping out anything serious if we hit the race anyway
                    # and the atomic incr API doesn't let you set cache expiration times
                    memcache.set('ParkingEventsServiceStatus', 0 if specialEventsWarning is None else specialEventsWarning+1,  6*3600)
                else:
                    specialEvents = json.loads(eventsResult.content)
                    cacheexpiretime = datetime.datetime.strptime(specialEvents['CacheUntil'], "%Y-%m-%dT%H:%M:%S")
                    diff = cacheexpiretime - datetime.datetime.now()
                    seconds = (diff.days*86400) + diff.seconds
                    if seconds < 0:
                        # if the data from scraper is stale we need to ignore it
                        logging.debug('API parking: Special events feed is stale')
                        memcache.set('ParkingEventsServiceStatus', 0 if specialEventsWarning is None else specialEventsWarning+1,  6*3600)
                        specialEvents = {}
                    else:
                        logging.info("API: Caching Special Events Parking for %d more seconds" % seconds)
                        memcache.set('ParkingEvents', specialEvents, seconds)


        searchwindow = self.request.get_range('searchwindow', default=3, min_value=0, max_value=24)
        testingtimeparam = self.request.get('testingts')
        if testingtimeparam is '':
            testingtime = None
        else:
            try:
                testingtime = datetime.datetime.fromtimestamp(float(testingtimeparam))
            except ValueError:
                logging.debug("Invalid date passed for testing, ignoring: %s" % testingtimeparam)

        events = parseSpecialEvents(specialEvents, searchwindow, testingtime)

        soup = BeautifulSoup(result.content)
        json_response = []
        getLots(soup, json_response, "dataRow rowShade");
        getLots(soup, json_response, "dataRow");
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
                lot['address'] = ['430 N. Frances St.','415 N. Lake St.']
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

        # encapsulate response in json or jsonp
        logging.debug('API: json response %s' % json_response)

        callback = self.request.get('callback')
        if callback is not '':
            self.response.headers['Content-Type'] = 'application/javascript'
            self.response.headers['Access-Control-Allow-Origin'] = '*'
            self.response.headers['Access-Control-Allow-Methods'] = 'GET'
            response = callback + '(' + json.dumps(json_response) + ');'
        else:
            self.response.headers['Content-Type'] = 'application/json'
            response = json.dumps(json_response)

        stathat.apiStatCount()
        self.response.out.write(response)

## end RequestHandler

def getLots(soup, response, class_name):
    results = []
    for lot in soup.html.body.findAll("div",{"class":class_name}):
        #logging.debug('lot... %s' % lot);
        #logging.debug('lot.div.a ... %s' % lot.div.a.string)
        for detail in lot:
            if detail.string is not None and detail.string.isdigit():
                #logging.debug('DIGIT %s' % detail.string)
                lot_spots = detail.string

        lot_details = {
            'name' : lot.div.a.string,
            'open_spots' : lot_spots
        }
        response.append(lot_details)

## end

def getParkingSpecialEvents():
    loop = 0
    done = False
    result = None
    specialeventsurl = 'http://www.cityofmadison.com/parkingUtility/calendar/index.cfm'
    cachehours = 24

    #initialize the dict to hold result of scrape.
    specialevents = dict()
    specialevents['CacheUntil'] = datetime.datetime.strftime(api_utils.getLocalDatetime() + datetime.timedelta(hours=+cachehours), '%Y-%m-%dT%H:%M:%S')
    logging.info(specialevents['CacheUntil'])
    specialevents['ParkingSpecialEvents'] = []
    specialevents['LastScraped'] = datetime.datetime.strftime(api_utils.getLocalDatetime(), '%Y-%m-%dT%H:%M:%S')

    # Looping in case fetch flaky.
    while not done and loop < 3:
        try:

            #grab the city parking html page - what an awesome API!!! :(
            result = urlfetch.fetch(specialeventsurl)

            #invoke soup to parse html
            soup = BeautifulSoup(result.content)

            # find the calendar table containing special event info.
            # returns array of <tr>'s.
            special_event_rows = soup.find("table", { "id" : "calendar" }).findAll('tr')

            # loop table rows, starting with 3rd row (excludes 2 header rows)
            for row_index in range(2, len(special_event_rows)):

                # grab the array of cells in the current row
                table_cells = special_event_rows[row_index].findAll('td')

                parkinglocation = table_cells[1].string
                eventvenue = table_cells[4].string
                event = table_cells[3].string

                # take the event time strings (already central time), create datetime obj, then convert back to correct string
                eventtimeobj = datetime.datetime.strptime(table_cells[0].string + api_utils.get_time_from_text(table_cells[5].string)
                                                          .replace(' ',''), '%m/%d/%Y%I:%M%p')
                eventtime = datetime.datetime.strftime(eventtimeobj, '%Y-%m-%dT%H:%M:%S')

                # split '00:00 pm - 00:00 pm' into start and end strings
                timeparts = table_cells[2].string.split(' - ')

                # clean up whitespace to avoid errors due to inconsistent format
                timeparts[0] = timeparts[0].replace(' ', '')
                timeparts[1] = timeparts[1].replace(' ', '')

                parkingstarttimeobj = datetime.datetime.strptime(table_cells[0].string + timeparts[0], '%m/%d/%Y%I:%M%p')
                parkingstarttime = datetime.datetime.strftime(parkingstarttimeobj, '%Y-%m-%dT%H:%M:%S')

                parkingendtimeobj = datetime.datetime.strptime(table_cells[0].string + timeparts[1], '%m/%d/%Y%I:%M%p')
                parkingendtime = datetime.datetime.strftime(parkingstarttimeobj, '%Y-%m-%dT%H:%M:%S')

                # add this special event info to the ParkingSpecialEvents collection
                specialevents['ParkingSpecialEvents'].append({"ParkingLocation":parkinglocation, "EventVenue":eventvenue, "EventTime":eventtime, "Event":event, "ParkingStartTime":parkingstarttime, "ParkingEndTime":parkingendtime})

                # setting content var to keep contract with caller exactly in-tact (for now).
            result.content = json.dumps(specialevents)

            done = True;

        # problem hiting url, try a few times
        except urlfetch.DownloadError:
            logging.error("Error loading page (%s)... sleeping" % loop)
            if result:
                logging.debug("Error status: %s" % result.status_code)
                logging.debug("Error header: %s" % result.headers)
                logging.debug("Error content: %s" % result.content)
            time.sleep(6)
            loop = loop+1

        # This is bad. Some data may be in a differnt format due to
        # either unexpected data entry or *gulp* site redeisgn.
        # Likely require code change to fix.
        except ValueError:
            logging.error("Error parsing scraped content from (%s)... exiting getParkingSpecialEvents()" % specialeventsurl)
            done = True
            result = None
    return result

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
application.error_handlers[500] = api_utils.handle_500

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)
  #wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()