#Library with methods for accessing the Sesame triplestore

import urlfetch
import urllib
from django.utils import simplejson as json
from operator import itemgetter

from rdflib.graph import ConjunctiveGraph
from rdflib.term import URIRef, Literal
from rdflib.namespace import Namespace, RDF, RDFS, XSD

rdfStoreUrl = 'http://ec2-46-51-144-109.eu-west-1.compute.amazonaws.com:8080/openrdf-sesame/repositories/iwaproj'

def matchEvents(username,city):

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
