import logging
import webapp2 as webapp
import json

from google.appengine.api import urlfetch
from google.appengine.ext.webapp.util import run_wsgi_app

from api.v2 import api_utils
from api.v2.parking.cityparking import CityParkingService
from api.v2.parking.campusparking import CampusParkingService
from stats import stathat


class ParkingHandler(webapp.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.headers['Allow'] = 'GET'
        self.response.status = 405  # method not allowed
        self.response.out.write(
            json.dumps(
                api_utils.buildErrorResponse('-1', 'The API does not support POST requests')
            )
        )

    def get(self):
        lot_results = {}

        # always include these headers
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.headers['Allow'] = 'GET'

        try:
            lot_results['cityLots'] = CityParkingService().get_data()
            logging.debug('API: city_lots json response %s' % lot_results)

        except (ValueError, urlfetch.DownloadError, AttributeError) as e:
            logging.error('Failed to retrieve city data', str(e))
            self.response.status = 500
            self.response.out.write(
                json.dumps(
                    api_utils.buildErrorResponse('-1',
                                                 'There was a problem retrieving the city parking data')
                )
            )

        try:
            lot_results['campusLots'] = CampusParkingService().get_data()
            logging.debug('API: campus lots added, json response %s' % lot_results)
        except (ValueError, urlfetch.DownloadError, AttributeError) as e:
            logging.error('Failed to retrieve campus data', str(e))
            self.response.status = 500
            self.response.out.write(
                json.dumps(
                    api_utils.buildErrorResponse('-1',
                                                 'There was a problem retrieving the campus parking data')
                )
            )

        #  encapsulate response in json or jsonp
        callback = self.request.get('callback')
        if callback is not '':
            self.response.headers['Content-Type'] = 'application/javascript'
            self.response.headers['Access-Control-Allow-Origin'] = '*'
            self.response.headers['Access-Control-Allow-Methods'] = 'GET'
            response = callback + '(' + json.dumps(lot_results) + ');'
        else:
            self.response.headers['Content-Type'] = 'application/json'
            response = json.dumps(lot_results)

        #stathat.apiStatCount()
        self.response.out.write(response)


## end MainHandler


application = webapp.WSGIApplication(
    [('/v2/parking', ParkingHandler), ], debug=True
)


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
