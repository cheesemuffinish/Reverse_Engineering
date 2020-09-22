import sys
import logging

LOGGING_LEVEL = logging.DEBUG
ENABLE_COLORS = True
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


if ENABLE_COLORS:
    class colors:
        PURPLE = '\033[95m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        NORMAL = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        INVERT = '\033[7m'
else:
    class colors:
        PURPLE = ''
        BLUE = ''
        GREEN = ''
        YELLOW = ''
        RED = ''
        NORMAL = ''
        BOLD = ''
        UNDERLINE = ''
        INVERT = ''

DECODED_COLOR = colors.GREEN#+colors.BOLD
UNDECODED_COLOR = colors.YELLOW#+colors.BOLD
ERROR_COLOR = colors.RED#+colors.BOLD

# Source: http://stackoverflow.com/questions/2186919/getting-correct-string-length-in-python-for-strings-with-ansi-color-codes
import re
strip_ANSI_escape_sequences_sub = re.compile(r"""
    \x1b     # literal ESC
    \[       # literal [
    [;\d]*   # zero or more digits or semicolons
    [A-Za-z] # a letter
    """, re.VERBOSE).sub

def strip_ANSI_escape_sequences(s):
    return strip_ANSI_escape_sequences_sub("", s)