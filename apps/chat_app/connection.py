from twitch_auth import AUTH_TOKEN, USERNAME
import socket
import time
from ..clips_app.clipgen import clipStream
from threading import Thread
import re
from datetime import datetime

TCP_IP = socket.gethostbyname('irc.chat.twitch.tv')
TCP_PORT = 6667
BUFFER_SIZE = 4096

#linked list
class Node(object):
    def __init__(self, val):
        self.val = val
        self.next = None

class LinkedList(object):
    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0.0

    #adding to tail
    def add(self, val):
        newNode = Node(val)
        if self.head is None:
            self.head = newNode
            self.tail = newNode
        else:
            self.tail.next = newNode
            self.tail = newNode
        self.length += 1.0
        return newNode

    #popping from head
    def pop(self):
        if self.head is None:
            return -1
        condemnedNode = self.head
        self.head = self.head.next
        #if the popped node was the only node in the list, also update the tail
        if self.head is None:
            self.tail = None
        self.length -= 1.0
        return condemnedNode

#this is where we'll store our message/timestamp values for the moving time window
class MessageList(LinkedList):

    #adding an empty messages property to help detect disconnects
    def __init__(self):
        self.empty_messages = 0
        super(MessageList, self).__init__()    

    #adds a new message/timestamp to the list
    def add(self, message, timestamp):
        if len(message) < 1:
            self.empty_messages += 1
        super(MessageList, self).add({ 'message': message, 'timestamp': timestamp })
    
    #removes old messages from the head if the current head was created more than [timeframe] seconds ago
    def trim(self, timeframe):
        while time.time() - self.head.val['timestamp'] > timeframe:
            super(MessageList, self).pop()

    #prints out all of the messages in the list
    def dump(self):
        currentNode = self.head
        result = []
        while currentNode is not None:
            result.append(currentNode.val['message'])
            currentNode = currentNode.next
        return result

    #checks if the last few messages are empty
    def detectDisconnect(self):
        if self.length > 10 and self.empty_messages > 10:
            self.empty_messages = 0
            log('MessageList detected disconnect')
            return True
        return False


#decorator that creates a separate thread for the wrapped function to avoid blocking main django thread
def schedule(func):
    def wrapper(*args, **kwargs):
        t = Thread(target = func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return wrapper

#establishes connection to twitch IRC server, returns connected socket
def connect(channel_name):
    log('connecting to ' + channel_name)
    s = socket.socket()
    s.connect(( TCP_IP, TCP_PORT ))
    oauth = 'oauth:' + AUTH_TOKEN[6:]
    s.send('PASS ' + oauth + '\r\n')
    s.send('NICK ' + USERNAME + '\r\n')
    s.send('USER ' + USERNAME + '\r\n')
    s.send('JOIN #' + channel_name + '\r\n')
    connect_spew = s.recv(BUFFER_SIZE) #clears the buffer
    log('connected to ' + channel_name)
    return s

#returns the latest message from the socket
def readChat(socket):
    return socket.recv(BUFFER_SIZE)

#returns just the user's name and message by removing all the extra fat
def parseMessage(channel_name, twitch_message):
    MESSAGE_REGEX = re.compile(channel_name + r' :(?P<message>.*)')
    try:
        message = MESSAGE_REGEX.search(twitch_message).groupdict()['message']
        return message
    except:
        log('unable to parse raw chat message')
        return twitch_message

#Starts in a new thread. Keeps track of messages created, both total and running total, clips the stream once the thread determines that an interesting spike in activity has occured (as determined by the parameters)
#everything is floats to make sure the averages aren't too messed up
@schedule
def chatStats(channel_name, running_timeframe=10.0, max_timeframe=120, delay_on_connect=60.0, delay_on_clip=30.0, activity_threshold=3):
    #initial setup
    stream = connect(channel_name)
    #gets time at the start of the thread
    start_time = time.time()
    total_time_elapsed = 0.0
    clipped_at = 0.0
     #this will be a list of messages and timestamps; could create a second list to collect messages over a longer time period than the target one (eg total is 5 minutes, target is 15 seconds) for better accuracy
    short_list = MessageList()
    long_list = MessageList()
    while True:
        #gets message from stream
        msg = readChat(stream)
        #keeps connection alive by replying to pings. If a ping is received, the rest of the loop is skipped.
        if pingPong(stream, msg):
            continue
        #attempts to reconnect to the chat server if a disconnect has been detected
        if short_list.detectDisconnect():
            stream = connect(channel_name)
        #prettifies the message
        msg = parseMessage(channel_name, msg)
        print msg
        #updates total elapsed time
        current_time = time.time()
        total_time_elapsed = current_time - start_time
        #determines whether the stream has been live long enough to meet or exceed the running timeframe setting
        #if msg exists, increment total number of messages received, add the message to the moving frame, and trim the moving frame to get rid of old messages
        #the goal of the moving frame is to contain only messages created in the last X seconds
        if len(msg) > 0:
            short_list.add(msg, current_time)
            long_list.add(msg, current_time)
            short_list.trim(running_timeframe)
            long_list.trim(max_timeframe)
        #gets average number of messages created since we started watching the stream, and also during the moving frame
        long_per_sec = long_list.length/max_timeframe
        short_per_sec = short_list.length/running_timeframe
        #if the number of messages created per second in the last X seconds exceeds the average amount since we started watching the stream by a certain amount, AND we've been watching the stream long enough, AND it's been long enough since we last created a clip of this stream, THEN clip the stream
        if (short_per_sec > long_per_sec * activity_threshold) and (total_time_elapsed > delay_on_connect) and (current_time - clipped_at >= delay_on_clip):
            #clips at 5 seconds before detection to account for chat's delay between significant event and reaction/avg messages sent catchup
            clipStream(channel_name, 5, short_list.dump())
            #stores current time as clipped_at, so that we don't create another clip immediately afterwards
            clipped_at = current_time
            log('clipping ' + channel_name)

#keeps connection alive by replying to IRC server's pings, returns true if the msg contained the ping, false otherwise
def pingPong(stream, msg):
    if 'PING :tmi.twitch.tv' in msg:
        stream.send('PONG :tmi.twitch.tv\r\n')
        #logging for pings
        log('replied to ping')
        return True
    return False

#logs errors and such to a file
def log(message):
    open('error_log.txt', 'w').write(str(datetime.now()) + ': ' + message)