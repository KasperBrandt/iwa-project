import cgi, datetime, wsgiref.handlers, os, random, urllib, urllib2, sys
from datetime import date

from operator import itemgetter

from django.utils import simplejson as json

from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch

from xml.etree import ElementTree as etree

from rdflib.graph import ConjunctiveGraph
from rdflib.term import URIRef, Literal
from rdflib.namespace import Namespace, RDF, RDFS, XSD

rdfStoreUrl = 'http://ec2-46-51-144-109.eu-west-1.compute.amazonaws.com:8080/openrdf-sesame/repositories/iwaproj'

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
            sys.exit()

        nrOfArtists = 100
        artists = getLastfmArtists(username, nrOfArtists)

        nrOfGenres = 5
        topArtists = 3
        genres = getGenres(artists, nrOfGenres, topArtists)

        location = getLocation(city)

        locationInformation = getLocInfo(location[1],location[2])

        events = getEvents(date1, date2, location[0])

        graph = createRDF(username, city, artists, locationInformation, events, genres)

        storeRDF(graph)

        matchingEventsAllDates = matchEvents(username, city)
        recEventsAllDates = getRecommendations(username, city)

        matchingEvents = filterDates(matchingEventsAllDates,date1,date2)
        recEvents = filterDates(matchingEventsAllDates,date1,date2)

        template_values = {
            'events': matchingEvents,
            'recEvents': recEvents,
            'username': username,
            'city': city,
            'cityInfo': locationInformation[0:15],
            'genres': genres,
            'artists': artists[0:15]
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

def filterDates(events,start,end):

    results = []
    eventIndex = 0

    for event in events:
        dateArr = event[1].split('-')
        dateEvent = date(int(dateArr[0]),int(dateArr[1]),int(dateArr[2]))

        if dateEvent >= start and dateEvent <= end:
            results.insert(eventIndex,event)
            eventIndex += 1

    return results

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
        sys.exit()

    return artists

def getLocation(city):

    api_key = "wV3l1uxVevrxnA6e"

    city.replace(" ","%20")

    url = "http://api.songkick.com/api/3.0/search/locations.xml?query=" + city + "&apikey=" + api_key

    locationXML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)

    if locationXML.status_code == 200:
        location = []

        tree = etree.fromstring(locationXML.content)

        location = tree.find('results/location/metroArea')
        locationId = location.attrib['id']
        locationLat = location.attrib['lat']
        locationLong = location.attrib['lng']

        location.insert(0, locationId)
        location.insert(1, locationLat)
        location.insert(2, locationLong)

        return location

    else:
        # Need better error handling
        print "Location does not exist or something else went wrong with the connection to the Songkick server."
        sys.exit()

def getLocInfo(lat,long):

    results = []
    index = 0

    api_key = "AIzaSyDva2nYRJnjiQ-BW-I67_5m7GxA_19gA7Y"

    url = "https://maps.googleapis.com/maps/api/place/search/xml?location="+lat+","+long+"&radius=10000&types=amusement_park|museum|shopping_mall|zoo|point_of_interest&sensor=false&key=" + api_key

    poiXML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)

    if poiXML.status_code == 200:

        tree = etree.fromstring(poiXML.content)

        for poi in tree.findall('result'):

            poiName = poi.find('name').text
            results.insert(index, poiName)
            index += 1

        return results

    else:
        print "Something went wrong with the connection to the Google Places server"
        sys.exit()

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

                try:
                    genres = findEventGenres(event.find('performance/artist').attrib['displayName'])

                    concert = []

                    concert.insert(0, event.attrib['id'])
                    concert.insert(1, concertDate)
                    concert.insert(2, event.attrib['displayName'])
                    concert.insert(3, event.find('performance/artist').attrib['displayName'])
                    concert.insert(4, event.find('venue').attrib['displayName'])
                    concert.insert(5, genres)

                except AttributeError:
                    concert.insert(0, "")
                    concert.insert(1, "")
                    concert.insert(2, "")
                    concert.insert(3, "")
                    concert.insert(4, "")
                    concert.insert(5, "")

                events.insert(eventIndex, concert)
                eventIndex += 1

        return events

    else:
        # Need better error handling
        print "Event per page lookup failed or something else went wrong with the connection to the Songkick server."

def matchEvents(username, city):

    query = """
PREFIX ns2:<http://iwa2012-18-project.appspot.com/>
PREFIX ns1:<http://iwa2012-18-project.appspot.com/event/>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?eventid ?event ?date
WHERE {
?eventid ns1:artist ?artistURI .
<http://iwa2012-18-project.appspot.com/lastfm/%s> ns2:likesArtist ?artistURI .
?eventid rdfs:label ?event .
?eventid ns1:onDate ?date .
?eventid ns1:city <http://dbpedia.org/resource/%s> .
}
""" % (username, city)

    endPoint = rdfStoreUrl + "?"

    response = queryRdfStore(endPoint, query)

    res = []
    resIndex = 0

    for row in response:
        event = []
        eventIndex = 0
        for key,value in row.iteritems():
            event.insert(eventIndex,value)
            eventIndex += 1
        res.insert(resIndex, event)
        resIndex += 1

    return res

