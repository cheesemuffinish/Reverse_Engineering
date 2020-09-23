import sys
import logging

LOGGING_LEVEL = logging.DEBUG
logger = None

def setupLogging():
    global logger
    root = logging.getLogger()
    root.setLevel(LOGGING_LEVEL)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(LOGGING_LEVEL)
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)
    logger = root
