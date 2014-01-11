import jinja2
import os
import webapp2
import logging
import uuid
import json
import random

from datetime import datetime

from data_model import StopLocation

from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.api import memcache 
from google.appengine.ext import db


class MapPage(webapp2.RequestHandler):

  def get(self):
    channel_id = uuid.uuid4().hex
    token = channel.create_channel(channel_id)

    # shove the new channel id into memcache so we can update this new browser session
    channels = json.loads(memcache.get('channels') or '{}')
    channels[channel_id] = str(datetime.now())
    memcache.set('channels', json.dumps(channels))

    template_values = {'token': token}
    template = jinja_environment.get_template('livemap.html')
    self.response.out.write(template.render(template_values))


class InboundChannelRequest(webapp2.RequestHandler):

  def post(self):
    logging.debug('received channel open')

class NewEventTaskRequest(webapp2.RequestHandler):

  def post(self):
    stopID = self.request.get('stopID')
    #apiKey = self.request.get('apiKey')

    # lookup location of stopID in memcache
    # if miss, lookup in datastore
    key = 'stopLocation:%s' % stopID
    stop = memcache.get(key)
    if stop is None:
        stop = db.GqlQuery('select * from StopLocation where stopID = :1', stopID).get()
        if stop is not None:
            #logging.debug('shoving stop %s entity into memcache' % stopID)
            memcache.set(key,stop)
        else:
            logging.debug('failed to lookup stop %s' % stopID)
            return

    message = {'function' : 'event',
               'lat' : stop.location.lat,
               'lng' : stop.location.lon}

    # lookup all active channels in memcache
    channels = json.loads(memcache.get('channels') or '{}')
    logging.debug('%s total channels open' % len(channels))
    
    # roll through all channels
    for channel_id in channels.iterkeys():
        encoded_message = json.dumps(message)
        channel.send_message(channel_id, encoded_message)

# end new event

class TestPokeRequest(webapp2.RequestHandler):

  def get(self):
    channels = json.loads(memcache.get('channels') or '{}')
    for channel_id in channels.iterkeys():
        channel.send_message(channel_id, json.dumps({'function':'reload'}))

# end test

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

app = webapp2.WSGIApplication([('/map', MapPage),
                               ('/map/channel', InboundChannelRequest),
                               ('/map/task', NewEventTaskRequest),
                               ('/map/poke', TestPokeRequest)
                              ],
                              debug=True)