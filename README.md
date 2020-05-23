Madison Transit API
========
This project is a civic hacking project that makes the Madison Metro bus system more accessible,
easier to use, and make the entire riding experience more enjoyable.

https://api.smsmybus.com

The app is currently deployed on Google App Engine.

This application provides access to a free, easy to use, JSON-based web service interface for
Madison Metro service. Once you've received a developer token, you have access to the following
services:

* Real-time arrival estimates for every route at every stop in the city.
* A list of all stops in a specified route
* The geo-location of any stop in the city
* Search for stops near a specified geo-location
* A list of all routes in the system

### API Resources

There is a second repository that contains some example uses of the API

https://github.com/gtracy/smsmybus-dev

There is a Google Group used for developer discussion

https://groups.google.com/group/smsmybus-dev

Running Your Own Instance
-------------------------

You can deploy your own instance for testing or for
running your own version of the API, either on the Google infrastructure
or locally using the Python SDK dev_appserver. Before deploying,
copy config.py-sample to config.py and customize the settings. If you are deploying
locally, not using the SMS features, and will not export statistics
to Google Docs, you may not need to change anything.

Deploy/run the application, and visit
https://baseurl/debug/create/newkey

You will likely need to log in at that time. If running locally,
be sure to click on 'Sign in as administrator' to create the key.

That will create your first developer key, 'fixme'. You can go to
the Datastore Viewer ( https://localhost:8080/_ah/admin/datastore )
and edit your new key.

Finally, you need to load route data. SMSMyBus crawls the Madison
Metro website to load route and stop data. There are detailed instructions [on the wiki](https://github.com/gtracy/madison-transit-api/wiki/Bootstrapping-the-database).

You should now be able to use the API as documented to fetch realtime
bus data, substituting your URL for api.smsmybus.com

GCP Deployment
---
The App Engine SDK is deprecated so you must use the command line tools. Here's a note for myself to remember the command. :)

`gcloud app deploy --project=msn-transit-api --version=FIXME --no-promote`

CRON only

`gcloud app deploy --project=msn-transit-api ./cron.yaml`