def getRecommendations(username, city):
    query = """
PREFIX ns2:<http://iwa2012-18-project.appspot.com/>
PREFIX ns1:<http://iwa2012-18-project.appspot.com/event/>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?eventid ?event ?date
WHERE {
?eventid ns1:artist ?artistURI .
?eventid ns1:genre ?genre .
<http://iwa2012-18-project.appspot.com/lastfm/%s> ns2:likesGenre ?genre .
?eventid rdfs:label ?event .
?eventid ns1:onDate ?date .
?eventid ns1:city <http://dbpedia.org/resource/%s> .
}
""" % (username, city)

    endPoint = rdfStoreUrl + "?"

    response = queryRdfStore(endPoint, query)

    res = []
    resIndex = 0

    for row in response:
        event = []
        eventIndex = 0
        for key,value in row.iteritems():
            event.insert(eventIndex,value)
            eventIndex += 1
        res.insert(resIndex, event)
        resIndex += 1

    return res


def getGenres(artists, nrOfGenres, topArtists):

    if topArtists > len(artists):
        topArtists = len(artists)

    index = 0

    res = []
    resindex = 0

    while(index < topArtists):
        artist = artists[index].replace(" ","_")

        query = """PREFIX dbpedia-owl: <http://dbpedia.org/property/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?genre
WHERE {
{ <http://dbpedia.org/resource/%s> dbpedia-owl:genre ?genreURI.
?genreURI rdfs:label ?genre .
FILTER (langMatches(lang(?genre), 'en')) }
}
""" % (artist)

        endpoint = "http://dbpedia.org/sparql?"

        response = queryRdfStore(endpoint,query)

        index += 1

        for row in response:
    
            for key,value in row.iteritems():
                res.insert(resindex,value)
                resindex += 1

    resCounted = [(a, res.count(a)) for a in set(res)]
    resSorted = sorted(resCounted, key=itemgetter(1), reverse=True)

    genreIndex = 0
    genres = []

    for item in resSorted:
        if genreIndex == nrOfGenres:
            break
        genres.insert(genreIndex, item[0])
        genreIndex += 1

    return genres

def findEventGenres(artistName):

    res = []

    query = """
PREFIX dbpedia-owl: <http://dbpedia.org/property/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?genre
WHERE {
{ <http://dbpedia.org/resource/%s> dbpedia-owl:genre ?genreURI.
?genreURI rdfs:label ?genre .
FILTER (langMatches(lang(?genre), 'en')) }
}
""" % (artistName.replace(" ","_"))

    endpoint = "http://dbpedia.org/sparql?"

    response = queryRdfStore(endpoint,query)

    resindex = 0

    for row in response:
        for key,value in row.iteritems():
            res.insert(resindex,value)
            resindex += 1

    return res

def createRDF(username, city, artists, locationInformation, events, genres):

    graph = ConjunctiveGraph()

    rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')
    iwa = Namespace('http://iwa2012-18-project.appspot.com/')
    lfm = Namespace('http://iwa2012-18-project.appspot.com/lastfm/')
    ev = Namespace('http://iwa2012-18-project.appspot.com/event/')
    dbp = Namespace('http://dbpedia.org/resource/') # DBPedia link to artists, genres and cities
    
    for artist in artists:

        graph.add(( lfm[username], iwa['likesArtist'], dbp[artist.replace(" ","_")] ))
        graph.add(( dbp[artist.replace(" ","_")], rdfs['label'], Literal(artist) ))

    for location in locationInformation:

        graph.add(( dbp[city.replace(" ","_")], iwa['poi'], Literal(location) ))

    for event in events:

        try:
            graph.add(( ev[event[0]], ev['onDate'], Literal(str(event[1].year)+"-"+str(event[1].month)+"-"+str(event[1].day),datatype=XSD.date) ))
            graph.add(( ev[event[0]], rdfs['label'], Literal(event[2]) ))
            graph.add(( ev[event[0]], ev['artist'], dbp[event[3].replace(" ","_")] ))
            graph.add(( ev[event[0]], ev['venue'], Literal(event[4]) ))
            graph.add(( ev[event[0]], ev['city'], dbp[city.replace(" ","_")] ))

            for eventGenre in event[5]:

                graph.add(( ev[event[0]], ev['genre'], dbp[eventGenre.replace(" ","_")] ))

        except AttributeError:
            graph.add(( ev[event[0]], rdfs['label'], Literal("Event is missing information") ))

    for genre in genres:

        graph.add(( lfm[username], iwa['likesGenre'], dbp[genre.replace(" ","_")] ))
        graph.add(( dbp[genre.replace(" ","_")], rdfs['label'], Literal(genre) ))

    graph.add(( dbp[city.replace(" ","_")], rdfs['label'], Literal(city) ))

    return graph

def storeRDF(graph):

    data=graph.serialize(format='xml')    
    url = rdfStoreUrl + "/statements"

    jsonresult = urlfetch.fetch(url,payload=data,deadline=30,method=urlfetch.POST, headers={ 'content-type': 'application/rdf+xml'})

def queryRdfStore(endPoint, query):

    try:
        url = endPoint + urllib.urlencode({"query" : query})

    except UnicodeEncodeError:
        return ""

    jsonresult = urlfetch.fetch(url,deadline=30,method=urlfetch.GET, headers={"accept" : "application/sparql-results+json"})

    if(jsonresult.status_code == 200):
        res = json.loads(jsonresult.content)
        
        res_var = res['head']['vars']
        
        response = []
        for row in res['results']['bindings']:
            dic = {}
            for var in res_var:
                dic[var] = row[var]['value']
                
            response.append(dic)
                        
        return response    
    else:
        return {"error" : jsonresult.content} 

application = webapp.WSGIApplication([('/', MainPage)], debug=True)

def main():

    run_wsgi_app(application)

if __name__ == "__main__":
    main()