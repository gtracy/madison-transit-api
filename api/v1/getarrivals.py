import os
import wsgiref.handlers
import logging
import time
import webapp2 as webapp
import json

from google.appengine.api import memcache
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api.labs.taskqueue import Task
from google.appengine.runtime import DeadlineExceededError

from api.v1 import api_utils
from api import asynch
from stats import stathat
import config


class MainHandler(webapp.RequestHandler):

    def post(self):
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','The API does not support POST requests')))
        return
    
    def get(self):
      start = time.time()
      dev_key = self.request.get('key')

      try:
          if api_utils.afterHours() is False:

              # validate the request parameters
              devStoreKey = validateRequest(self.request)
              if devStoreKey is None:
                  # filter out the kiosk errors from the log
                  if( not (dev_key == 'kiosk' and self.request.get('stopID') == '') ):
                      logging.error("failed to validate the request parameters")
                  self.response.headers['Content-Type'] = 'application/javascript'
                  self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','Unable to validate the request. There may be an illegal developer key.')))
                  return

              # snare the inputs
              stopID = api_utils.conformStopID(self.request.get('stopID'))
              routeID = self.request.get('routeID')
              vehicleID = self.request.get('vehicleID')
              #logging.debug('getarrivals request parameters...  stopID %s routeID %s vehicleID %s' % (stopID,routeID,vehicleID))
              
              if stopID is not '' and routeID is '':
                  json_response = stopRequest(stopID, dev_key)
                  api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETARRIVALS,self.request.query_string,self.request.remote_addr);
              elif stopID is not '' and routeID is not '':
                  json_response = stopRouteRequest(stopID, routeID, devStoreKey)
                  api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETARRIVALS,self.request.query_string,self.request.remote_addr);
              elif routeID is not '' and vehicleID is not '':
                  json_response = routeVehicleRequest(routeID, vehicleID, devStoreKey)
                  api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETVEHICLE,self.request.query_string,self.request.remote_addr);
              else:
                  logging.debug("API: invalid request")
                  api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETARRIVALS,self.request.query_string,self.request.remote_addr,'illegal query string combination');
                  json_response = api_utils.buildErrorResponse('-1','Invalid Request parameters')

          else:
              # don't run these jobs during "off" hours
              #logging.debug('shunted... off hour request')
              json_response = api_utils.buildErrorResponse('-1','The Metro service is not currently running')

          # encapsulate response in json or jsonp
          #logging.debug('API: json response %s' % json_response);

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
      except DeadlineExceededError:
          self.response.clear()
          self.response.set_status(500)
          self.response.out.write("This operation could not be completed in time...")

      stathat.apiTimeStat(config.STATHAT_API_GETARRIVALS_TIME_KEY,((time.time()-start)*1000))
      stathat.apiStatCount()
      # push event out to anyone watching the live board
      channels = memcache.get('channels')
      if channels is not None:
          task = Task(url='/map/task', params={'stopID':stopID})
          task.add('eventlogger')

## end RequestHandler

def validateRequest(request):
    
    # validate the key
    devStoreKey = api_utils.validateDevKey(request.get('key'))
    if devStoreKey is None:
        api_utils.recordDeveloperRequest(None,api_utils.GETARRIVALS,request.query_string,request.remote_addr,'illegal developer key specified');
        return None
    stopID = request.get('stopID')
    routeID = request.get('routeID')
    vehicleID = request.get('vehicleID')
    
    # give up if someone asked for stop 0, which seems to be popular for some reason
    #logging.debug('validating stopID %s' % stopID);
    if stopID == '' or stopID is '0' or stopID is '0000':
        return None
        
    # a stopID or routeID is required
    if stopID is None and routeID is None:
        api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETARRIVALS,request.query_string,request.remote_addr,'either a stopID or a routeID must be included');
        return None
    
    # the routeID requires either a vehicleID or stopID
    if routeID is not None:
        if vehicleID is None and stopID is None:
            api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETARRIVALS,request.query_string,request.remote_addr,'if routeID is specified, either a vehicleID or stopID is required');
            return None
    
    # the vehicleID requires a routeID
    if vehicleID is not None:
        if routeID is None:
            api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETVEHICLE,request.query_string,request.remote_addr,'if a vehicleID is specified, you must include a routeID');
            return False
        
    # we've noticed some flagrant abuses of the API where the format
    # of the request parameters are just bogus. check those here
    if len(stopID) > 4:
        return None
        
    #logging.debug("successfully validated command parameters")
    return devStoreKey

