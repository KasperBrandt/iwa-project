import cgi, datetime, wsgiref.handlers, os
from datetime import date

import util, lastfm, songkick

from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


from xml.etree import ElementTree as etree

class MainPage(webapp.RequestHandler):
    
    def get(self):
        buildLogin(self)

    def post(self):
        username = self.request.get("username")
        dateStart = self.request.get("datepickerStart")
        dateEnd = self.request.get("datepickerEnd")
        city = self.request.get("city")

        date1 = util.convertToDate(dateStart)
        date2 = util.convertToDate(dateEnd)

        if date1 > date2:
            # Need better error handling
            print "Incorrect dates, make sure the end date lies after the start date."

        nrOfArtists = 500
        artists = lastfm.getUserArtists(username, nrOfArtists)

        locationId = songkick.getLocationId(city)

        events = songkick.getEvents(date1, date2, locationId)

        matchingEvents = matchEvents(artists, events)

        eventNames = []
        index = 0
        for concert in events:
            eventNames.insert(index, concert[2])
            index += 1

        matchingEventNames = []
        index2 = 0
        for match in matchingEvents:
            matchingEventNames.insert(index2, match[2])
            index2 += 1

        template_values = {
            'username': username,
            'artists': artists,
            'eventNames': eventNames,
            'matches': matchingEventNames,
        }

        path = os.path.join(os.path.dirname(__file__), "website.html")
        self.response.out.write(template.render(path, template_values))

def buildLogin(self):
    template_values = {
    }

    path = os.path.join(os.path.dirname(__file__), "index.html")
    self.response.out.write(template.render(path, template_values))


def matchEvents(artists,events):

    result = []
    index = 0

    for concert in events:
        if artists.count(concert[2]) > 0:
            result.insert(index,concert)
            index += 1

    return result

application = webapp.WSGIApplication([('/', MainPage)], debug=True)

def main():

    run_wsgi_app(application)

if __name__ == "__main__":
    main()
