import logging

from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import quota
from google.appengine.api.urlfetch import DownloadError

from google.appengine.ext import db

from BeautifulSoup import BeautifulSoup, Tag
from data_model import RouteListing
from data_model import BusStopAggregation

from api.v1 import api_utils
import config

# our local cache hashed by SID for each request
aggregated_results = {}


def clean(sid):
    logging.debug('cleaning request sid: %s' % sid)
    del aggregated_results[sid]
## end

def cleanAll():
    logging.debug('cleaning the aggregated results list. total of %s sids' % str(len(aggregated_results)))
    for key,value in aggregated_results.items():
        logging.debug('... BULK clean %s' % key);
        del aggregated_results[key]
    logging.debug('done with the clean... %s' % aggregated_results)
## end

def email_missing_stop(stopID, routeID, sid):
      # setup the response email
      message = mail.EmailMessage()
      message.sender = config.EMAIL_SENDER_ADDRESS
      message.to = config.EMAIL_REPORT_ADDRESS
      message.subject = 'Missing stop ID requested by API client - %s' % stopID
      message.body = 'RouteID: %s \n' % routeID + 'SID: %s \n' % sid
      message.send()
## end

def aggregateBusesAsynch(sid, stopID, routeID=None):
    if len(stopID) == 3:
        stopID = "0" + stopID
    elif len(stopID) == 2:
        stopID = "00" + stopID
    elif len(stopID) == 1:
        stopID = "000" + stopID
        
    routes = getRouteListing(stopID,routeID)
    if len(routes) == 0:
        # this can happen if the user passes in a bogus stopID
        logging.error("API: User error. There are no matching stops for this ID?!? %s" % stopID)
        if stopID not in config.INVALID_STOP_IDS:
            email_missing_stop(stopID,routeID,sid)
        return None
    else:
        aggregated_results[sid] = []
        logging.debug('Stop aggregation start %s '%sid)
        logging.debug(aggregated_results)
        # create a bunch of asynchronous url fetches to get all of the route data
        rpcs = []
        memcache.set(sid,0)
        for r in routes:
            rpc = urlfetch.create_rpc()
            rpc.callback = create_callback(rpc,stopID,r.route,sid,r.direction)
            counter = memcache.incr(sid)
            urlfetch.make_fetch_call(rpc, r.scheduleURL)
            rpcs.append(rpc)
            
        # all of the schedule URLs have been fetched. now wait for them to finish
        for rpc in rpcs:
            rpc.wait()
        
        # all calls should be complete at this point    
        while memcache.get(sid) > 0 :
            logging.info('API: ERROR : uh-oh. in waiting loop... %s' % memcache.get(sid))
            rpc.wait()
            
        return aggregateAsynchResults(sid)
    

## end aggregateBusesAsynch()

#
# once all of the results have been grabbed, piece them together
#
def aggregateAsynchResults(sid):
    logging.info("API: Time to report back on results for %s..." % sid)
      
    try:
        if len(aggregated_results[sid]) == 0:
            logging.debug("We couldn't find results for transaction %s. Chances are there aren't any matches with the request." % sid)
            textBody = "Doesn't look good... Your bus isn't running right now!"
    except KeyError as e:
        logging.error('aggregation error: %s' % e.message)
        logging.debug(aggregated_results)

    return aggregated_results[sid]
  
## end aggregatAsynchResults()

