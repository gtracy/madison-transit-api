import logging
import re
import webapp2 as webapp
import json
import urllib

from google.appengine.api import urlfetch
from google.appengine.ext.webapp.util import run_wsgi_app

from api import asynch
from api.v1 import api_utils
from stats_and_maps.stats import stathat

class MainHandler(webapp.RequestHandler):

    def get(self):

        # validate the request parameters
        devStoreKey = validateRequest(self.request)
        if devStoreKey is None:
            logging.debug("unable to validate the request parameters")
            self.response.headers['Content-Type'] = 'application/javascript'
            self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','Illegal request parameters')))
            return

        # snare the inputs
        routeID = self.request.get('routeID')
        logging.debug('getvehicles request parameters...  routeID %s' % routeID)

        if api_utils.afterHours() is True:
            # don't run these jobs during "off" hours
            json_response = api_utils.buildErrorResponse('-1', 'The Metro service is not currently running')
        elif routeID is not '':
            json_response = routeRequest(routeID)
            api_utils.recordDeveloperRequest(devStoreKey, api_utils.GETVEHICLES, self.request.query_string, self.request.remote_addr);
        else:
            logging.error("API: invalid request")
            json_response = api_utils.buildErrorResponse('-1','Invalid Request parameters. Did you forget to include a routeID?')
            api_utils.recordDeveloperRequest(devStoreKey, api_utils.GETVEHICLES, self.request.query_string, self.request.remote_addr,'illegal query string combination');

        #logging.debug('API: json response %s' % json_response);
        # encapsulate response in json
        callback = self.request.get('callback')
        if callback is not '':
            self.response.headers['Content-Type'] = 'application/javascript'
            self.response.headers['Access-Control-Allow-Origin'] = '*'
            self.response.headers['Access-Control-Allow-Methods'] = 'GET'
            response = callback + '(' + json.dumps(json_response) + ');'
        else:
            self.response.headers['Content-Type'] = 'application/json'
            response = json.dumps(json_response)

        self.response.out.write(response)
        stathat.apiStatCount()

    def post(self):
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','The API does not support POST requests')))
        return

## end MainHandler

VEHICLE_URL_BASE = "http://webwatch.cityofmadison.com/TMWebWatch/GoogleMap.aspx/getVehicles"
def routeRequest(routeID):

    # need to first translate the routeID into the
    # internal Metro code for that route.
    route = asynch.getRouteListing(routeID=routeID)
    if not route or len(route) is 0:
        logging.error("Exiting early: unable to locate route listing: " + routeID)
        return api_utils.buildErrorResponse('-1', 'Unknown routeID')
    else:
        metro_route_code = route[0].routeCode
        logging.debug('%s - %s' % (routeID, metro_route_code))

    # now go fetch the vehicle details from Metro...
    loop = 0
    done = False
    result = None
    while not done and loop < 3:
        try:
            payload = {}
            payload['routeID'] = metro_route_code
            headers = {'Content-Type': 'application/json'}
            result = urlfetch.fetch(
                url=VEHICLE_URL_BASE,
                payload=json.dumps(payload),
                method=urlfetch.POST,
                headers=headers)
            done = True
        except urlfetch.Error:
            logging.error("Error loading page (%s)... sleeping" % loop)
            if result:
                logging.debug("Error status: %s" % result.status_code)
                logging.debug("Error header: %s" % result.headers)
                logging.debug("Error content: %s" % result.content)
            time.sleep(6)
            loop = loop+1

    logging.error(result.status_code)
    logging.error(result.content)
    if result is None or result.status_code != 200:
        logging.error("Exiting early: error fetching URL: " + result.status_code)
        return api_utils.buildErrorResponse('-1', 'Error reading live Metro feed')

    # vehicle results are in a JSON array
    # { "d" : [ {}, {} ] }
    logging.debug('now parse the JSON')
    json_result = json.loads(result.content)
    logging.error(json_result)
    vehicles = json_result['d']
    logging.debug(vehicles)

    # setup the core response object
    results = dict({'status' : 0,
                    'routeID' : routeID,
                    'count' : len(vehicles)-1,
                    'timestamp' : api_utils.getLocalTimestamp(),
                    'vehicles' : list()})

    # loop through all vehicles on the route and parse
    # out details for the response
    for v in vehicles:
        if v == vehicles[-1]:
            break
        logging.error(v)
        spot = dict({'lat':v['lat'],
                     'lon':v['lon'],
                     'direction':v['directionName'],
                     'vehicleID':v['propertyTag'],
                     'nextStop':v['nextStop'],

                     'bikeRack':v['bikeRack'],
                     'wifiAccess':v['wiFiAccess'],
                     'wheelChairAccessible':v['wheelChairAccessible'],
                     'wheelChairLift':v['wheelChairLift']})
        results['vehicles'].append(spot)

    return results

## routeRequest()


def validateRequest(request):

    # validate the key
    devStoreKey = api_utils.validateDevKey(request.get('key'))
    if devStoreKey is None:
        api_utils.recordDeveloperRequest(None, api_utils.GETSTOPS, request.query_string, request.remote_addr, 'illegal developer key specified');
        return None

    routeID = request.get('routeID')
    if routeID is None or routeID is '':
        api_utils.recordDeveloperRequest(devStoreKey,type,request.query_string,request.remote_addr,'a routeID must be included');
        return None

    return devStoreKey

## end validateRequest()


application = webapp.WSGIApplication([('/v1/getvehicles', MainHandler)
                                      ],
                                     debug=True)
application.error_handlers[500] = api_utils.handle_500

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
