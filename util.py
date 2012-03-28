import re
#Auxiliary functions module

from datetime import date

def convertToDate(dateOld):
    dateArr = dateOld.split('/')
    dateNew = date(int(dateArr[2]),int(dateArr[0]),int(dateArr[1]))
    return dateNew

def getMBId(url):
    return re.findall('release/(.*?)\.html',url)[0]
