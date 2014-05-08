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
        city_lots = dict()
        # always include these headers
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.headers['Allow'] = 'GET'

        try:
            city_lots = CityParkingService().get_data()
            logging.debug('API: city_lots json response %s' % city_lots)
        except urlfetch.DownloadError:
            logging.error('Failed to retrieve city data')
            self.response.status = 500
            self.response.out.write(
                json.dumps(
                    api_utils.buildErrorResponse('-1', 'Failed to retrieve city data')
                )
            )
        except ValueError:
            logging.error('Failed to parse city html data')
            self.response.status = 500
            self.response.out.write(
                json.dumps(
                    api_utils.buildErrorResponse('-1', 'Failed to parse city html data')
                )
            )

        uw_lots = {}
        logging.debug('API: uw_lots json response %s' % uw_lots)

        #  encapsulate response in json or jsonp
        callback = self.request.get('callback')
        if callback is not '':
            self.response.headers['Content-Type'] = 'application/javascript'
            self.response.headers['Access-Control-Allow-Origin'] = '*'
            self.response.headers['Access-Control-Allow-Methods'] = 'GET'
            response = callback + '(' + json.dumps(city_lots) + ');'
        else:
            self.response.headers['Content-Type'] = 'application/json'
            response = json.dumps(city_lots)

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