## end validateRequest()

def stopRequest(stopID, devKey):

    #logging.debug("Stop Request started")
    response_dict = None
    
    # if this is a kiosk request, grab the cached result
    if( devKey.find('kiosk') >= 0 ):
        #logging.debug('kiosk request. check for cache hit')
        # look for memcahced results
        results_cache_key = 'kiosk::%s' % stopID
        response_dict = memcache.get(results_cache_key)
        if( response_dict is None ):
            logging.debug('gettarrivals : kiosk cache miss')

    if( response_dict is None ):
        response_dict = {'status':'0',
                         'timestamp':api_utils.getLocalTimestamp()
                         }    

        # unique key to track this request
        t = str(time.time()).split('.')[0]
        sid = '%s::%s::%s' % (stopID,devKey,t)

        # fetch all of the data for this stop
        routes = asynch.aggregateBusesAsynch(sid,stopID)
        if routes is None or len(routes) == 0:
            response_dict['status'] = '-1'
            response_dict['description'] = 'No routes found for this stop'
            response_dict['stopID'] = stopID
            return response_dict

        # get the stop details
        stop_dict = {'stopID':stopID,}
        
        # take the first 10 results. we assume the results are sorted by time
        #route_results = sorted(route_results, key=attrgetter('time'))
        route_results = []
        for r in routes:
            minutes = api_utils.computeCountdownMinutes(r.arrivalTime)
            if minutes > 0:
                route_results.append(dict({'routeID':r.routeID,
                              'vehicleID':'unknown',
                              'minutes':str(minutes),
                              'arrivalTime':r.arrivalTime,
                              'destination':r.destination,
                              }))            
        
        # add the populated stop details to the response
        stop_dict.update({'route':route_results});
        response_dict.update({'stop':stop_dict})
            
        # cleanup the results
        asynch.clean(sid)

        # cache results if it is from a kiosk
        if( devKey.find('kiosk') >= 0 ):
            # look for memcahced results
            results_cache_key = 'kiosk::%s' % stopID
            memcache.set(results_cache_key,response_dict,75)
            #logging.debug('gettarrivals : kiosk cache set')

    else:
        logging.debug('getarrivals : kiosk cash hit')
        response_dict['cached'] = True

    return response_dict

## end stopRequest()


def stopRouteRequest(stopID, routeID, devStoreKey):
    logging.debug("Stop/Route Request started")

    # got fetch all of the data for this stop
    sid = stopID + str(devStoreKey) + str(time.time())
    routes = asynch.aggregateBusesAsynch(sid,stopID,routeID)
    if routes is None:
        response_dict = {'status':'0',
                         'timestamp':api_utils.getLocalTimestamp(),
                         'info':'No routes found'
                        }
        return response_dict
    
    response_dict = {'status':'0',
                     'timestamp':api_utils.getLocalTimestamp()
                     }    
    
    # there should only be results. we assume the results are sorted by time
    stop_dict = {'stopID':stopID,}
    route_results = []
    for r in routes:
        if not api_utils.inthepast(r.arrivalTime):
            route_results.append(dict({'routeID':r.routeID,
                          'vehicleID':'unknown',
                          'minutes':str(api_utils.computeCountdownMinutes(r.arrivalTime)),
                          'arrivalTime':r.arrivalTime,
                          'destination':r.destination,
                          }))
    
    # add the populated stop details to the response
    stop_dict.update({'route':route_results});
    response_dict.update({'stop':stop_dict})
        
    return response_dict

## end stopRouteRequest()

def routeVehicleRequest(routeID, vehicleID, devStoreKey):
    logging.debug("Route/Vehicle Request started for %s, route %s vehicle %s" % (devStoreKey,routeID,vehicleID))
    
    # encapsulate response in json
    return {'status':'-1',
            'timestamp':getLocalTimestamp(),
            'description':'Vehicle requests calls are not yet supported',
           }

## end stopRouteRequest()


application = webapp.WSGIApplication([('/v1/getarrivals', MainHandler),
                                      ],
                                     debug=True)


def main():
  logging.getLogger().setLevel(logging.ERROR)
  run_wsgi_app(application)
  #wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()

