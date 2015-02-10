import os
import wsgiref.handlers
import logging
import webapp2 as webapp
import json

from data_model import StopLocation
from utils.geo import geotypes
from api.v1 import api_utils
from stats import stathat

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api.labs.taskqueue import Task

class GetStopHandler(webapp.RequestHandler):

    def get(self):

      # validate the request parameters
      devStoreKey = validateRequest(self.request,api_utils.GETSTOPS)
      if devStoreKey is None:
          if( not (self.request.get('key') == 'kiosk' and self.request.get('stopID') == '') ):
              logging.error("failed to validate the request parameters")
          self.response.headers['Content-Type'] = 'application/javascript'
          self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','Illegal request parameters')))
          return

      # snare the inputs
      stopID = api_utils.conformStopID(self.request.get('stopID'))
      routeID = self.request.get('routeID')
      destination = self.request.get('destination').upper()
      logging.debug('getstops request parameters...  routeID %s destination %s' % (routeID,destination))

      if api_utils.afterHours() is True:
          # don't run these jobs during "off" hours
	      json_response = api_utils.buildErrorResponse('-1','The Metro service is not currently running')
      elif routeID is not '' and destination is '':
          json_response = routeRequest(routeID, None)
          api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETSTOPS,self.request.query_string,self.request.remote_addr);
      elif routeID is not '' and destination is not '':
          json_response = routeRequest(routeID, destination)
          api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETSTOPS,self.request.query_string,self.request.remote_addr);
      else:
          logging.error("API: invalid request")
          json_response = api_utils.buildErrorResponse('-1','Invalid Request parameters. Did you forget to include a routeID?')
          api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETSTOPS,self.request.query_string,self.request.remote_addr,'illegal query string combination');

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
      # push event out to anyone watching the live board
      task = Task(url='/map/task', params={'stopID':stopID})
      task.add('eventlogger')

    def post(self):
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','The API does not support POST requests')))
        return

## end GetStopHandler

class GetStopLocationHandler(webapp.RequestHandler):

    def get(self):

      # validate the request parameters
      devStoreKey = validateRequest(self.request,api_utils.GETSTOPLOCATION)
      if devStoreKey is None:
          logging.debug("unable to validate the request parameters")
          self.response.headers['Content-Type'] = 'application/javascript'
          self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','Illegal request parameters')))
          return

      # snare the inputs
      stopID = api_utils.conformStopID(self.request.get('stopID'))
      logging.debug('getstoplocation request parameters...  stopID %s' % stopID)

      if api_utils.afterHours() is True:
          # don't run these jobs during "off" hours
	      json_response = api_utils.buildErrorResponse('-1','The Metro service is not currently running')
      elif stopID is not '':
          json_response = stopLocationRequest(stopID)
          api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETSTOPS,self.request.query_string,self.request.remote_addr);
      else:
          logging.error("API: invalid request")
          json_response = api_utils.buildErrorResponse('-1','Invalid Request parameters. Did you forget to include a stpID?')
          api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETSTOPS,self.request.query_string,self.request.remote_addr,'illegal query string combination');

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
      # push event out to anyone watching the live board
      task = Task(url='/map/task', params={'stopID':stopID})
      task.add('eventlogger')

    def post(self):
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','The API does not support POST requests')))
        return

## end GetStopLocationHandler

class GetNearbyStopsHandler(webapp.RequestHandler):

    def get(self):

      # validate the request parameters
      devStoreKey = validateRequest(self.request,api_utils.GETNEARBYSTOPS)
      if devStoreKey is None:
          logging.error("unable to validate the request parameters")
          self.response.headers['Content-Type'] = 'application/json'
          self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','Illegal request parameters')))
          return

      # snare the inputs
      lat = float(self.request.get('lat'))
      lon = float(self.request.get('lon'))
      radius = self.request.get('radius')
      if radius == '' or radius is None:
          radius = 100
      else:
          radius = int(radius)
      routeID = self.request.get('routeID')
      direction = self.request.get('direction')

      # stop location requests...
      json_response = nearbyStops(lat,lon,radius,routeID,direction)

      # encapsulate response in json
      #logging.debug('API: json response %s' % response);
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
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','The API does not support POST requests')))
        return