#
# This function handles the callback of a single fetch request.
# If all requests for this sid are services, aggregate the results
#
def handle_result(rpc,stopID,routeID,sid,directionID):
    routes = None
    result = None
    try:
        # go fetch the webpage for this route/stop!
        result = rpc.get_result()
        done = True;
    except urlfetch.DownloadError:
         api_utils.apiErrorCount()
         logging.error("API: Error loading page. route %s, stop %s" % (routeID,stopID))
         if result:
            logging.error("API: Error status: %s" % result.status_code)
            logging.error("API: Error header: %s" % result.headers)
            logging.error("API: Error content: %s" % result.content)
           
    directionLabel = api_utils.getDirectionLabel(directionID)       
    arrival = '0'
    textBody = 'unknown'
    valid = False
    if result is None or result.status_code != 200:
           logging.error("API: Exiting early: error fetching URL")
           if( result is not None ):
                logging.error("fetch error: %s" % result.status_code)
           textBody = "error " + routeID + " (missing data)"
    else:
           soup = BeautifulSoup(result.content)
           for slot in soup.html.body.findAll("a","ada"):
              # only take the first time entry
              if slot['title'].split(':')[0].isdigit():
                arrival = slot['title']
                textBody = arrival.replace('P.M.','pm').replace('A.M.','am')
                valid = True

                # the next column includes very specific details about
                # where the route is going. some buses take multiple 
                # routes to a destination point. that detail is here
                direction = slot.parent.nextSibling.string.strip().lower().title()
                # contort this string to minimize it
                # ... strip off the "To" on the front end
                direction = direction.replace('To ','',1).strip()
                # ... correct the transfer point acronym we broke in the title() call above
                direction = direction.replace('Tp','TP')
                
                # the original implementaiton leveraged the datastore to store and
                # ultimately sort the results when we got all of the routes back.
                # we'll continute to use the model definition, but never actually store
                # the results in the datastore.
                stop = BusStopAggregation()
                stop.stopID = stopID
                stop.routeID = routeID
                stop.sid = sid
                stop.arrivalTime = textBody
                stop.destination = direction
          
                # turn the arrival time into absolute minutes
                hours = int(arrival.split(':')[0])
                if arrival.find('P.M.') > 0 and int(hours) < 12:
                    hours += 12
                minutes = int(arrival.split(':')[1].split()[0])
                arrivalMinutes = (hours * 60) + minutes
                stop.time = arrivalMinutes
          
                stop.text = "%s %s" % (textBody,direction)
                #stop.text = textBody + " toward %s" % directionLabel
                
                # instead of shoving this in the datastore, we're going to shove
                # it in a local variable and retrieve it with the sid later
                # old implementation --> stop.put()
                insert_result(sid,stop)

    # create the task that glues all the messages together when 
    # we've finished the fetch tasks
    counter = memcache.decr(sid)
    if counter == 0:
        # put them all together
        memcache.delete(sid)
        #routes = aggregateAsynchResults(sid)
        
    return routes

## end

# insert a BusAggregation result into the results array for this SID
# we'll scan the current list and insert it into the array based
# on the time-to-arrival
#
def insert_result(sid,stop):
    try:
        if len(aggregated_results[sid]) == 0:
            aggregated_results[sid] = [stop]
        else:
            done = False
            for i, s in enumerate(aggregated_results[sid]):
                if stop.time <= s.time:
                        aggregated_results[sid].insert(i,stop)
                        done = True
                        break
            if not done:
                aggregated_results[sid].append(stop)
    except KeyError as e:
        logging.error('aggregation error: %s' % e.message)


            
## end

# Use a helper function to define the scope of the callback.
def create_callback(rpc,stopID,routeID,sid,directionID):
    return lambda: handle_result(rpc,stopID,routeID,sid,directionID)
    
# Convenience method to extract RouteListing
def getRouteListing(stopID,routeID=None):
    
    # ignore the invalid stop IDs that keep coming in
    if stopID in config.INVALID_STOP_IDS:
        return []
        
        
    if routeID is None:
        key = 'routelisting:%s' % stopID
    else:
        key = 'routelisting:%s:%s' % (stopID,routeID)
    
    entities = api_utils.deserialize_entities(memcache.get(key))
    if not entities:
        if routeID is None:
            entities = db.GqlQuery("SELECT * FROM RouteListing WHERE stopID = :1",stopID).fetch(50)
        else:
            entities = db.GqlQuery("SELECT * FROM RouteListing WHERE stopID = :1 AND route = :2",stopID,routeID).fetch(50)
        if entities:
            memcache.set(key, api_utils.serialize_entities(entities))
        
    return entities

## end

