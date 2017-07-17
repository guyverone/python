import urllib.request
import time
import json
from win10toast import ToastNotifier
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import cgitb
cgitb.enable(format='text')

url = 'https://www.jubi.com'
allTicker = '/api/v1/allticker/'
ticker = '/api/v1/ticker'

sched = BackgroundScheduler()
percent = 0
openingPriceDict = {}


def getTicker(coin):
    return getHttpResponse(url + ticker + "?coin=" + coin)

def getHttpResponse(url):
    resp = urllib.request.urlopen(url)
    respData = resp.read()
    return str(respData, 'utf8')
    
def getAllTicker():
    return getHttpResponse(url + allTicker)

@sched.scheduled_job('cron', day_of_week='*', hour='0,8,16', minute=0)
def getOpeningPrice():
    respData = getAllTicker()
    now = datetime.datetime.now()
    print("Starting to get opening price on " + now.strftime('%Y-%m-%d %H:%M:%S'))
    getEachCoinBasicInfo('getAllTicker', respData, getOpeningPrice_continue)

def getEachCoinBasicInfo(switch, jsonStr, callback):
    parsedJsonData = json.loads(jsonStr)
    if(switch == 'getAllTicker'):
        keys = parsedJsonData.keys()
        for key in keys:
            itemData = parsedJsonData.get(key)
            high = itemData.get('high')
            low = itemData.get('low')
            last = itemData.get('last')
            callback(key, high, low, last)
    else:
        key = switch
        high = parsedJsonData.get('high')
        low = parsedJsonData.get('low')
        last = parsedJsonData.get('last')
        callback(key, high, low, last)
        
def getOpeningPrice_continue(key, high, low, last):
    openingPriceDict[key] = last

def doNotificate(switch, jsonStr):
    getEachCoinBasicInfo(switch, jsonStr, doNotificate_continue)

def doNotificate_continue(key, high, low, last):
    openingPrice = 0
    if(isinstance(openingPriceDict.get(key), float) or isinstance(openingPriceDict.get(key), int)):
        openingPrice = openingPriceDict.get(key)
    else:
        openingPrice = last
    calPer = calculatePercentage(openingPrice, last)
    if((abs(calPer) - percent)>=0 or calPer==0):
        buildContent(key, openingPrice, high, low, last, calPer)

def calculatePercentage(openingPrice, lastPrice):
    calPer = (float(lastPrice) - float(openingPrice)) / float(openingPrice)
    return calPer

def buildContent(key, openingPrice, high, low, last, calPer):
    sleep(0,0,3)
    if(calPer >= 0):
        showContent(key, openingPrice, high, low, last, calPer, "+")
    else:
        showContent(key, openingPrice, high, low, last, calPer, "")

def showContent(key, openingPrice, high, low, last, calPer, sign):
    strContent = 'opening: ' + str(openingPrice) + '  \nhighest: ' + str(high) + '    lowest: ' + str(low) + ' \nlast: ' + str(last) + '    ' + sign + str(round(calPer,2)*100) +'%'
    print(key + " " + strContent)
    invokeWindowsNotifier(key, strContent)

def invokeWindowsNotifier(title, message):
    toaster = ToastNotifier()
    toaster.show_toast(title, message)

def runGetAllTicker():
    while(1):
        respData = getAllTicker()
        doNotificate('getAllTicker', respData)
        sleep(0,0,120)

def sleep(hour, min, sec):
    time.sleep(hour*3600 + min*60 + sec)


def runGetTicker(coins):
    while(1):
        for coin in coins:
            respData = getTicker(coin)
            doNotificate(coin, respData)
            sleep(0,0,15)
        
sched.start()
