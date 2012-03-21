
#Auxiliary functions module

from datetime import date

def convertToDate(dateOld):
    dateArr = dateOld.split('/')
    dateNew = date(int(dateArr[2]),int(dateArr[0]),int(dateArr[1]))
    return dateNew

def matchEvents(artists,events):

    result = []
    index = 0

    for concert in events:
        if artists.count(concert[2]) > 0:
            result.insert(index,concert)
            index += 1

    return result