## end GetNearbyStopsHandler

class DebugHandler(webapp.RequestHandler):

    def get(self):
      # stop location requests...
      response = nearbyStops(43.0637457,-89.4188056,500,None,'westbound')

      # encapsulate response in json
      logging.debug('API: json response %s' % response);
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(json.dumps(response))

## end DebugHandler


class NotSupportedHandler(webapp.RequestHandler):

    def get(self):

      # validate the request parameters
      devStoreKey = validateRequest(self.request)
      if devStoreKey is None:
          logging.warning("API: unsupported method")
          self.response.headers['Content-Type'] = 'application/javascript'
          self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','This method is not yet enabled')))
          return

    def post(self):
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','The API does not support POST requests')))
        return

## end NotSupportedHandler

def getDestinationCode(destination):
    # we have to translate the direction input into a code used
    # for the metro lookup
    destination_code_key = '%s:codekey' % destination
    destination_code = memcache.get(destination_code_key)
    if( destination_code is None ):

        logging.warn('cache miss on destination code %s' % destination)
        destination_listing = db.GqlQuery('select * from DestinationListing where label = :1', destination).get()
        if destination_listing is None:
            logging.error('routeRequest :: unable to locate destination %s in the datastore!?' % destination)
            response_dict = {'status':'0',
                             'info':('Destination %s not found' % destination)
                            }
            return response_dict
        else:
            destination_code = destination_listing.id
            memcache.set(destination_code_key,destination_code)

    return destination_code

def nearbyStops(lat,lon,radius,routeID,direction):

    # limit the radius value to 500
    if radius > 1000:
        radius = 1000

    if routeID is None or routeID == "":
        #logging.debug('nearbyStops (%s,%s,%s,%s)' % (lat,lon,radius,routeID))
        results = StopLocation.proximity_fetch(
             StopLocation.all(),
             geotypes.Point(lat,lon),  # Or db.GeoPt
             max_results=100,
             max_distance=radius)
    else:
        if direction is not None:
            results = StopLocation.proximity_fetch(
                 StopLocation.all().filter('routeID =', routeID).filter('direction =', direction),
                 geotypes.Point(lat,lon),  # Or db.GeoPt
                 max_results=100,
                 max_distance=radius)
        else:
            results = StopLocation.proximity_fetch(
                 StopLocation.all().filter('routeID =', routeID),
                 geotypes.Point(lat,lon),  # Or db.GeoPt
                 max_results=100,
                 max_distance=radius)

    if results is None:
        response_dict = {'status':'0',
                         'info':'No stops found',
                        }
        return response_dict


    response_dict = {'status':'0',}
    stop_results = []
    stop_tracking = []
    for stop in results:
        # kind of a hack, but limit the results to one per route.
        # the query will return multiple results for each stop
        if stop.stopID not in stop_tracking:
            stop_results.append(dict({
                                'stopID':stop.stopID,
                                'intersection':stop.intersection,
                                'latitude':stop.location.lat,
                                'longitude':stop.location.lon,
                                }))
            #logging.debug('appending %s to route tracking list' % stop.stopID)
            stop_tracking.append(stop.stopID)

    response_dict.update({'stop':stop_results})

    return response_dict


