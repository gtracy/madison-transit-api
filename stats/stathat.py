import logging
import urllib
import urllib2
import webapp2 as webapp
from google.appengine.api import urlfetch
from google.appengine.api.labs.taskqueue import Task
from google.appengine.api import memcache

import config

STATHAT_MEMCACHE_ERROR_COUNT = 'stathat_error_count'
STATHAT_MEMCACHE_REQ_COUNT = 'stathat_req_count'

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
    memcache.incr(STATHAT_MEMCACHE_REQ_COUNT, 1, None, 0)
    #task = Task(url='/stats/new/count', params={'stat_key':config.STATHAT_API_COUNT_STAT_KEY})
    #task.add('stats')


def apiErrorCount():
    memcache.incr(STATHAT_MEMCACHE_ERROR_COUNT, 1, None, 0)
    #task = Task(url='/stats/new/count', params={'stat_key':config.STATHAT_API_ERROR_STAT_KEY})
    #task.add('stats')

def apiTimeStat(stat_key,value):
    task = Task(url='/stats/new/value', params={'stat_key':stat_key,'value':value})
    task.add('stats')

def noop():
    logging.debug('noop called')
## end


class StatValueTaskHandler(webapp.RequestHandler):

  def post(self):
    stat_key = self.request.get('stat_key')
    value = self.request.get('value')

    stathat = StatHat()
    stathat.post_value(config.STATHAT_USER_KEY,stat_key,value,callback=noop)

## end StatValueTaskHandler

class StatFlushHandler(webapp.RequestHandler):

    def get(self):
        stathat = StatHat()

        errors = memcache.get(STATHAT_MEMCACHE_ERROR_COUNT)
        if errors is not None:
            stathat.post_count(config.STATHAT_USER_KEY,config.STATHAT_API_ERROR_STAT_KEY,errors,callback=noop)
            memcache.decr(STATHAT_MEMCACHE_ERROR_COUNT, errors)

        req_count = memcache.get(STATHAT_MEMCACHE_REQ_COUNT)
        if req_count is not None:
            stathat.post_count(config.STATHAT_USER_KEY,config.STATHAT_API_COUNT_STAT_KEY,req_count,callback=noop)
            memcache.decr(STATHAT_MEMCACHE_REQ_COUNT, req_count)

## end StatFlushHandler


application = webapp.WSGIApplication([('/stats/new/value', StatValueTaskHandler),
                                      ('/stats/flush', StatFlushHandler)
                                      ],
                                     debug=True)

def main():
  logging.getLogger().setLevel(logging.ERROR)
  run_wsgi_app(application)

if __name__ == '__main__':
  main()

