from __future__ import print_function
from datetime import timedelta
import datetime
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def convert_time(hour, min):
    seconds = hour*60*60 + min*60
    hr = seconds//3600
    seconds %= 3600
    mn = seconds//60

    return (hr, mn)


def day_time_splitter(fulltime):
    days = []
    fulltime = fulltime.split('.')
    exact_time = fulltime[1:3]
    hr = int(exact_time[0])
    mn = int(exact_time[1])
    for n in range(len(fulltime[0])):
        days.append(int(fulltime[0][n]))

    (hr, mn) = convert_time(hr, mn)

    return (days, hr, mn)


def is_tenMin_range(fulltime):

    (day, hr, mn) = day_time_splitter(fulltime)
    classtime = datetime.datetime.now().replace(hour=hr, minute=mn)
    thres = 20
    if mn-thres < 0:
        after = datetime.datetime.now().replace(hour=hr, minute=mn+thres)
        (hr, mn) = convert_time(hr, mn-thres)
        before = datetime.datetime.now().replace(hour=hr, minute=mn)

    elif mn+thres > 59:
        before = datetime.datetime.now().replace(hour=hr, minute=mn-thres)
        (hr, mn) = convert_time(hr, mn+thres)
        after = datetime.datetime.now().replace(hour=hr, minute=mn)
    else:
        before = datetime.datetime.now().replace(hour=hr, minute=mn-thres)
        after = datetime.datetime.now().replace(hour=hr, minute=mn+thres)

    today = datetime.datetime.now().weekday()
    if today in day and before <= datetime.datetime.now() <= after:
        print('right time to zoom')
        return True


def sliceLastOccur(string, char):
    res = ''
    i = 0

    while(i < len(string)):
        if(string[i] == char):
            res = string[0:i]
        i += 1
    return res


def googleDatetimeConverter(dt):
    dt = sliceLastOccur(dt, '-')
    res = datetime.datetime.strptime(str(dt), '%Y-%m-%dT%H:%M:%S')
    return res


def openZoom(zoomLink):
    print(zoomLink)
    ch_options = Options()
    ch_options.add_argument('--no-sandbox')
    ### Type "chrome://version/" in google chrome and look for your profile path ###
    ch_options.add_argument('user-data-dir=/path/to/chrome/profile/') 
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=ch_options)
    driver.get(zoomLink)


def gotZoom(link):
    if 'zoom' in link:
        return True
    else:
        return False


def googAuto(calendarId):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            ### follow this link https://developers.google.com/calendar/quickstart/python and enable google calendar API to get your credentials.json ###
            flow = InstalledAppFlow.from_client_secrets_file('/path/to/google/calendar/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.now().isoformat() + 'Z'  # 'Z' indicates UTC time
    nowdt = datetime.datetime.now()
    nowDatetime = datetime.datetime.strptime(nowdt.isoformat(), '%Y-%m-%dT%X.%f')
    maxtime = datetime.datetime.utcnow().replace(hour=23, minute=59, second=0).isoformat() + 'Z'
    print("Getting today's Zoom meetings..")
    events_result = service.events().list(calendarId=calendarId, timeMin=now, timeMax=maxtime, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    timenow = datetime.datetime.now()
    meetings = []
    meetings_list = []
    dummy_dict = {'name': 'sample_name', 'startTime': 'sample_time', 'link': 'sample_link'}

    if not events:
        print('No upcoming Zooms found for today.')

    print("Today's events: ")
    for event in events:

        loc = event.get('location')
        if 'location' in event and gotZoom(loc):
            meetings = dummy_dict.copy()

            start = event['start'].get('dateTime')
            if start != None:
                pass
            else:
                start = event['originalStartTime'].get('dateTime')

            start = googleDatetimeConverter(start)
            name = event['summary']
            meetings['name'] = name
            meetings['startTime'] = start
            meetings['link'] = event.get('location')
            print(meetings['name'])
            meetings_list.append(meetings)

    timeThres = datetime.timedelta(minutes=20)

    res = False
    for i in meetings_list:
        if ((i['startTime'] - timeThres) <= timenow <= (i['startTime'] + timeThres) and gotZoom(i['link'])):
            print('Starting', i['name'], '...')
            openZoom(i['link'])
            res = True
            break
        else:
            pass

    if res is False:
        print('no zooms now')

    time.sleep(1)
    print('Done')
    time.sleep(0.5)


googAuto('primary')