def routeRequest(routeID,destination):

    # @fixme memcache these results!
    if destination is not None:

        destination_code = getDestinationCode(destination)
        logging.debug('route listing query for route %s and direction %s' % (routeID,destination_code))
        q = db.GqlQuery('select * from RouteListing where route = :1 and direction = :2 order by route', routeID, destination_code)

    else:

        q = db.GqlQuery('select * from RouteListing where route = :1 order by route', routeID)


    routes = q.fetch(500)
    if routes is None:
        response_dict = {'status':'0',
                         'info':'No stops found'
                        }
        return response_dict

    response_dict = {'status':'0',
                     'timestamp':api_utils.getLocalTimestamp(),
                     'routeID':routeID
                    }

    stop_results = []
    for r in routes:
        stop = r.stopLocation
        if stop is None:
            logging.error('API: ERROR, no location!?')
            continue

        stop_results.append(dict({'stopID' : stop.stopID,
                          'intersection' : stop.intersection,
                          'latitude' : stop.location.lat,
                          'longitude' : stop.location.lon,
                          'destination' : stop.direction,
                          }))

    # add the populated stop details to the response
    response_dict.update({'stops':stop_results})

    return response_dict

## end routeRequest()

def stopLocationRequest(stopID):

    key = 'stopLocation:%s' % stopID
    stop = memcache.get(key)
    if stop is None:
        logging.warn('stopLocation cache MISS - going to the datastore (%s)' % stopID)
        stop = db.GqlQuery('select * from StopLocation where stopID = :1', stopID).get()
        if stop is None:
            logging.error('stopLocationRequest :: unable to locate stop %s in the datastore!?' % stopID)
            response_dict = {'status':'0',
                             'info':('Stop %s not found' % stopID)
                            }
            return response_dict
        else:
            #logging.debug('shoving stop %s entity into memcache' % stopID)
            memcache.set(key,stop)

    return {'status':'0',
            'stopID':stopID,
            'intersection':stop.intersection,
            'latitude':stop.location.lat,
            'longitude':stop.location.lon,
           }

## end stopLocationRequest()

def validateRequest(request,type):

    # validate the key
    devStoreKey = api_utils.validateDevKey(request.get('key'))
    if devStoreKey is None:
        logging.debug('... illegal developer key %s' % request.get('key'))
        api_utils.recordDeveloperRequest(None,api_utils.GETSTOPS,request.query_string,request.remote_addr,'illegal developer key specified');
        return None

    if type == api_utils.GETSTOPS:
        routeID = request.get('routeID')
        destination = request.get('destination').upper()

        # a routeID is required
        if routeID is None or routeID is '':
            api_utils.recordDeveloperRequest(devStoreKey,type,request.query_string,request.remote_addr,'a routeID must be included');
            return None
        elif destination is not None and routeID is '':
            api_utils.recordDeveloperRequest(devStoreKey,type,request.query_string,request.remote_addr,'if a destination is specified, a routeID must be included');
            return None
    elif type == api_utils.GETSTOPLOCATION:
        stopID = api_utils.conformStopID(request.get('stopID'))
        if stopID == '' or stopID == '0' or stopID == '00':
            return None
    elif type == api_utils.GETNEARBYSTOPS:
        lat = request.get('lat')
        lon = request.get('lon')
        radius = request.get('radius')
        # lat/long is required
        if lat is None or lon is None:
            api_utils.recordDeveloperRequest(devStoreKey,type,request.query_string,request.remote_addr,'both latitude and longitude values must be specified');
            return None
        elif radius is not None and radius is not '' and radius > '5000':
            logging.error('unable to validate getnearbystops call. illegal radius value of %s' % radius)
            api_utils.recordDeveloperRequest(devStoreKey,type,request.query_string,request.remote_addr,'radius must be less than 5,000');
            return None

    return devStoreKey

## end validateRequest()

application = webapp.WSGIApplication([('/v1/getstops', GetStopHandler),
                                      ('/v1/getstoplocation', GetStopLocationHandler),
                                      ('/v1/getvehicles', NotSupportedHandler),
                                      ('/v1/getnearbystops', GetNearbyStopsHandler),
                                      ('/v1/getdebug', DebugHandler),
                                      ],
                                     debug=True)
application.error_handlers[500] = api_utils.handle_500

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)
  #wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
