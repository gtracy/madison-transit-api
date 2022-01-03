import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch

#
# This handler is the task handler for sending a shadow API request
# to the new gtfs/node implementation
#
class ShadowAPITask(webapp.RequestHandler):
    def post(self):
        devKey = self.request.get('devKey')
        stopID = self.request.get('stopID')
        routeID = self.request.get('routeID');
        logging.info('shadow API request! %s - %s - %s' % (devKey,stopID,routeID))

        url = 'https://gtfs.smsmybus.com/v1/getarrivals?key=%s&stopID=%s' % (devKey,stopID)
        try:
            result = urlfetch.fetch(url)
            if result.status_code == 200:
                logging.info('successful shadow call')
                logging.info('%s' % result.content)
            else:
                logging.error('successful shadow FAILED')
                logging.error('fetch status: %s' % result.status_code)
                logging.info('%s' % result.content)
        except urlfetch.Error:
            logging.exception('Caught exception fetching url')
            
        self.response.set_status(200)



application = webapp.WSGIApplication([('/shadow/task', ShadowAPITask),
                                     ],
                                     debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()

