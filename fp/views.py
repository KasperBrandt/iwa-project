# Create your views here.
from django.http import HttpResponse
from django.core.context_processors import csrf
from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms

from datetime import date

import songkick
import util
import places
import lastfm_iwa as lastfm
import sesame


def index(request):
    return HttpResponse(lastfm.__file__)

def main(request):
    if request.method == 'GET':
       
        template_values = {'username' : "guillelmo",
                           'startDate' : "3/1/2012",
                           'endDate' : "12/1/2012",
                           'city': "Madrid"}
   
        path = "index.html"        
        return render_to_response(path, template_values, context_instance=RequestContext(request))
    
    elif request.method == 'POST':

        username = request.POST["username"]
        dateStart = request.POST["datepickerStart"]
        dateEnd = request.POST["datepickerEnd"]
        city = request.POST["city"]

        date1 = util.convertToDate(dateStart)
        date2 = util.convertToDate(dateEnd)

        if date1 > date2:
            # Need better error handling            
            print "Incorrect dates, make sure the end date lies after the start date."

        nrOfArtists = 100
        artists = lastfm.getUserArtists(username, nrOfArtists)

        nrOfGenres = 5
        genres = sesame.getGenres(artists[0:5], nrOfGenres)

        location = songkick.getLocation(city)

        locationInformation = places.getLocInfo(location[1],location[2])

        events = songkick.getEvents(date1, date2, location[0])

        graph = sesame.createRDF(username, city, artists, locationInformation, events, genres)

        sesame.storeRDF(graph)

        matchingEventsAllDates = sesame.matchEvents(username, city)
        recEventsAllDates = sesame.getRecommendations(username, city)

        matchingEvents = filterDates(matchingEventsAllDates,date1,date2)
        recEvents = filterDates(matchingEventsAllDates,date1,date2)                

        template_values = {
            'events': matchingEvents,
            'recEvents': recEvents,
            'username': username,
            'city': city,
            'cityInfo': locationInformation[0:15],
            'genres': genres,
            'artists': artists[0:15],
        }
        
        #path = os.path.join(os.path.dirname(__file__), "website.html")
        #self.response.out.write(template.render(path, template_values))
        return render_to_response("website.html", template_values)

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

