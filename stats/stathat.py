import urllib
import urllib2
from google.appengine.api import urlfetch

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
