from threading import Thread
from datetime import datetime
import logging
import logging.handlers

file_name = 'debug.log'
logger = logging.getLogger('Logger')
handler = logging.handlers.RotatingFileHandler(file_name, maxBytes=5000)
logger.addHandler(handler)

#decorator that creates a separate thread for the wrapped function to avoid blocking main django thread
def schedule(func):
    def wrapper(*args, **kwargs):
        t = Thread(target = func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return wrapper

#logs errors and such to a file
def log(message):
    logger.debug(str(datetime.now()) + ': ' + message + '\n')
    # print (str(datetime.now()) + ': ' + message + '\n')
    # open('error_log.txt', 'a').write(str(datetime.now()) + ': ' + message + '\n')