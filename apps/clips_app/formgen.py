import urllib2
from ..chat_app.twitch_auth import CLIENT_ID, API_TOKEN, PERSISTENT
import json
from dateutil import parser
from datetime import timedelta
from django.utils import timezone
import requests

#gets the stream object by name
def getStream(channel_name):
    url = 'https://api.twitch.tv/kraken/streams/{}'.format(channel_name)
    header = {
        'Client-iD': CLIENT_ID,
    }
    request = urllib2.Request(url, headers=header)
    response = urllib2.urlopen(request)
    stream = json.load(response)
    return stream

#returns stream object's ID as an integer
def getStreamID(stream):
    return int(stream['stream']['_id'])

#returns stream object's uptime in seconds as an integer
def getStreamUptime(stream):
    created_at = parser.parse(stream['stream']['created_at'])
    now = timezone.now()
    diff = now - created_at
    diffSeconds = diff.seconds
    return diffSeconds

#returns stream object's fps as an integer
def getStreamFPS(stream):
    average_fps = stream['stream']['average_fps']
    if average_fps > 25.0 and average_fps < 35.0:
        return 30
    elif average_fps > 55.0 and average_fps < 65.0:
        return 60
    else:
        return -1

#returns stream object's current frame offset as an integer. Unsure if needed, offset seems to be specified in seconds actually
def getStreamOffset(stream):
    offset = getStreamUptime(stream) * getStreamFPS(stream)
    return offset

#clips a stream at current time using my API token
def clipStream(channel_name, chat_offset=0):
    stream = getStream(channel_name)
    stream_id = getStreamID(stream)
    offset = getStreamUptime(stream)

    post_data = {
        'channel': channel_name,
        'offset': offset - chat_offset,
        'broadcast_id': stream_id,
    }

    cookie_data = {
        'api_token': API_TOKEN,
        'persistent': PERSISTENT,
    }

    r = requests.post('http://clips.twitch.tv/clips', data=post_data, cookies=cookie_data)