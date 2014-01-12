import logging
import urllib
import urllib2
import webapp2 as webapp
from google.appengine.api import urlfetch
from google.appengine.api.labs.taskqueue import Task

import config


class StatHat:

        URL_BASE = 'http://api.stathat.com'

        def http_post_async(self, path, data):
            pdata = urllib.urlencode(data)

            rpc = urlfetch.create_rpc()
            urlfetch.make_fetch_call(
                rpc, 
                url=self.URL_BASE+path,
                payload=pdata,
                method='POST'
            )
            return({'status':'async'})

        def http_post(self, path, data):
            pdata = urllib.urlencode(data)
            req = urllib2.Request(self.URL_BASE + path, pdata)
            resp = urllib2.urlopen(req)
            return resp.read()

        def post_value(self, user_key, stat_key, value, callback=None):
            if( callback is None ):
                return self.http_post_async('/v', {'key': stat_key, 'ukey': user_key, 'value': value})
            else: 
                return self.http_post('/v', {'key': stat_key, 'ukey': user_key, 'value': value})

        def post_count(self, user_key, stat_key, count, callback=None):
            if( callback is None ):
                return self.http_post('/c', {'key': stat_key, 'ukey': user_key, 'count': count})
            else: 
                return self.http_post_async('/c', {'key': stat_key, 'ukey': user_key, 'count': count})

        def ez_post_value(self, ezkey, stat_name, value):
                return self.http_post('/ez', {'ezkey': ezkey, 'stat': stat_name, 'value': value})

        def ez_post_count(self, ezkey, stat_name, count):
                return self.http_post('/ez', {'ezkey': ezkey, 'stat': stat_name, 'count': count})


def apiStatCount():
    task = Task(url='/stats/new/count', params={'stat_key':config.STATHAT_API_COUNT_STAT_KEY})
    task.add('stats')

def apiErrorCount():
    task = Task(url='/stats/new/count', params={'stat_key':config.STATHAT_API_ERROR_STAT_KEY})
    task.add('stats')

def apiTimeStat(stat_key,value):
    task = Task(url='/stats/new/value', params={'stat_key':stat_key,'value':value})
    task.add('stats')

def noop():
    logging.debug('noop called')
## end

class StatCountTaskHandler(webapp.RequestHandler):

  def post(self):
    stat_key = self.request.get('stat_key')

    stathat = StatHat()
    stathat.post_count(config.STATHAT_USER_KEY,stat_key,1,callback=noop)

## end StatCountTaskHandler

class StatValueTaskHandler(webapp.RequestHandler):

  def post(self):
    stat_key = self.request.get('stat_key')
    value = self.request.get('value')

    stathat = StatHat()
    stathat.post_value(config.STATHAT_USER_KEY,stat_key,value,callback=noop)

## end StatValueTaskHandler


application = webapp.WSGIApplication([('/stats/new/count', StatCountTaskHandler),
                                      ('/stats/new/value', StatValueTaskHandler)
                                      ],
                                     debug=True)

def main():
  logging.getLogger().setLevel(logging.ERROR)
  run_wsgi_app(application)

if __name__ == '__main__':
  main()

