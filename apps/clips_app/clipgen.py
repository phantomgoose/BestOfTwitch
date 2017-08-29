import urllib2
from ..chat_app.twitch_auth import CLIENT_ID, API_TOKEN, PERSISTENT
from ..functions import schedule, log
import json
from dateutil import parser
from django.utils import timezone
import requests
import re
from .models import Clip, Emoticon
from django.core.exceptions import ObjectDoesNotExist
import threading

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

#converts emoticons in chat into image links (in its own thread)
# @schedule
def updateEmoticonDB():
    print 'starting update'
    print 'Active threads: ' + str(threading.active_count())
    url = 'https://api.twitch.tv/kraken/chat/emoticons'
    header = {
        'Client-iD': CLIENT_ID,
    }
    request = urllib2.Request(url, headers=header)
    response = urllib2.urlopen(request)
    jsonified_response = json.load(response)
    emoticon_dict = {}
    for emoticon in jsonified_response['emoticons']:
        key = emoticon['regex']
        url = emoticon['images'][0]['url']
        if key is None:
            key = 'temp'
        if url is None:
            url = 'temp'
        emoticon_dict[key] = url
    print 'built dictionary'
    for key in emoticon_dict.keys():
        existing_emoticon = False
        try:
            existing_emoticon = Emoticon.objects.get(name=key)
        except ObjectDoesNotExist:
            pass
        if existing_emoticon:
            if existing_emoticon.url != emoticon_dict[key]:
                log('Updating emoticon ' + key + ' due to url change.')
                existing_emoticon.url = emoticon_dict[key]
                existing_emoticon.save()
        else:
            log('Emoticon ' + key + ' does not exist in the DB yet. Creating new one.')
            Emoticon.objects.create(name=key, url=emoticon_dict[key])
    print 'built db'
    log('Finished updating emoticon DB.')

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