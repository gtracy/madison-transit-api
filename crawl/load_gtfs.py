import logging

from google.appengine.api.taskqueue import Task
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.db import GeoPt
from google.appengine.ext.db import TransactionFailedError
from google.appengine.ext.db import Timeout
from google.appengine.runtime import DeadlineExceededError

from data_model import StopLocation
from data_model import StopLocationLoader
from data_model import RouteListing
from data_model import RouteListingLoader
from data_model import DestinationListing

CRAWL_URLBASE = "http://webwatch.cityofmadison.com/tmwebwatch/LiveADADepartureTimes"

#
# a collection of handlers that will transform RouteListingLoader entities
# into routes and destinations
#
# note that order matters. the Stop transformation has to happen first.
#
class RouteTransformationStart(webapp.RequestHandler):
    def get(self) :
        # shove a task in the queue because we need more time then
        # we may be able to get in the browser
        for route in range(1, 100):
            task = Task(url="/gtfs/port/routes/task",params={'route':route})
            task.add('crawler')
        self.response.out.write('done. spawned a task to go do the route transformations')

## end RouteTransformationStart

class RouteTransformationTask(webapp.RequestHandler):
    def post(self):
        try:
            routeID = self.request.get('route')
            if len(routeID) == 1:
                routeID = '0' + routeID

            q = RouteListingLoader.all()
            q.filter("routeID = ", routeID)
            for r in q.run(keys_only=True):
                logging.debug('launch key query %s', r)
                task = Task(url="/gtfs/port/routes/transform/task",params={'rll_key':r})
                task.add('crawler')
            self.response.set_status(200)

        except Timeout:
            logging.error('FAIL : timeout getting the route loader tasks spawned')
            self.response.set_status(200)
            self.response.out.write("timeout")

        return

## end RouteTransformationParent

class RouteTransformationChildTask(webapp.RequestHandler):
    def post(self):
        route_loader_key = self.request.get('rll_key')
        logging.debug('work on %s' % self.request.get('rll_key'))
        route_loader = RouteListingLoader.get(route_loader_key)
        if route_loader is None:
            logging.error('total fail. unable to find %s' % route_loader_key)
        else:
            logging.debug(route_loader.routeID)
            # find the corresponding stop details
            stop = db.GqlQuery("SELECT * FROM StopLocation WHERE stopID = :1", route_loader.stopID).get()
            if stop is None:
              logging.error("Missing stop %s which should be impossible",route_loader.stopID);

            try:
                url = CRAWL_URLBASE + '?r=' + route_loader.routeCode + '&d=' + route_loader.directionCode + '&s=' + route_loader.stopCode
                logging.debug(url)
                route = RouteListing()
                route.route = route_loader.routeID
                route.routeCode = route_loader.routeCode
                route.direction = route_loader.directionCode
                route.stopID = route_loader.stopID
                route.stopCode = route_loader.stopCode
                route.scheduleURL = url
                route.stopLocation = stop
                route.put()
                logging.info("added new route listing entry to the database!")

                DestinationListing.get_or_insert(route_loader.direction, id=route_loader.directionCode, label=route_loader.direction)
            except TransactionFailedError:
                logging.error('FAIL : unable to store RouteListing for route %s, stop %s', (route_loader.routeID,route_loader.stopID))
                self.response.set_status(2)
                self.response.out.write('transaction fail')

        return

## end RouteTransformationChild

#
# This handler is designed to port the GTFS Stops loaded via the bulk loader
# It simply creates a number of background tasks to do the grunt work
#
class PortStopsHandler(webapp.RequestHandler):
    def get(self):

        # query the StopLocationLoader for all stops
        stops = StopLocationLoader.all()
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

        logging.debug('Finished spawning StopLocationLoader tasks!')
        self.response.out.write('done spawning porting tasks!')

## end PortStopsHandler

#
# This handler is the task handler for porting an individual GTFS stop
#
class PortStopTask(webapp.RequestHandler):
    def post(self):
        stop_list = []

        stopID = self.request.get('stopID')
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

        s = StopLocation()
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


application = webapp.WSGIApplication([('/gtfs/port/stops', PortStopsHandler),
                                      ('/gtfs/port/stop/task/', PortStopTask),
                                      ('/gtfs/port/routes', RouteTransformationStart),
                                      ('/gtfs/port/routes/task', RouteTransformationTask),
                                      ('/gtfs/port/routes/transform/task', RouteTransformationChildTask)
                                     ],
                                     debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()

