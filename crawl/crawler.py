import wsgiref.handlers
import logging
import re
import os
import webapp2 as webapp

from google.appengine.api import quota
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import datastore_errors
from google.appengine.api.urlfetch import DownloadError
from google.appengine.api.labs import taskqueue
from google.appengine.api.taskqueue import Task

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.db import GeoPt

from google.appengine.runtime import apiproxy_errors
from google.appengine.runtime import DeadlineExceededError
from api.BeautifulSoup import BeautifulSoup, Tag

from data_model import RouteListing
from data_model import StopLocation
from data_model import DestinationListing
from data_model import DeveloperKeys


CRAWL_URLBASE = "http://webwatch.cityofmadison.com/tmwebwatch/LiveADADepartureTimes"

# just kick off the crawler by sticking a task in the queue
# for the top-level arrival time page
#
class CrawlerStartHandler(webapp.RequestHandler):
    def get(self):
        loop = 0
        done = False
        while not done and loop < 3:
            try:
                # fetch the page
                result = urlfetch.fetch(CRAWL_URLBASE)
                done = True;
            except urlfetch.DownloadError:
                logging.info("Error loading page (%s)... sleeping" % loop)
                if result:
                    logging.debug("Error status: %s" % result.status_code)
                    logging.debug("Error header: %s" % result.headers)
                    logging.debug("Error content: %s" % result.content)
                    time.sleep(4)
                    loop = loop+1

        self.response.write(result.content)
        # roll through all of the links and create crawl tasks for them
        soup = BeautifulSoup(result.content)
        for slot in soup.html.body.findAll("a","adalink"):

            # sample HTML for each link
            #  <a class="adalink" title="01 - Route 1" href="?r=61">01 - Route 1</a>
            #
            # skip the supplemental listings
            #
            if slot['title'].find('Supplemental') == -1:
                href = slot['href']
                routeID = slot['title'].split(' ',1)[0]
                crawlURL = CRAWL_URLBASE + href
                logging.error("route %s, %s" % (routeID,crawlURL))
                task = Task(url='/crawl/routelist/crawlingtask', params={'crawl':crawlURL,'routeID':routeID})
                task.add('crawler')

        return

## end CrawlerStartHandler()

# task handler for all crawling jobs. this task handles two types of pages
#  1) intermediate page which has different direction for a single route
#  2) bottom page which lists all stops for a route direction
#
class CrawlingTaskHandler(webapp.RequestHandler):
    def post(self):
        try:
            scrapeURL = self.request.get('crawl')
            direction = self.request.get('direction')
            routeID = self.request.get('routeID')

            loop = 0
            done = False
            result = None
            while not done and loop < 3:
                try:
                    # fetch the page
                    result = urlfetch.fetch(scrapeURL)
                    done = True;
                except urlfetch.DownloadError:
                    logging.info("Error loading page (%s)... sleeping" % loop)
                    if result:
                        logging.debug("Error status: %s" % result.status_code)
                        logging.debug("Error header: %s" % result.headers)
                        logging.debug("Error content: %s" % result.content)
                        time.sleep(4)
                        loop = loop+1

            # start to interrogate the results
            soup = BeautifulSoup(result.content)
            for slot in soup.html.body.findAll("a","adalink"):

                if slot.has_key('href'):
                    href = slot['href']
                    title = slot['title']
                    logging.info("FOUND A TITLE ----> %s" % title)

                    # route crawler looks for titles with an ID# string
                    #
                    # stop links have the following format
                    #    <a class="adalink" title="CAMPUS &amp; BABCOCK RR [EB#0809]" href="?r=61&amp;d=102&amp;s=3457">CAMPUS &amp; BABCOCK RR [EB#0809]</a>
                    #
                    if title.find("#") > 0:
                        # we finally got down to the page we're looking for

                        # pull the stopID from the page content...
                        stopID = title.split("#")[1].split("]")[0]

                        # pull the intersection from the page content...
                        intersection = title.split("[")[0].strip()

                        logging.info("found stop %s, %s" % (stopID,intersection))

                        # check for conflicts...
                        stop = db.GqlQuery("SELECT * FROM StopLocation WHERE stopID = :1", stopID).get()
                        if stop is None:
                          logging.error("Missing stop %s which should be impossible" % stopID);

                        # pull the route and direction data from the URL
                        routeData = scrapeURL.split('?')[1]
                        logging.info("FOUND THE PAGE ---> arguments: %s stopID: %s" % (routeData,stopID))
                        routeArgs = routeData.split('&')
                        fakeRouteID = routeArgs[0].split('=')[1]
                        directionID = routeArgs[1].split('=')[1]
                        timeEstimatesURL = CRAWL_URLBASE + href

                        # check for conflicts...
                        r = db.GqlQuery("SELECT * FROM RouteListing WHERE route = :1 AND direction = :2 AND stopID = :3",
                                        routeID, directionID, stopID).get()
                        if r is None:
                          # add the new route to the DB
                          route = RouteListing()
                          route.route = routeID
                          route.direction = directionID
                          route.stopID = stopID
                          route.scheduleURL = timeEstimatesURL
                          route.stopLocation = stop
                          route.put()
                          logging.info("added new route listing entry to the database!")
                        else:
                          logging.error("we found a duplicate entry!?! %s", r.scheduleURL)
                    else:
                        # direction links look like the following,
                        #    <a class="adalink" title="CapSq" href="?r=61&amp;d=102">CapSq</a>
                        #
                        # fetch the next page depth to get to the stop details
                        #

                        if href.find("?r=") > -1:
                            # create a new task with this link
                            crawlURL = CRAWL_URLBASE + href
                            task = Task(url='/crawl/routelist/crawlingtask', params={'crawl':crawlURL,'direction':title,'routeID':routeID})
                            task.add('crawler')
                            logging.info("Added new task for %s, direction %s, route %s" % (title.split(",")[0],title,routeID))

                        # label crawler looks for titles with letters for extraction/persistence
                        if title.replace('-','').replace(' ','').isalpha():
                            directionID = href.split('d=')[0]
                            logging.info("found the route LABEL page! href: %s" % href)
                            l = DestinationListing.get_or_insert(title, id=directionID, label=title)

        except apiproxy_errors.DeadlineExceededError:
            logging.error("DeadlineExceededError exception!?")
            return

        return;

