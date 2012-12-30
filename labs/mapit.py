import os
import wsgiref.handlers
import logging
from operator import itemgetter

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.db import GeoPt
from google.appengine.ext.webapp import template
from google.appengine.api.labs.taskqueue import Task

from google.appengine.runtime import apiproxy_errors
from data_model import PhoneLog
from data_model import StopLocation
from data_model import RouteListing


class MapHandler(webapp.RequestHandler):
    def get(self):
      
      # review the results for popular stops
      reqs = getRequestedStops();
      stops_stats = []
      keyLookup = []
      totalReqs = 0
      for key,value in reqs.items():
          stops_stats.append({'stopID':key,
                              'count':value,
                              })
          totalReqs += value
          keyLookup.append(key+':loc')

      # do we have the stop locations?
      stopLocations = memcache.get_multi(keyLookup) #reqs.keys())
      if stopLocations is None or len(stopLocations) == 0:
          logging.error("unable to find stop locations!?")
          # create an event to go get this data
          task = Task(url='/labs/maptask', params={'clean':'1',})
          task.add('crawler')
          msg = "no data"
      else:
          logging.debug('yes... found cached copies of the stop locations!')
          msg = "your data"
          
      locations = []
      median = 2.5
      logging.debug('found a total of %s requests with a median %s' % (str(totalReqs),str(median)))
      for key,value in stopLocations.items():
          if value is None:
              continue;

          stopID = key.split(':')[0]
          # normalized value = count/median * %Total + (count-median)+ base
          weight = (float(reqs[stopID]) / median) + float(reqs[stopID]) - median + 75.0
          logging.debug('%s / %s weight is %s' % (stopID,reqs[stopID],str(weight)))
          locations.append({'stopID':stopID,
                            'location':value,
                            'count':reqs[stopID],
                            'weight':weight,
                            })
          
      template_values = {'stops':stops_stats,
                         'locations':locations,
                         'message':msg,
                         }
        
      # create a page that provides a form for sending an SMS message
      path = os.path.join(os.path.dirname(__file__), 'mapit.html')
      self.response.out.write(template.render(path,template_values))
    
## end MapHandler()

class DisplayStops(webapp.RequestHandler):
    def get(self):
        reqs = getRequestedStops();
        stops_stats = []
        for key,value in reqs.items():
            # try to figure out if we have a stoplocation for each id
            stop = db.GqlQuery("SELECT * FROM StopLocation where stopID = :1", key).get()
            if stop is None:
                stops_stats.append({'stopID':key,
                                    'count':value,
                                  })
        template_values = {'stops':stops_stats,
                           }
        
        # create a page that provides a form for sending an SMS message
        path = os.path.join(os.path.dirname(__file__), 'stops.html')
        self.response.out.write(template.render(path,template_values))
                
## end DisplayStops

class FixStopForm(webapp.RequestHandler):
    def get(self):
        template_values = {'stopID':self.request.get('stopID')}
        # create a page that provides a form for sending an SMS message
        path = os.path.join(os.path.dirname(__file__), 'fixstop.html')
        self.response.out.write(template.render(path,template_values))
        
## end FixStop

class FixStop(webapp.RequestHandler):
    def post(self):
        stopID = self.request.get('stopID')
        lat = self.request.get('lat')
        lon = self.request.get('lon')

        stop = StopLocation()
        stop.stopID = stopID
        stop.routeID = '00'
        stop.intersection = self.request.get('intersection').upper()
        stop.location = GeoPt(lat,lon)
        stop.update_location()
        stop.direction = '00'
        logging.debug('created new stoplocation for %s' % stopID)
        stop.put()
        
        routeQ = db.GqlQuery("SELECT * FROM RouteListing WHERE stopID = :1", stopID)
        routes = routeQ.fetch(100)
        if len(routes) > 0:
            for r in routes:
                logging.debug('updating route %s with new location' % r.route)
                r.stopLocation = stop
                r.put()

        self.redirect('http://smsmybus.com/labs/displaystops')
        
## end FixStop

class CollectorHandler(webapp.RequestHandler):
    def post(self):
        self.get()
        
    def get(self):
      # do some analysis on the request history...
      reqs = getRequestedStops()

      # find that lat/longs for all the stops
      validStops = reqs.keys()      
      stopLocs = memcache.get_multi(validStops)
      if self.request.get('clean') or stopLocs is None:
        memcache.delete_multi(validStops)
        logging.debug("logging stop locations!")
        locations = dict()
        cursor = None
        # Start a query for all stop locations
        q = StopLocation.all()
        while q is not None:
          # If the app stored a cursor during a previous request, use it.
          if cursor:
              q.with_cursor(cursor)

          # Perform the query to get results.
          locationQuery = q.fetch(1000)
          cursor = q.cursor()
          if len(locationQuery) > 0:
            logging.debug('just read in another chunk of stop locations...')
            for l in locationQuery:
                location = l.location
                stopKey = l.stopID + ':loc'
                if l.stopID in validStops and stopKey not in stopLocs:
                    logging.debug('adding location %s for stopID %s' % (location,l.stopID))
                    stopLocs[stopKey] = location
          else:
              logging.debug('No more stop locations left in the query!')
              break
          
      memcache.set_multi(stopLocs)
      return
    
## end CollectorHandler

# @todo memcache this list
# @todo create a task that periodically refreshes this list
def getRequestedStops():
      # do some analysis on the request history...
      reqs = dict()
      cursor = None
      # Start a query for all Person entities.
      q = PhoneLog.all()
      while q is not None:
          # If the app stored a cursor during a previous request, use it.
          if cursor:
              q.with_cursor(cursor)

          logQuery = q.fetch(1000)
          cursor = q.cursor()
          if len(logQuery) > 0:
            # run through all of the results and add up the number of 
            # requests for each stopID
            #
            for e in logQuery:
                # add up all of the unique stop IDs
                requestString = e.body.split()
                if len(requestString) >= 2:
                    stopID = requestString[1]
                elif len(requestString) > 0:
                    stopID = requestString[0]
                
                if len(requestString) > 0 and stopID.isdigit() and len(stopID) == 4:
                    if stopID in reqs:
                        reqs[stopID] += 1
                    else:
                        #logging.debug('new stop found... %s' % stopID)
                        reqs[stopID] = 1
          else:
              logging.debug('nothing left!')
              break
      return reqs
## end

class SpawnCollector(webapp.RequestHandler):
    def post(self):
        self.get()
        
    def get(self):
          # create an event to go get this data
          task = Task(url='/labs/maptask', params={'clean':'1',})
          task.add('crawler')
        
def main():
  logging.getLogger().setLevel(logging.DEBUG)
  application = webapp.WSGIApplication([('/labs/map', MapHandler),
                                        ('/labs/maptask', CollectorHandler),
                                        ('/labs/spawncollector', SpawnCollector),
                                        ('/labs/displaystops', DisplayStops),
                                        ('/labs/fixstop', FixStop),
                                        ('/labs/fixstopform', FixStopForm),
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
