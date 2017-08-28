import urllib2
from ..chat_app.twitch_auth import CLIENT_ID, API_TOKEN, PERSISTENT
import json
from dateutil import parser
from django.utils import timezone
import requests
import re
from .models import Clip

SLUG_REGEX = re.compile(r'slug: "(?P<slug>[a-zA-Z]*)"')

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

#clips a stream at current time using my API token and returns the clip's slug
def clipStream(channel_name, chat_offset=0, message_dump=""):
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
    messages = ' '.join(message_dump)
    try:
        Clip.objects.create(url='https://clips.twitch.tv/' + SLUG_REGEX.search(r.content).groupdict()['slug'], messages=messages, channel=channel_name)
    except AttributeError:
        print 'Fatal: could not create clip. API error?'
        print AttributeError, AttributeError.args, AttributeError.message