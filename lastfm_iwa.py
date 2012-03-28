
# Last.fm methods build specially for IWA (not a generic API).

import urlfetch
import urllib2
import logging
from xml.etree import ElementTree as etree

api_key = "7e6d32dffbf677fc4f766168fd5dc30e"

def getUserArtists(username, nrOfArtists):

    #secret = "5856a08bb3d5154359f22daa1a1c732b"

    url = "http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user=" + username + "&limit=" + str(nrOfArtists) + "&api_key=" + api_key

    artistsXML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)

    artists = []

    if artistsXML.status_code == 200:

        tree = etree.fromstring(artistsXML.content)

        for artist in tree.findall('topartists/artist'):
            rank = artist.attrib['rank']
            name = artist.find('name')
            mbid = artist.find('mbid')
            artists.insert(int(rank), {'name': name.text, 'mbid': mbid.text})

    else:
        # Need better error handling
        print "Last FM User does not exist or something else went wrong with the connection to the Last FM server."
        sys.exit()

    return artists


def getAlbumInfo(mb_id):

    url = "http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key="+api_key+"&mbid="+mb_id
    #logger.info("getAlbum "+mb_id+" "+url)

    error = False
    try: 
        albumXML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)        
    except urllib2.HTTPError:
        error = True
        #logger.info("album not found.: "+mb_id)
            
    if not error and albumXML.status_code == 200:
        
        tree = etree.fromstring(albumXML.content)

        album = tree.find('album')

        name =  album.find('name').text
        reldate = album.find('releasedate').text.strip()
        image = album.find("image[@size='large']").text
        
        return {'name': name, 'reldate' : reldate, 'image': image}
        
def getArtistImage(mb_id):

    url = "http://ws.audioscrobbler.com/2.0/?method=artist.getimages&mbid="+mb_id+"&api_key="+api_key+"&limit=1"

    #logger.info("getAlbum "+mb_id+" "+url)

    error = False
    
    try: 
        XML = urlfetch.fetch(url,deadline=60,method=urlfetch.GET)        
    except urllib2.HTTPError:
        error = True
        #logger.info("album not found.: "+mb_id)

    
    if not error and XML.status_code == 200:

        tree = etree.fromstring(XML.content)        

        name = tree.find("images").attrib['artist']
        image = tree.find("images").find("image").find('sizes').find("size[@name='original']").text
        return {'name': name, 'image': image}
        
        
