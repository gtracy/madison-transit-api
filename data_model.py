from google.appengine.ext import db
from utils.geo.geomodel import GeoModel

# note that a stop extends GeoModel
class StopLocation(GeoModel):
    stopID       = db.StringProperty()
    intersection = db.StringProperty()
    direction    = db.StringProperty()
    description  = db.StringProperty(multiline=True)
## end StopLocation

# temporary storage model for the bulk uploader
class StopLocationLoader(db.Model):
    stopID       = db.StringProperty()
    name         = db.StringProperty()
    description  = db.StringProperty(multiline=True)
    lat          = db.FloatProperty()
    lon          = db.FloatProperty()
    direction    = db.StringProperty()
## end StopLocationLoader

class RouteListing(db.Model):
    route        = db.StringProperty()
    routeCode    = db.StringProperty()
    direction    = db.StringProperty()
    stopID       = db.StringProperty()
    stopCode     = db.StringProperty()
    scheduleURL  = db.StringProperty(indexed=False)
    stopLocation = db.ReferenceProperty(StopLocation,collection_name="stops")
## end RouteListing

class RouteListingLoader(db.Model):
    routeID       = db.StringProperty()
    routeCode     = db.StringProperty()
    direction     = db.StringProperty()
    directionCode = db.StringProperty()
    stopID        = db.StringProperty()
    stopCode      = db.StringProperty()
## end RouteListingLoader


class DestinationListing(db.Model):
    id    = db.StringProperty()
    label = db.StringProperty()
## end DestinationListing

class DeveloperKeys(db.Model):
    dateAdded      = db.DateTimeProperty(auto_now_add=True)
    developerName  = db.StringProperty()
    developerKey   = db.StringProperty()
    developerEmail = db.EmailProperty()
    requestCounter = db.IntegerProperty()
    errorCounter   = db.IntegerProperty()
## end DeveloperKeys

class DeveloperRequest(db.Model):
    developer     = db.ReferenceProperty()
    date          = db.DateTimeProperty(auto_now_add=True)
    type          = db.StringProperty()
    error         = db.StringProperty()
    requestTerms  = db.StringProperty()
    remoteAddr    = db.StringProperty()
## end DeveloperRequest

class ParseErrors(db.Model):
    dateAdded = db.DateTimeProperty(auto_now_add=True)
    intersection = db.StringProperty()
    location = db.GeoPtProperty()
    direction = db.StringProperty()
    routeID = db.StringProperty()
    stopID = db.StringProperty()
    metaStringOne = db.TextProperty()
    metaStringTwo = db.TextProperty()
    reviewed = db.BooleanProperty()
## end ParseErrors

class BusStopAggregation(db.Model):
    dateAdded   = db.DateTimeProperty(auto_now_add=True)
    routeID     = db.StringProperty(indexed=False)
    stopID      = db.StringProperty(indexed=False)
    destination = db.StringProperty(indexed=False)
    arrivalTime = db.StringProperty(indexed=False)
    time        = db.IntegerProperty()
    text        = db.StringProperty(multiline=True,indexed=False)
    sid         = db.StringProperty()
## end BusStopAggregation

class StopStat(db.Model):
    dateAdded   = db.DateTimeProperty(auto_now_add=True)
    stopID      = db.StringProperty()
    apiKey      = db.StringProperty()
## end StopStat