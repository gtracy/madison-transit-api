import wsgiref.handlers
import logging
import os

from google.appengine.api.taskqueue import Task
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.db import GeoPt

from data_model import RouteListing
from data_model import StopLocation
from data_model import StopLocationLoader

#
# This handler is designed to port the GTFS Stops loaded via the bulk loader
# It simply creates a number of background tasks to do the grunt work
#
class PortStopsHandler(webapp.RequestHandler):
    def get(self):
    
        # query the StopLocationLoader for all stops
        q = db.GqlQuery("select * from StopLocationLoader")
        stops = q.fetch(500)
        offset = 500
        while stops is not None and len(stops) > 0:
            for s in stops:
                # create a new task for each stop
                task = Task(url='/gtfs/port/stop/task/', 
                            params={'stopID':s.stopID,
                                    'name':s.name,
                                    'description':s.description,
                                    'lat':str(s.lat),
                                    'lon':str(s.lon),
                                    'direction':s.direction,
                                   })
                task.add('crawler')
                
            # get the next bunch of stops from the query
            stops = q.fetch(500,offset)
            offset += 500

        logging.debug('Finished spawning %s StopLocationLoader tasks!' % str(offset-500))
        self.response.out.write('done spawning porting tasks!')
    
## end PortStopsHandler

#
# This handler is the task handler for porting an individual GTFS stop
#
class PortStopTask(webapp.RequestHandler):
    def post(self):
        stop_list = []
        route_list = []
        
        stopID      = self.request.get('stopID')
        if len(stopID) == 1:
            stopID = "000" + stopID
        if len(stopID) == 2:
            stopID = "00" + stopID
        if len(stopID) == 3:
            stopID = "0" + stopID
            
        name        = self.request.get('name')
        description = self.request.get('description')
        lat         = self.request.get('lat')
        lon         = self.request.get('lon')
        direction   = self.request.get('direction')
        
        # if it doesn't, create a new one
        s = StopLocation()
        stop_template = s
        
        s.stopID = stopID
        s.intersection = name.split('(')[0].rstrip()
        s.direction = direction
        s.description = description
        s.location = GeoPt(lat,lon)
        s.update_location()
        stop_list.append(s)
                
        # put the new stop in the datastore
        db.put(stop_list)
        logging.info('done updating stop locations for stopID %s' % stopID)
        
        self.response.set_status(200)

## end PortStopTask


def main():
  logging.getLogger().setLevel(logging.DEBUG)
  application = webapp.WSGIApplication([('/gtfs/port/stops', PortStopsHandler),
                                        ('/gtfs/port/stop/task/', PortStopTask),
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()

