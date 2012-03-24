import urllib2 

class FetchResponse:
    """Wrapper class for the fetch method (not completely equivalent to the GAE response)"""
    content = ''

GET = 1
POST = 2

def fetch(url, payload=None, method=GET, headers={},
          allow_truncated=False, follow_redirects=True,
          deadline=None, validate_certificate=None):

    response = FetchResponse()

    req = urllib2.Request(url, payload, headers)
    

    res = urllib2.urlopen(req)
    
    response.content = res.read()
    response.status_code = res.code
    response.final_url = res.geturl()
    return response




