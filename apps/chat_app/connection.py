from twitch_auth import AUTH_TOKEN, USERNAME
import socket
import time
from ..clips_app.formgen import clipStream
from threading import Thread

TCP_IP = socket.gethostbyname('irc.chat.twitch.tv')
TCP_PORT = 6667
BUFFER_SIZE = 4096

#linked list
class MessageNode(object):
    def __init__(self, val):
        self.val = val
        self.next = None

class MessageList(object):
    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0.0

    #adding to tail
    def add(self, val):
        newNode = MessageNode(val)
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
class RunningMessages(MessageList):
    #adds a new message/timestamp to the list
    def add(self, message, timestamp):
        super(RunningMessages, self).add({ 'message': message, 'timestamp': timestamp })
    
    #removes old messages from the head if the current head was created more than [timeframe] seconds ago
    def trim(self, timeframe):
        while time.time() - self.head.val['timestamp'] > timeframe:
            super(RunningMessages, self).pop()

    #prints out all of the messages in the list
    def dump(self):
        currentNode = self.head
        while currentNode is not None:
            print currentNode.val['message']
            currentNode = currentNode.next

#decorator that creates a separate thread for the wrapped function to avoid blocking main django thread
def schedule(func):
    def wrapper(*args, **kwargs):
        t = Thread(target = func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return wrapper

#establishes connection to twitch IRC server, returns connected socket
def connect(channel_name):
    s = socket.socket()
    s.connect(( TCP_IP, TCP_PORT ))
    oauth = 'oauth:' + AUTH_TOKEN[6:]
    s.send('PASS ' + oauth + '\r\n')
    s.send('NICK ' + USERNAME + '\r\n')
    s.send('USER ' + USERNAME + '\r\n')
    s.send('JOIN #' + channel_name + '\r\n')
    connect_spew = s.recv(BUFFER_SIZE) #clears the buffer
    return s

#returns the latest message from the socket
def readChat(socket):
    return socket.recv(BUFFER_SIZE)

#Starts in a new thread. Keeps track of messages created, both total and running total, clips the stream once the thread determines that an interesting spike in activity has occured (as determined by the parameters)
#everything is floats to make sure the averages aren't too messed up
@schedule
def chatStats(channel_name, running_timeframe=10.0, min_timeframe=60.0, min_delay_between_clips=30.0, activity_threshold=3):
    #initial setup
    stream = connect(channel_name)
    #gets time at the start of the thread
    start_time = time.time()
    total_time_elapsed = 0.0
    total_messages = 0.0
    clipped_at = 0.0
    running_total_messages = RunningMessages() #this will be a list of messages and timestamps
    while True:
        #gets message from stream
        msg = readChat(stream)
        #updates total elapsed time
        current_time = time.time()
        total_time_elapsed = current_time - start_time
        #determines whether the stream has been live long enough to meet or exceed the running timeframe setting
        if total_time_elapsed > running_timeframe:
            timeframe = running_timeframe
        else:
            timeframe = total_time_elapsed
        #if msg exists, increment total number of messages received, add the message to the moving frame, and trim the moving frame to get rid of old messages
        #the goal of the moving frame is to contain only messages created in the last X seconds
        if len(msg) > 0:
            total_messages += 1
            running_total_messages.add(msg, current_time)
            running_total_messages.trim(timeframe)
        #gets average number of messages created since we started watching the stream, and also during the moving frame
        total_per_second = total_messages/total_time_elapsed
        running_per_second = running_total_messages.length/timeframe
        #if the number of messages created per second in the last X seconds exceeds the average amount since we started watching the stream by a certain amount, AND we've been watching the stream long enough, AND it's been long enough since we last created a clip of this stream, THEN clip the stream
        if running_per_second > total_per_second * activity_threshold and total_time_elapsed > min_timeframe and current_time - clipped_at >= min_delay_between_clips:
            #clips at 5 seconds before detection to account for chat's delay between significant event and reaction/avg messages sent catchup
            clipStream(channel_name, 5)
            #stores current time as clipped_at, so that we don't create another clip immediately afterwards
            clipped_at = current_time
            print 'clipping {}'.format(channel_name)