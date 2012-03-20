import cgi, datetime, wsgiref.handlers, os, random
from datetime import date

from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch

from xml.etree import ElementTree as etree

class MainPage(webapp.RequestHandler):
    
    def get(self):
        buildLogin(self)

    def post(self):
        username = self.request.get("username")
        dateStart = self.request.get("datepickerStart")
        dateEnd = self.request.get("datepickerEnd")
        city = self.request.get("city")

        date1 = convertToDate(dateStart)
        date2 = convertToDate(dateEnd)

        if date1 > date2:
            # Need better error handling
            print "Incorrect dates, make sure the end date lies after the start date."

        nrOfArtists = 500
        artists = getLastfmArtists(username, nrOfArtists)

        location = getLocation(city)

        locationInformation = getLocInfo(location[1],location[2])

        events = getEvents(date1, date2, location[0])

        matchingEvents = matchEvents(artists, events)

        eventNames = []
        index = 0
        for concert in events:
            eventNames.insert(index, concert[2])
            index += 1

        locationNames = []
        index2 = 0
        for location in locationInformation:
            locationNames.insert(index2, location[0])
            index2 += 1

        template_values = {
            'username': username,
            'artists': artists,
            'eventNames': eventNames,
            'locations': locationNames,
        }

        path = os.path.join(os.path.dirname(__file__), "website.html")
        self.response.out.write(template.render(path, template_values))

def buildLogin(self):
    template_values = {
    }

    path = os.path.join(os.path.dirname(__file__), "index.html")
    self.response.out.write(template.render(path, template_values))

def convertToDate(dateOld):
    dateArr = dateOld.split('/')
    dateNew = date(int(dateArr[2]),int(dateArr[0]),int(dateArr[1]))
    return dateNew

def getLastfmArtists(username, nrOfArtists):

    api_key = "7e6d32dffbf677fc4f766168fd5dc30e"
    #secret = "5856a08bb3d5154359f22daa1a1c732b"

    url = "http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user=" + username + "&limit=" + str(nrOfArtists) + "&api_key=" + api_key

    artistsXML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)

    artists = []

    if artistsXML.status_code == 200:

        tree = etree.fromstring(artistsXML.content)

        for artist in tree.findall('topartists/artist'):
            rank = artist.attrib['rank']
            name = artist.find('name')
            artists.insert(int(rank), name.text)

    else:
        # Need better error handling
        print "Last FM User does not exist or something else went wrong with the connection to the Last FM server."

    return artists

def getLocation(city):

    api_key = "wV3l1uxVevrxnA6e"

    city.replace(" ","%20")

    url = "http://api.songkick.com/api/3.0/search/locations.xml?query=" + city + "&apikey=" + api_key

    locationXML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)

    if locationXML.status_code == 200:
        location = []

        tree = etree.fromstring(locationXML.content)
        locationId = tree.find('results/location/metroArea').attrib['id']
        locationLat = tree.find('results/location/metroArea').attrib['lat']
        locationLong = tree.find('results/location/metroArea').attrib['lng']

        location.insert(0, locationId)
        location.insert(1, locationLat)
        location.insert(2, locationLong)

        return location

    else:
        # Need better error handling
        print "Location does not exist or something else went wrong with the connection to the Songkick server."

def getLocInfo(lat,long):

    results = []
    index = 0

    api_key = "AIzaSyDva2nYRJnjiQ-BW-I67_5m7GxA_19gA7Y"

    url = "https://maps.googleapis.com/maps/api/place/search/xml?location="+lat+","+long+"&radius=10000&types=amusement_park|museum|shopping_mall|zoo|point_of_interest&sensor=false&key=" + api_key

    poiXML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)

    if poiXML.status_code == 200:

        tree = etree.fromstring(poiXML.content)

        for poi in tree.findall('result'):
            place = []

            try:
                poiName = poi.find('name').text
                poiIcon = poi.find('icon').text

                place.insert(0, poiName)
                place.insert(1, poiIcon)

                results.insert(index,place)
                index += 1

            except AttributeError:
                print ""

        return results

    else:
        print "Something went wrong with the connection to the Google Places server"

def getEvents(startDate, endDate, locId):

    api_key = "wV3l1uxVevrxnA6e"

    url = "http://api.songkick.com/api/3.0/metro_areas/" + locId +"/calendar.xml?apikey=" + api_key

    events = []

    pages = getPages(url)
    page = 1

    while(page <= pages):
        urlPage = url + "&page=" + str(page)

        pageEvents = getEventsOnPage(startDate, endDate, urlPage)
        events.extend(pageEvents)

        page += 1

    return events

def getPages(url):
    eventXML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)

    if eventXML.status_code == 200:

        tree = etree.fromstring(eventXML.content)
        totalEvents = tree.attrib['totalEntries']

    else:
        # Need better error handling
        print "Event lookup failed or something else went wrong with the connection to the Songkick server."

    pages = int(totalEvents) / 50

    return pages

def getEventsOnPage(startDate, endDate, url):
    eventXML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)

    events = []
    eventIndex = 0

    if eventXML.status_code == 200:

        tree = etree.fromstring(eventXML.content)

        for event in tree.findall('results/event'):

            conDate = event.find('start').attrib['date']
            conDateArr = conDate.split('-')
            concertDate = date(int(conDateArr[0]), int(conDateArr[1]), int(conDateArr[2]))

            if concertDate >= startDate and concertDate <= endDate:

                concert = []
                try:
                    concert.insert(0, str(concertDate))
                    concert.insert(1, event.attrib['displayName'])
                    concert.insert(2, event.find('performance/artist').attrib['displayName'])
                    concert.insert(3, event.find('venue').attrib['displayName'])
                except AttributeError:
                    concert.insert(0, "")
                    concert.insert(1, "")
                    concert.insert(2, "")
                    concert.insert(3, "")
                events.insert(eventIndex, concert)

                eventIndex += 1

        return events

    else:
        # Need better error handling
        print "Event per page lookup failed or something else went wrong with the connection to the Songkick server."

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