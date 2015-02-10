import logging
import webapp2 as webapp
import json

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

from api.v1 import api_utils
from stats import stathat
from data_model import RouteListing

class StaticAPIs(db.Model):
    method = db.StringProperty()
    json   = db.TextProperty()
    date   = db.DateTimeProperty(auto_now_add=True)
#

class MainHandler(webapp.RequestHandler):

    def get(self):

      # validate the request parameters
      devStoreKey = validateRequest(self.request,api_utils.GETROUTES)
      if devStoreKey is None:
          logging.debug("unable to validate the request parameters")
          self.response.headers['Content-Type'] = 'application/javascript'
          self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','Illegal request parameters')))
          return

      logging.debug('getroutes request...  ')
      if self.request.get('force') is not '':
          refresh = True
      else:
          refresh = False

      if api_utils.afterHours() is True:
          # don't run these jobs during "off" hours
	      json_response = api_utils.buildErrorResponse('-1','The Metro service is not currently running')
      else:
          if refresh is True:
              json_response = getRoutes(refresh)

              # drop it into the memcache again
              memcache.set(api_utils.GETROUTES, json_response)
              logging.debug('---> storing in memcache');
          else:
              logging.debug('---> memcache hit');
              json_response = memcache.get(api_utils.GETROUTES)
              if json_response is None:
                  json_response = getRoutes(refresh)

                  # drop it into the memcache again
                  memcache.set(api_utils.GETROUTES, json_response)
                  logging.debug('---> storing in memcache');


          # record the API call for this devkey
          api_utils.recordDeveloperRequest(devStoreKey,api_utils.GETROUTES,self.request.query_string,self.request.remote_addr);

      #logging.debug('API: json response %s' % json_response);
      callback = self.request.get('callback')
      if callback is not '':
          self.response.headers['Content-Type'] = 'application/javascript'
          self.response.headers['Access-Control-Allow-Origin'] = '*'
          self.response.headers['Access-Control-Allow-Methods'] = 'GET'
          response = callback + '(' + json.dumps(json_response) + ');'
      else:
          self.response.headers['Content-Type'] = 'application/json'
          response = json_response

      self.response.out.write(response)
      stathat.apiStatCount()

    def post(self):
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.out.write(json.dumps(api_utils.buildErrorResponse('-1','The API does not support POST requests')))
        return

## end MainHandler


def getRoutes(refresh):

    if refresh is False:
        # do we already have it in the datastore?
        api = db.GqlQuery('select * from StaticAPIs where method = :1', api_utils.GETROUTES).get()
        if api is not None:
            logging.debug('---> datastore hit');
            return api.json

    logging.debug('---> datastore lookup starting!')
    offset = 0
    q = RouteListing.all()
    routes = q.fetch(1000)

    hits = {}
    response_dict = {'status':0,'timestamp':api_utils.getLocalTimestamp()}
    while len(routes) > 0:
        offset += len(routes)

        ## stopped here trying to create a map of unique routes and endpoints
        ##
        for r in routes:
            # are we tracking this route/direction pair?
            key = r.route + ':' + r.direction
            hits[key] = hits.get(key,0) + 1

        # get more routes
        routes = q.fetch(1000,offset)

    routeMap = {}
    for k,v in hits.iteritems():
        key = k.split(':')
        routeID = key[0]
        direction = key[1]
        directionLabel = api_utils.getDirectionLabel(direction)

        logging.debug('adding direction %s to route %s' % (directionLabel,routeID))
        if routeID in routeMap:
            routeMap[routeID].append(directionLabel)
        else:
            routeMap[routeID] = list()
            routeMap[routeID].append(directionLabel)

    route_results = []
    for k,v in routeMap.iteritems():
        route_results.append(dict({'routeID':k,'directions':routeMap[k]}))

    # add the populated route details to the response
    response_dict.update({'routes':route_results})
    json_results = json.dumps(response_dict)

    static = StaticAPIs()
    static.method = api_utils.GETROUTES
    static.json = json_results
    static.put()

    return json_results

## end getRoutes()

def validateRequest(request,type):

    # validate the key
    devStoreKey = api_utils.validateDevKey(request.get('key'))
    if devStoreKey is None:
        api_utils.recordDeveloperRequest(None,api_utils.GETSTOPS,request.query_string,request.remote_addr,'illegal developer key specified');
        return None

    return devStoreKey

## end validateRequest()

application = webapp.WSGIApplication([('/v1/getroutes', MainHandler),
                                      ],
                                     debug=True)
application.error_handlers[500] = api_utils.handle_500

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)
  #wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
