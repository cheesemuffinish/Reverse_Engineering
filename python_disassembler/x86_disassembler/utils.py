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

#def binary(x):
#    return "{0:b}".format(x)


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

# Note: this function is derived from: https://gist.github.com/ImmortalPC/c340564823f283fe530b
def hexdump( src, length=16, sep='.', hasDecoded=None ):

    result = [];

    # Python3 support
    try:
        xrange(0,1);
    except NameError:
        xrange = range;

    for i in xrange(0, len(src), length):
        subSrc = src[i:i+length];
        hexa = '';
        isMiddle = False;
        for h in xrange(0,len(subSrc)):

            prefix = ""
            postfix = ""
            if hasDecoded and ENABLE_COLORS:
                if hasDecoded[i+h]:
                    prefix = DECODED_COLOR
                elif hasDecoded[i+h] == None:
                    prefix = ERROR_COLOR
                else:
                    prefix = UNDECODED_COLOR
                postfix = colors.NORMAL

            if h == length/2:
                hexa += ' ';
            h = subSrc[h];
            if not isinstance(h, int):
                h = ord(h);
            h = hex(h).replace('0x','');
            if len(h) == 1:
                h = '0'+h;
            hexa += prefix+h+postfix+' ';
        #print(repr(hexa))
        hexa = hexa.strip(' ');
        text = '';
        for cIdx, c in enumerate(subSrc):
            prefix = ""
            postfix = ""
            if hasDecoded and ENABLE_COLORS:
                if hasDecoded[i+cIdx]:
                    prefix = DECODED_COLOR
                elif hasDecoded[i+cIdx] == None:
                    prefix = ERROR_COLOR
                else:
                    prefix = UNDECODED_COLOR
                postfix = colors.NORMAL

            if not isinstance(c, int):
                c = ord(c);
            if 0x20 <= c < 0x7F:
                text += prefix+chr(c)+postfix;
            else:
                text += prefix+sep+postfix;

        # each prefix/postfix adds a character.... so length is weirder to calculate
        if ENABLE_COLORS:
            #result.append(('0x%08X  ▏ %-174s  ▏%-142s ▏') % (i, hexa, text))
            nonAnsiLen = len(strip_ANSI_escape_sequences(hexa))
            ansiLen = len(hexa)
            invisLen = ansiLen - nonAnsiLen
            result.append(('0x%08X  ▏ %-'+str((length*(2+1))+1+invisLen)+'s  ▏%-'+str(length+invisLen)+'s ▏') % (i, hexa, text))
        else:
            result.append(('0x%08X  ▏ %-'+str(length*(2+1)+1)+'s  ▏%-16s ▏') % (i, hexa, text));

    legend = ""
    table = '\n'.join(result)
    if ENABLE_COLORS and hasDecoded != None:
        legend =  "("+DECODED_COLOR+ "Decoded Byte"+colors.NORMAL+", "+UNDECODED_COLOR+"Undecoded Byte"+", "+ERROR_COLOR+"Error Byte"+colors.NORMAL+")\n"

    return legend + table


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