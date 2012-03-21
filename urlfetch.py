import urllib2 

class FetchResponse:
    """Wrapper class for the fetch method (not completely equivalent to the GAE response)"""
    content = ''
    
def fetch(url,deadline,method):
    response = FetchResponse()
    res = urllib2.urlopen(url)

    response.content = res.read()
    response.status_code = res.code
    response.final_url = res.geturl()
    return response

GET = 'get'


