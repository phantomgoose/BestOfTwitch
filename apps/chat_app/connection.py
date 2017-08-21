import urllib2
from twitch_auth import AUTH_TOKEN

headers = {
    'Authorization': AUTH_TOKEN,
}

url = 'https://api.twitch.tv/kraken/channels/summit1g/'

request = urllib2.Request(url, headers=headers)

print request.get_header('Client-ID')

response = urllib2.urlopen(request).read()
print response