
# Songkick methods build specially for IWA (not a generic API).

from google.appengine.api import urlfetch
from xml.etree import ElementTree as etree
from datetime import date

def getLocationId(city):

    api_key = "wV3l1uxVevrxnA6e"

    city.replace(" ","%20")

    url = "http://api.songkick.com/api/3.0/search/locations.xml?query=" + city + "&apikey=" + api_key

    locationXML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)

    if locationXML.status_code == 200:

        tree = etree.fromstring(locationXML.content)
        locationId = tree.find('results/location/metroArea').attrib['id']
        return locationId

    else:
        # Need better error handling
        print "Location does not exist or something else went wrong with the connection to the Songkick server."

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