## end CrawlingTask()

class DropTableHandler(webapp.RequestHandler):
    def post(self, model=""):
        logging.debug('HEADS UP -> we have a request to drop the entities in the %s model' % model)
        self.get(model)

    def get(self, model=""):
        qstring = "select * from " + model
        logging.info("query string is... %s" % qstring)
        q = db.GqlQuery(qstring)
        results = q.fetch(500)
        logging.info('deleting %s' % str(q.count()))
        while results:
            logging.info('deleting %s' % str(q.count()))
            db.delete(results)
            results = q.fetch(500, len(results))

## end

class StartTableDrop(webapp.RequestHandler):
    def get(self,model=""):
        url = '/droptable/%s' % model
        logging.debug('getting ready to start task to drop the %s table' % model)
        task = Task(url=url, params={})
        task.add('crawler')
        self.response.out.write('got it. started the background task to delete all %s entities' % model)

class RouteListHandler(webapp.RequestHandler):
    def get(self,routeID=""):
      logging.info("fetching all stop locations for route %s" % routeID)
      q = db.GqlQuery("SELECT * FROM StopLocation WHERE routeID = :1", routeID)
      if q is not None:
          results = []

          # Perform the query to get 500 results.
          stops = q.fetch(500)
          logging.info("running through stop location list....")
          for s in stops:
              logging.debug("fetch route list details for stop %s" % s.stopID)
#              try:
#                  sLocation = s.stopLocation
#              except datastore_errors.Error,e:
#                  if e.args[0] == "ReferenceProperty failed to be resolved":
#                      sLocation = None
#                  else:
#                      raise

              results.append({'stopID':s.stopID,
                              #'location':sLocation if sLocation is not None else 'unknown',
                              'intersection':s.intersection,# if sLocation is not None else 'unknown',
                              'direction':s.direction,# if sLocation is not None else 'unknown',
                              'routeID':routeID,
                              })


      # add the counter to the template values
      template_values = {'stops':results}

      # create a page that provides a form for sending an SMS message
      path = os.path.join(os.path.dirname(__file__), 'stop.html')
      self.response.out.write(template.render(path,template_values))


## end

application = webapp.WSGIApplication([('/crawl/routelist/configure', CrawlerStartHandler),
                                        ('/crawl/routelist/crawlingtask', CrawlingTaskHandler),
                                        ('/routelist/(.*)', RouteListHandler),
                                        ('/droptable/(.*)', DropTableHandler),
                                        ('/debug/drop/(.*)', StartTableDrop)
                                        ],
                                       debug=True)

def main():
  logging.getLogger().setLevel(logging.INFO)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
