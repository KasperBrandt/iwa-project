
# Last.fm methods build specially for IWA (not a generic API).

import urlfetch
from xml.etree import ElementTree as etree

def getUserArtists(username, nrOfArtists):

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


