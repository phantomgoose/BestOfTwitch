import urllib2
from ..chat_app.twitch_auth import CLIENT_ID
import json
from dateutil import parser
from datetime import timedelta
from django.utils import timezone

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