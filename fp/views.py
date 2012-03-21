# Create your views here.
from django.http import HttpResponse
from django.core.context_processors import csrf
from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms

import songkick
import util
import lastfm_iwa as lastfm


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

        nrOfArtists = 500
        artists = lastfm.getUserArtists(username, nrOfArtists)

        locationId = songkick.getLocationId(city)

        events = songkick.getEvents(date1, date2, locationId)

        matchingEvents = util.matchEvents(artists, events)

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
        
        #path = os.path.join(os.path.dirname(__file__), "website.html")
        #self.response.out.write(template.render(path, template_values))
        return render_to_response("website.html", template_values)
