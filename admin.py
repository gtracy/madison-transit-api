import os
import wsgiref.handlers
import logging
import webapp2 as webapp
import json

from operator import itemgetter
from datetime import datetime
from datetime import date
from datetime import timedelta

from google.appengine.api import channel
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api.labs.taskqueue import Task
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from google.appengine.runtime import apiproxy_errors

import gdata.docs.service
import gdata.spreadsheet.service
import gdata.spreadsheet.text_db

import config

from data_model import DeveloperKeys



#
# Every so often persist the API counters to the datastore
#
class PersistCounterHandler(webapp.RequestHandler):
  def get(self):
    logging.debug('persisting API counters to the datastore')
    devkeys_to_save = []
    devkeys = db.GqlQuery("SELECT * FROM DeveloperKeys").fetch(100)
    for dk in devkeys:
        counter_key = dk.developerKey + ':counter'
        count = memcache.get(counter_key)
        if count is not None:
            logging.debug('persisting %s at %s' % (counter_key,str(count)))
            dk.requestCounter += int(count)
            memcache.set(counter_key,0)
            devkeys_to_save.append(dk)

    if len(devkeys_to_save) > 0:
        db.put(devkeys_to_save)

    logging.debug('... done persisting %s counters' % str(len(devkeys_to_save)))

## end

#
# Daily reporting email
#
class DailyReportHandler(webapp.RequestHandler):

    def get(self):
      devkeys_to_save = []
      msg_body = '\n'

      # right now we're only reporting on the API counters
      devkeys = db.GqlQuery("SELECT * FROM DeveloperKeys").fetch(100)
      for dk in devkeys:
          msg_body += dk.developerName + '(%s) :  ' % dk.developerKey
          msg_body += str(dk.requestCounter)
          msg_body += '\n'

          # post counter to google doc
          updateField(dk.developerKey,dk.requestCounter)

          # reset the daily counter
          if dk.requestCounter > 0:
            dk.requestCounter = 0
            devkeys_to_save.append(dk)

      # save the modified developer keys
      if len(devkeys_to_save) > 0:
          db.put(devkeys_to_save)

## end

class GDocHandler(webapp.RequestHandler):

    def get(self):
      devkeys = db.GqlQuery("SELECT * FROM DeveloperKeys").fetch(100)
      for dk in devkeys:
          logging.debug('updating gdoc for %s with %s' % (dk.developerKey,str(dk.requestCounter)))
          updateField(dk.developerKey,dk.requestCounter)
## end

class ResetChannelsHandler(webapp.RequestHandler):
  def get(self):
    now = datetime.now()
    channels = json.loads(memcache.get('channels') or '{}')
    for channel_id, created in channels.items():

        dt = datetime.strptime(created.split(".")[0], "%Y-%m-%d %H:%M:%S")

        # NOTE: normally this would be 60 minutes; set it lower to expose the refresh behavior
        if (now - dt) > timedelta(minutes=1):
            del channels[channel_id]
            channel.send_message(channel_id, json.dumps({'function':'reload'}))

    if channels:
        memcache.set('channels', json.dumps(channels))
        logging.debug('channels not empty')
    else:
        memcache.delete('channels')
        logging.debug('empty. delete it.')

## end

def updateField(category,value):
    member = 'Sheet1'
    # get a connection to the db/spreadsheet
    client = gdata.spreadsheet.text_db.DatabaseClient(config.GOOGLE_DOC_EMAIL,config.GOOGLE_DOC_PASSWORD)

    today = date.today() + timedelta(hours=-6)
    dateString = str(today.month)+ "/" + str(today.day) + "/" + str(today.year)
    logging.info('adding %s to %s for %s on %s' % (value,category,member,dateString))

    databases = client.GetDatabases(config.GOOGLE_DOC_KEY,
                                    config.GOOGLE_DOC_TITLE)
    if len(databases) != 1:
        logging.error("database query is broken!?! can't find the document")
    for db in databases:
        tables = db.GetTables(name=member)
        for t in tables:
            if t:
                records = t.FindRecords('date == %s' % dateString)
                for r in records:
                    if r:
                        if category not in r.content:
                            logging.error('could not find %s - 0' % category)
                        else:
                            r.content[category] = str(value)
                            r.Push()

                    else:
                        logging.error("unable to find the contents for this record!?!")
            else:
                logging.error("couldn't find the table!?!")
    return

## end

class CreateDeveloperKeysHandler(webapp.RequestHandler):
    def get(self):
      key = DeveloperKeys()
      key.developerName = 'Prog Mamer'
      key.developerKey = 'fixme'
      key.developerEmail = 'fixme@gmail.com'
      key.requestCounter = 0
      key.errorCounter = 0
      key.put()

## end

class APIUserDumpHandler(webapp.RequestHandler):
    def get(self):
        devs = db.GqlQuery("SELECT * FROM DeveloperKeys").fetch(limit=None)
        template_values = {
            'devs' : devs
        }
        path = os.path.join(os.path.dirname(__file__), 'views/devlist.html')
        self.response.out.write(template.render(path,template_values))




application = webapp.WSGIApplication([('/admin/persistcounters', PersistCounterHandler),
                                      ('/admin/dailyreport', DailyReportHandler),
                                      ('/admin/gdoctest', GDocHandler),
                                      ('/admin/resetchannels', ResetChannelsHandler),
                                      ('/admin/apidump', APIUserDumpHandler),
                                      ('/admin/api/create', CreateDeveloperKeysHandler)
                                      ],
                                     debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
