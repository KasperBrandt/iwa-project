#Google Places methods build for IWA (not a generic API). 

import urlfetch
from xml.etree import ElementTree as etree

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
            results.insert(index,poiName)
            index+=1

        return results

    else:
        print "Something went wrong with the connection to the Google Places server"
        sys.exit()
