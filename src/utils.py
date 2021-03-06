# coding=utf-8
import logging
import math
import string
import stat
import os.path
import tempfile
from collections import abc
import collections

from sys import platform
from enum import Enum

from typing import (
    Union,
    Tuple,
    SupportsFloat, Iterator,
)

try:
    # This module is generated when cx_freeze compiles the app.
    from BUILD_CONSTANTS import BEE_VERSION
except ImportError:
    # We're running from source!
    BEE_VERSION = "(dev)"
    FROZEN = False
else:
    FROZEN = True

WIN = platform.startswith('win')
MAC = platform.startswith('darwin')
LINUX = platform.startswith('linux')

# Formatters for the logger handlers.
short_log_format = None
long_log_format = None

# Various logger handlers
stdout_loghandler = None
stderr_loghandler = None
file_loghandler = None

# App IDs for various games. Used to determine which game we're modding
# and activate special support for them
STEAM_IDS = {
    'PORTAL2': '620',

    'APTAG': '280740',
    'APERTURE TAG': '280740',
    'ALATAG': '280740',
    'TAG': '280740',

    'TWTM': '286080',
    'THINKING WITH TIME MACHINE': '286080',

    # Others:
    # 841: P2 Beta
    # 213630: Educational
    # 247120: Sixense
    # 211480: 'In Motion'
    # 317400: PS Mel - No workshop
}

if WIN:
    # Some events differ on different systems, so define them here.
    EVENTS = {
        'LEFT': '<Button-1>',
        'LEFT_DOUBLE': '<Double-Button-1>',
        'LEFT_CTRL': '<Control-Button-1>',
        'LEFT_SHIFT': '<Shift-Button-1>',
        'LEFT_RELEASE': '<ButtonRelease-1>',
        'LEFT_MOVE': '<B1-Motion>',

        'RIGHT': '<Button-3>',
        'RIGHT_DOUBLE': '<Double-Button-3>',
        'RIGHT_CTRL': '<Control-Button-3>',
        'RIGHT_SHIFT': '<Shift-Button-3>',
        'RIGHT_RELEASE': '<ButtonRelease-3>',
        'RIGHT_MOVE': '<B3-Motion>',

        'KEY_EXPORT': '<Control-e>',
        'KEY_SAVE_AS': '<Control-s>',
        'KEY_SAVE': '<Control-Shift-s>',
    }
    # The text used to show shortcuts in menus.
    KEY_ACCEL = {
        'KEY_EXPORT': 'Ctrl-E',
        'KEY_SAVE': 'Ctrl-S',
        'KEY_SAVE_AS': 'Ctrl-Shift-S',
    }

    CURSORS = {
        'regular': 'arrow',
        'link': 'hand2',
        'wait': 'watch',
        'stretch_vert': 'sb_v_double_arrow',
        'stretch_horiz': 'sb_h_double_arrow',
        'move_item': 'plus',
        'destroy_item': 'x_cursor',
        'invalid_drag': 'no',
    }

    def add_mousewheel(target, *frames, orient='y'):
        """Add events so scrolling anywhere in a frame will scroll a target.

        frames should be the TK objects to bind to - mainly Frame or
        Toplevel objects.
        Set orient to 'x' or 'y'.
        This is needed since different platforms handle mousewheel events
        differently - Windows needs the delta value to be divided by 120.
        """
        scroll_func = getattr(target, orient + 'view_scroll')

        def mousewheel_handler(event):
            scroll_func(int(event.delta / -120), "units")
        for frame in frames:
            frame.bind('<MouseWheel>', mousewheel_handler, add='+')

elif MAC:
    EVENTS = {
        'LEFT': '<Button-1>',
        'LEFT_DOUBLE': '<Double-Button-1>',
        'LEFT_CTRL': '<Control-Button-1>',
        'LEFT_SHIFT': '<Shift-Button-1>',
        'LEFT_RELEASE': '<ButtonRelease-1>',
        'LEFT_MOVE': '<B1-Motion>',

        'RIGHT': '<Button-2>',
        'RIGHT_DOUBLE': '<Double-Button-2>',
        'RIGHT_CTRL': '<Control-Button-2>',
        'RIGHT_SHIFT': '<Shift-Button-2>',
        'RIGHT_RELEASE': '<ButtonRelease-2>',
        'RIGHT_MOVE': '<B2-Motion>',

        'KEY_EXPORT': '<Command-e>',
        'KEY_SAVE_AS': '<Command-s>',
        'KEY_SAVE': '<Command-Shift-s>',
    }

    KEY_ACCEL = {
        # tkinter replaces Command- with the special symbol automatically.
        'KEY_EXPORT': 'Command-E',
        'KEY_SAVE': 'Command-S',
        'KEY_SAVE_AS': 'Command-Shift-S',
    }

    CURSORS = {
        'regular': 'arrow',
        'link': 'pointinghand',
        'wait': 'spinning',
        'stretch_vert': 'resizeupdown',
        'stretch_horiz': 'resizeleftright',
        'move_item': 'plus',
        'destroy_item': 'poof',
        'invalid_drag': 'notallowed',
    }

    def add_mousewheel(target, *frames, orient='y'):
        """Add events so scrolling anywhere in a frame will scroll a target.

        frame should be a sequence of any TK objects, like a Toplevel or Frame.
        Set orient to 'x' or 'y'.
        This is needed since different platforms handle mousewheel events
        differently - OS X needs the delta value passed unmodified.
        """
        scroll_func = getattr(target, orient + 'view_scroll')

        def mousewheel_handler(event):
            scroll_func(-event.delta, "units")
        for frame in frames:
            frame.bind('<MouseWheel>', mousewheel_handler, add='+')
elif LINUX:
    EVENTS = {
        'LEFT': '<Button-1>',
        'LEFT_DOUBLE': '<Double-Button-1>',
        'LEFT_CTRL': '<Control-Button-1>',
        'LEFT_SHIFT': '<Shift-Button-1>',
        'LEFT_RELEASE': '<ButtonRelease-1>',
        'LEFT_MOVE': '<B1-Motion>',

        'RIGHT': '<Button-3>',
        'RIGHT_DOUBLE': '<Double-Button-3>',
        'RIGHT_CTRL': '<Control-Button-3>',
        'RIGHT_SHIFT': '<Shift-Button-3>',
        'RIGHT_RELEASE': '<ButtonRelease-3>',
        'RIGHT_MOVE': '<B3-Motion>',

        'KEY_EXPORT': '<Control-e>',
        'KEY_SAVE_AS': '<Control-s>',
        'KEY_SAVE': '<Control-Shift-s>',
    }
    KEY_ACCEL = {
        'KEY_EXPORT': 'Ctrl-E',
        'KEY_SAVE': 'Ctrl-S',
        'KEY_SAVE_AS': 'Ctrl-Shift-S',
    }

    CURSORS = {
        'regular': 'arrow',
        'link': 'hand2',
        'wait': 'watch',
        'stretch_vert': 'sb_v_double_arrow',
        'stretch_horiz': 'sb_h_double_arrow',
        'move_item': 'plus',
        'destroy_item': 'x_cursor',
        'invalid_drag': 'no',
    }

    def add_mousewheel(target, *frames, orient='y'):
        """Add events so scrolling anywhere in a frame will scroll a target.

        frame should be a sequence of any TK objects, like a Toplevel or Frame.
        Set orient to 'x' or 'y'.
        This is needed since different platforms handle mousewheel events
        differently - Linux uses Button-4 and Button-5 events instead of
        a MouseWheel event.
        """
        scroll_func = getattr(target, orient + 'view_scroll')

        def scroll_up(_):
            scroll_func(-1, "units")

        def scroll_down(_):
            scroll_func(1, "units")

        for frame in frames:
            frame.bind('<Button-4>', scroll_up, add='+')
            frame.bind('<Button-5>', scroll_down, add='+')

if MAC:
    # On OSX, make left-clicks switch to a rightclick when control is held.
    def bind_leftclick(wid, func, add='+'):
        """On OSX, left-clicks are converted to right-clicks

        when control is held.
        """
        def event_handler(e):
            # e.state is a set of binary flags
            # Don't run the event if control is held!
            if e.state & 4 == 0:
                func()
        wid.bind(EVENTS['LEFT'], event_handler, add=add)

    def bind_leftclick_double(wid, func, add='+'):
        """On OSX, left-clicks are converted to right-clicks

        when control is held."""
        def event_handler(e):
            # e.state is a set of binary flags
            # Don't run the event if control is held!
            if e.state & 4 == 0:
                func()
        wid.bind(EVENTS['LEFT_DOUBLE'], event_handler, add=add)

    def bind_rightclick(wid, func):
        """On OSX, we need to bind to both rightclick and control-leftclick."""
        wid.bind(EVENTS['RIGHT'], func)
        wid.bind(EVENTS['LEFT_CTRL'], func)
else:
    def bind_leftclick(wid, func, add='+'):
        """Other systems just bind directly."""
        wid.bind(EVENTS['LEFT'], func, add=add)

    def bind_leftclick_double(wid, func, add='+'):
        """Other systems just bind directly."""
        wid.bind(EVENTS['LEFT_DOUBLE'], func, add=add)

    def bind_rightclick(wid, func, add='+'):
        """Other systems just bind directly."""
        wid.bind(EVENTS['RIGHT'], func, add=add)

USE_SIZEGRIP = not MAC  # On Mac, we don't want to use the sizegrip widget

BOOL_LOOKUP = {
    False: False,
    0: False,
    '0': False,
    'no': False,
    'false': False,
    'FALSE': False,
    'n': False,
    'f': False,

    1: True,
    True: True,
    '1': True,
    'yes': True,
    'true': True,
    'TRUE': True,
    'y': True,
    't': True,
}


class CONN_TYPES(Enum):
    """Possible connections when joining things together.

    Used for things like catwalks, and bottomless pit sides.
    """
    none = 0
    side = 1  # Points E
    straight = 2  # Points E-W
    corner = 3  # Points N-W
    triple = 4  # Points N-S-W
    all = 5  # Points N-S-E-W

N = "0 90 0"
S = "0 270 0"
E = "0 0 0"
W = "0 180 0"
# Lookup values for joining things together.
CONN_LOOKUP = {
    # N S  E  W : (Type, Rotation)
    (1, 0, 0, 0): (CONN_TYPES.side, N),
    (0, 1, 0, 0): (CONN_TYPES.side, S),
    (0, 0, 1, 0): (CONN_TYPES.side, E),
    (0, 0, 0, 1): (CONN_TYPES.side, W),

    (1, 1, 0, 0): (CONN_TYPES.straight, S),
    (0, 0, 1, 1): (CONN_TYPES.straight, E),

    (0, 1, 0, 1): (CONN_TYPES.corner, N),
    (1, 0, 1, 0): (CONN_TYPES.corner, S),
    (1, 0, 0, 1): (CONN_TYPES.corner, E),
    (0, 1, 1, 0): (CONN_TYPES.corner, W),

    (0, 1, 1, 1): (CONN_TYPES.triple, N),
    (1, 0, 1, 1): (CONN_TYPES.triple, S),
    (1, 1, 0, 1): (CONN_TYPES.triple, E),
    (1, 1, 1, 0): (CONN_TYPES.triple, W),

    (1, 1, 1, 1): (CONN_TYPES.all, E),

    (0, 0, 0, 0): (CONN_TYPES.none, E),
}

del N, S, E, W


def clean_line(line: str):
    """Removes extra spaces and comments from the input."""
    if isinstance(line, bytes):
        line = line.decode()  # convert bytes to strings if needed
    if '//' in line:
        line = line.split('//', 1)[0]
    return line.strip()


FILE_CHARS = set(string.ascii_letters + string.digits + '-_ .|')


def is_plain_text(name, valid_chars=FILE_CHARS):
    """Check to see if any characters are not in the whitelist.

    """
    for char in name:
        if char not in valid_chars:
            return False
    return True


def whitelist(string, valid_chars=FILE_CHARS, rep_char='_'):
    """Replace any characters not in the whitelist with the replacement char."""
    chars = list(string)
    for ind, char in enumerate(chars):
        if char not in valid_chars:
            chars[ind] = rep_char
    return ''.join(chars)


def blacklist(string, invalid_chars='', rep_char='_'):
    """Replace any characters in the blacklist with the replacement char."""
    chars = list(string)
    for ind, char in enumerate(chars):
        if char in invalid_chars:
            chars[ind] = rep_char
    return ''.join(chars)


def get_indent(line: str):
    """Return the whitespace which this line starts with.

    """
    white = []
    for char in line:
        if char in ' \t':
            white.append(char)
        else:
            return ''.join(white)


def con_log(*text):
    """Log text to the screen.

    Portal 2 needs the flush in order to receive VBSP/VRAD's logged
    output into the developer console and update the progress bars.
    """
    print(*text, flush=True)


def bool_as_int(val: bool):
    """Convert a True/False value into '1' or '0'.

    Valve uses these strings for True/False in editoritems and other
    config files.
    """
    if val:
        return '1'
    else:
        return '0'


def conv_bool(val: Union[str, bool, None], default=False):
    """Converts a string to a boolean, using a default if it fails.

    Accepts any of '0', '1', 'false', 'true', 'yes', 'no'.
    If Val is None, this always returns the default.
    0, 1, True and False will be passed through unchanged.
    """
    if val is None:
        return default
    try:
        # Lookup bools, ints, and normal strings
        return BOOL_LOOKUP[val]
    except KeyError:
        # Try again with casefolded strings
        return BOOL_LOOKUP.get(val.casefold(), default)


def conv_float(val, default=0.0):
    """Converts a string to an float, using a default if it fails.

    """
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def conv_int(val: str, default=0):
    """Converts a string to an integer, using a default if it fails.

    """
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def parse_str(val: Union[str, 'Vec'], x=0.0, y=0.0, z=0.0) -> Tuple[int, int, int]:
    """Convert a string in the form '(4 6 -4)' into a set of floats.

     If the string is unparsable, this uses the defaults (x,y,z).
     The string can start with any of the (), {}, [], <> bracket
     types.

     If the 'string' is actually a Vec, the values will be returned.
     """
    if isinstance(val, Vec):
        return val.x, val.y, val.z

    try:
        str_x, str_y, str_z = val.split(' ')
    except ValueError:
        return x, y, z

    if str_x[0] in '({[<':
        str_x = str_x[1:]
    if str_z[-1] in ')}]>':
        str_z = str_z[:-1]
    try:
        return (
            float(str_x),
            float(str_y),
            float(str_z),
        )
    except ValueError:
        return x, y, z


def iter_grid(
        max_x: int,
        max_y: int,
        min_x: int=0,
        min_y: int=0,
        stride: int=1,
        ) -> Iterator[Tuple[int, int]]:
    """Loop over a rectangular grid area."""
    for x in range(min_x, max_x, stride):
        for y in range(min_y, max_y, stride):
            yield x, y


DISABLE_ADJUST = False


def adjust_inside_screen(x, y, win, horiz_bound=14, vert_bound=45):
    """Adjust a window position to ensure it fits inside the screen."""
    if DISABLE_ADJUST:  # Allow disabling this adjustment
        return x, y     # for multi-window setups
    max_x = win.winfo_screenwidth() - win.winfo_width() - horiz_bound
    max_y = win.winfo_screenheight() - win.winfo_height() - vert_bound

    if x < horiz_bound:
        x = horiz_bound
    elif x > max_x:
        x = max_x

    if y < vert_bound:
        y = vert_bound
    elif y > max_y:
        y = max_y
    return x, y


def center_win(window, parent=None):
    """Center a subwindow to be inside a parent window."""
    if parent is None:
        parent = window.nametowidget(window.winfo_parent())

    x = parent.winfo_rootx() + (parent.winfo_width()-window.winfo_width())//2
    y = parent.winfo_rooty() + (parent.winfo_height()-window.winfo_height())//2

    x, y = adjust_inside_screen(x, y, window)

    window.geometry('+' + str(x) + '+' + str(y))


def append_bothsides(deq):
    """Alternately add to each side of a deque."""
    while True:
        deq.append((yield))
        deq.appendleft((yield))


def fit(dist, obj):
    """Figure out the smallest number of parts to stretch a distance."""
    # If dist is a float the outputs will become floats as well
    # so ensure it's an int.
    dist = int(dist)
    if dist <= 0:
        return []
    orig_dist = dist
    smallest = obj[-1]
    items = collections.deque()

    # We use this so the small sections appear on both sides of the area.
    adder = append_bothsides(items)
    next(adder)
    while dist >= smallest:
        for item in obj:
            if item <= dist:
                adder.send(item)
                dist -= item
                break
    if dist > 0:
        adder.send(dist)

    assert sum(items) == orig_dist
    return list(items)  # Dump the deque


def restart_app():
    """Restart this python application.

    This will not return!
    """
    import os, sys
    # sys.executable is the program which ran us - when frozen,
    # it'll our program.
    # We need to add the program to the arguments list, since python
    # strips that off.
    args = [sys.executable] + sys.argv
    getLogger(__name__).info(
        'Restarting using "{}", with args {!r}',
        sys.executable,
        args,
    )
    logging.shutdown()
    os.execv(sys.executable, args)


def set_readonly(file):
    """Make the given file read-only."""
    # Get the old flags
    flags = os.stat(file).st_mode
    # Make it read-only
    os.chmod(
        file,
        flags & ~
        stat.S_IWUSR & ~
        stat.S_IWGRP & ~
        stat.S_IWOTH
    )


def unset_readonly(file):
    """Set the writeable flag on a file."""
    # Get the old flags
    flags = os.stat(file).st_mode
    # Make it writeable
    os.chmod(
        file,
        flags |
        stat.S_IWUSR |
        stat.S_IWGRP |
        stat.S_IWOTH
    )

class LogMessage:
    """Allow using str.format() in logging messages.

    The __str__() method performs the joining.
    """
    def __init__(self, fmt, args, kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs
        self.has_args = kwargs or args

    def format_msg(self):
        # Only format if we have arguments!
        # That way { or } can be used in regular messages.
        if self.has_args:
            f = self.fmt = str(self.fmt).format(*self.args, **self.kwargs)

            # Don't repeat the formatting
            del self.args, self.kwargs
            self.has_args = False
            return f
        else:
            return str(self.fmt)

    def __str__(self):
        """Format the string, and add an ASCII indent."""
        msg = self.format_msg()

        if '\n' not in msg:
            return msg

        # For multi-line messages, add an indent so they're associated
        # with the logging tag.
        lines = msg.split('\n')
        if lines[-1].isspace():
            # Strip last line if it's blank
            del lines[-1]
        # '|' beside all the lines, '|_ beside the last. Add an empty
        # line at the end.
        return '\n | '.join(lines[:-1]) + '\n |_' + lines[-1] + '\n'


class LoggerAdapter(logging.LoggerAdapter):
    """Fix loggers to use str.format().

    """
    def __init__(self, logger: logging.Logger, alias=None):
        # Alias is a replacement module name for log messages.
        self.alias = alias
        super(LoggerAdapter, self).__init__(logger, extra={})

    def log(self, level, msg, *args, exc_info=None, stack_info=False, **kwargs):
        """This version of .log() is for str.format() compatibility.

        The message is wrapped in a LogMessage object, which is given the
        args and kwargs
        """
        if self.isEnabledFor(level):
            self.logger._log(
                level,
                LogMessage(msg, args, kwargs),
                (), # No positional arguments, we do the formatting through
                # LogMessage..
                # Pull these two arguments out of kwargs, so they can be set..
                exc_info=exc_info,
                stack_info=stack_info,
                extra={'alias': self.alias},
            )

class NewLogRecord(logging.getLogRecordFactory()):
    """Allow passing an alias for log modules."""

    def getMessage(self):
        """We have to hook here to change the value of .module.

        It's called just before the formatting call is made.
        """
        if self.alias is not None:
            self.module = self.alias
        return str(self.msg)
logging.setLogRecordFactory(NewLogRecord)


def init_logging(filename: str=None) -> logging.Logger:
    """Setup the logger and logging handlers.

    If filename is set, all logs will be written to this file.
    """
    global short_log_format, long_log_format
    global stderr_loghandler, stdout_loghandler, file_loghandler
    import logging
    from logging import handlers
    import sys, io, os

    logger = logging.getLogger('BEE2')
    logger.setLevel(logging.DEBUG)

    # Put more info in the log file, since it's not onscreen.
    long_log_format = logging.Formatter(
        '[{levelname}] {module}.{funcName}(): {message}',
        style='{',
    )
    # Console messages, etc.
    short_log_format = logging.Formatter(
        # One letter for level name
        '[{levelname[0]}] {module}: {message}',
        style='{',
    )

    if filename is not None:
        # Make the directories the logs are in, if needed.
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # The log contains DEBUG and above logs.
        # We rotate through logs of 500kb each, so it doesn't increase too much.
        log_handler = handlers.RotatingFileHandler(
            filename,
            maxBytes=500 * 1024,
            backupCount=10,
        )
        log_handler.setLevel(logging.DEBUG)
        log_handler.setFormatter(long_log_format)

        logger.addHandler(log_handler)

    # This is needed for multiprocessing, since it tries to flush stdout.
    # That'll fail if it is None.
    class NullStream(io.IOBase):
        """A stream object that discards all data."""
        def __init__(self):
            super(NullStream, self).__init__()

        @staticmethod
        def write(self, *args, **kwargs):
            pass

        @staticmethod
        def read(*args, **kwargs):
            return ''

    if sys.stdout:
        stdout_loghandler = logging.StreamHandler(sys.stdout)
        stdout_loghandler.setLevel(logging.INFO)
        stdout_loghandler.setFormatter(short_log_format)
        logger.addHandler(stdout_loghandler)

        if sys.stderr:
            def ignore_warnings(record: logging.LogRecord):
                """Filter out messages higher than WARNING.

                Those are handled by stdError, and we don't want duplicates.
                """
                return record.levelno < logging.WARNING
            stdout_loghandler.addFilter(ignore_warnings)
    else:
        sys.stdout = NullStream()

    if sys.stderr:
        stderr_loghandler = logging.StreamHandler(sys.stderr)
        stderr_loghandler.setLevel(logging.WARNING)
        stderr_loghandler.setFormatter(short_log_format)
        logger.addHandler(stderr_loghandler)
    else:
        sys.stderr = NullStream()

    # Use the exception hook to report uncaught exceptions, and finalise the
    # logging system.
    old_except_handler = sys.__excepthook__

    def except_handler(*exc_info):
        """Log uncaught exceptions."""
        logger._log(
            level=logging.ERROR,
            msg='Uncaught Exception:',
            args=(),
            exc_info=exc_info,
        )
        logging.shutdown()
        # Call the original handler - that prints to the normal console.
        old_except_handler()

    sys.__excepthook__ = except_handler

    return LoggerAdapter(logger)


def getLogger(name: str='', alias: str=None) -> logging.Logger:
    """Get the named logger object.

    This puts the logger into the BEE2 namespace, and wraps it to
    use str.format() instead of % formatting.
    If set, alias is the name to show for the module.
    """
    if name:
        return LoggerAdapter(logging.getLogger('BEE2.' + name), alias)
    else:  # Allow retrieving the main logger.
        return LoggerAdapter(logging.getLogger('BEE2'), alias)


class EmptyMapping(abc.MutableMapping):
    """A Mapping class which is always empty.

    Any modifications will be ignored.
    This is used for default arguments, since it then ensures any changes
    won't be kept, as well as allowing default.items() calls and similar.
    """
    __slots__ = []

    def __call__(self):
        # Just in case someone tries to instantiate this
        return self

    def __getitem__(self, item):
        raise KeyError

    def __contains__(self, item):
        return False

    def get(self, item, default=None):
        return default

    def __bool__(self):
        return False

    def __next__(self):
        raise StopIteration

    def __len__(self):
        return 0

    def __iter__(self):
        return self

    items = values = keys = __iter__

    # Mutable functions
    setdefault = get

    def update(*args, **kwds):
        pass

    __setitem__ = __delitem__ = clear = update

    __marker = object()

    def pop(self, key, default=__marker):
        if default is self.__marker:
            raise KeyError
        return default

    def popitem(self):
        raise KeyError

EmptyMapping = EmptyMapping()  # We only need the one instance


class AtomicWriter:
    """Atomically overwrite a file.

    Use as a context manager - the returned temporary file
    should be written to. When cleanly exiting, the file will be transfered.
    If an exception occurs in the body, the temporary data will be discarded.

    This is not reentrant, but can be repeated - starting the context manager
    clears the file.
    """
    def __init__(self, filename, is_bytes=False):
        """Create an AtomicWriter.
        is_bytes sets text or bytes writing mode. The file is always writable.
        """
        self.filename = filename
        self.dir = os.path.dirname(filename)
        self.is_bytes = is_bytes
        self.temp = None

    def make_tempfile(self):
        """Create the temporary file object."""
        if self.temp is not None:
            # Already open - close and delete the current file.
            self.temp.close()
            os.remove(self.temp.name)

        # Create folders if needed..
        os.makedirs(self.dir, exist_ok=True)

        self.temp = tempfile.NamedTemporaryFile(
            mode='wb' if self.is_bytes else 'wt',
            dir=self.dir,
            delete=False,
        )

    def __enter__(self):
        """Delagate to the underlying temporary file handler."""
        self.make_tempfile()
        return self.temp.__enter__()

    def __exit__(self, exc_type, exc_value, tback):
        # Pass to tempfile, which also closes().
        temp_path = self.temp.name
        self.temp.__exit__(exc_type, exc_value, tback)
        self.temp = None
        if exc_type is not None:
            # An exception occured, clean up.
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass
        else:
            # No exception, commit changes
            os.replace(temp_path, self.filename)

        return False  # Don't cancel the exception.


Vec_tuple = collections.namedtuple('Vec_tuple', ['x', 'y', 'z'])

# Use template code to reduce duplication in the various magic number methods.

_VEC_ADDSUB_TEMP = '''
def __{func}__(self, other):
    """{op} operation.

    This additionally works on scalars (adds to all axes).
    """
    if isinstance(other, Vec):
        return Vec(
            self.x {op} other.x,
            self.y {op} other.y,
            self.z {op} other.z,
        )
    try:
        if isinstance(other, tuple):
            x = self.x {op} other[0]
            y = self.y {op} other[1]
            z = self.z {op} other[2]
        else:
            x = self.x {op} other
            y = self.y {op} other
            z = self.z {op} other
    except TypeError:
        return NotImplemented
    else:
        return Vec(x, y, z)

def __r{func}__(self, other):
    """{op} operation with reversed operands.

    This additionally works on scalars (adds to all axes).
    """
    if isinstance(other, Vec):
        return Vec(
            other.x {op} self.x,
            other.y {op} self.y,
            other.z {op} self.z,
        )
    try:
        if isinstance(other, tuple):
            x = other[0] {op} self.x
            y = other[1] {op} self.y
            z = other[2] {op} self.z
        else:
            x = other {op} self.x
            y = other {op} self.y
            z = other {op} self.z
    except TypeError:
        return NotImplemented
    else:
        return Vec(x, y, z)

def __i{func}__(self, other):
    """{op}= operation.

    Like the normal one except without duplication.
    """
    if isinstance(other, Vec):
        self.x {op}= other.x
        self.y {op}= other.y
        self.z {op}= other.z
    elif isinstance(other, tuple):
        self.x {op}= other[0]
        self.y {op}= other[1]
        self.z {op}= other[2]
    else:
        orig = self.x, self.y, self.z
        try:
            self.x {op}= other
            self.y {op}= other
            self.z {op}= other
        except TypeError as e:
            self.x, self.y, self.z = orig
            raise TypeError(
                'Cannot add {{}} to Vector!'.format(type(other))
            ) from e
    return self
'''

# Multiplication and division doesn't work with two vectors - use dot/cross
# instead.

_VEC_MULDIV_TEMP = '''
def __{func}__(self, other):
    """Vector {op} scalar operation."""
    if isinstance(other, Vec):
        raise TypeError("Cannot {pretty} 2 Vectors.")
    else:
        try:
            return Vec(
                self.x {op} other,
                self.y {op} other,
                self.z {op} other,
            )
        except TypeError:
            return NotImplemented

def __r{func}__(self, other):
    """scalar {op} Vector operation."""
    if isinstance(other, Vec):
        raise TypeError("Cannot {pretty} 2 Vectors.")
    else:
        try:
            return Vec(
                other {op} self.x,
                other {op} self.y,
                other {op} self.z,
            )
        except TypeError:
            return NotImplemented


def __i{func}__(self, other):
    """{op}= operation.

    Like the normal one except without duplication.
    """
    if isinstance(other, Vec):
        raise TypeError("Cannot {pretty} 2 Vectors.")
    else:
        self.x {op}= other
        self.y {op}= other
        self.z {op}= other
        return self
'''


class Vec:
    """A 3D Vector. This has most standard Vector functions.

    Many of the functions will accept a 3-tuple for comparison purposes.
    """
    __slots__ = ('x', 'y', 'z')

    INV_AXIS = {
        'x': 'yz',
        'y': 'xz',
        'z': 'xy',

        ('y', 'z'): 'x',
        ('x', 'z'): 'y',
        ('x', 'y'): 'z',
    }

    def __init__(self, x=0.0, y=0.0, z=0.0):
        """Create a Vector.

        All values are converted to Floats automatically.
        If no value is given, that axis will be set to 0.
        A sequence can be passed in (as the x argument), which will use
        the three args as x/y/z.

        :type x: int | float | Vec | list[str | int | float]
        """
        if isinstance(x, (int, float)):
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)
        else:
            it = iter(x)
            self.x = float(next(it, 0.0))
            self.y = float(next(it, y))
            self.z = float(next(it, z))

    def copy(self):
        return Vec(self.x, self.y, self.z)

    @classmethod
    def from_str(cls, val: Union[str, 'Vec'], x=0.0, y=0.0, z=0.0):
        """Convert a string in the form '(4 6 -4)' into a Vector.

         If the string is unparsable, this uses the defaults (x,y,z).
         The string can start with any of the (), {}, [], <> bracket
         types.

         If the value is already a vector, a copy will be returned.
         """

        x, y, z = parse_str(val, x, y, z)
        return cls(x, y, z)

    def mat_mul(self, matrix):
        """Multiply this vector by a 3x3 rotation matrix.

        Used for Vec.rotate().
        """
        a, b, c, d, e, f, g, h, i = matrix
        x, y, z = self.x, self.y, self.z

        self.x = (x * a) + (y * b) + (z * c)
        self.y = (x * d) + (y * e) + (z * f)
        self.z = (x * g) + (y * h) + (z * i)

    def rotate(self, pitch=0.0, yaw=0.0, roll=0.0, round_vals=True):
        """Rotate a vector by a Source rotational angle.
        Returns the vector, so you can use it in the form
        val = Vec(0,1,0).rotate(p, y, r)

        If round is True, all values will be rounded to 3 decimals
        (since these calculations always have small inprecision.)
        """
        # pitch is in the y axis
        # yaw is the z axis
        # roll is the x axis

        rad_pitch = math.radians(pitch)
        rad_yaw = math.radians(yaw)
        rad_roll = math.radians(roll)
        cos_p = math.cos(rad_pitch)
        cos_y = math.cos(rad_yaw)
        cos_r = math.cos(rad_roll)

        sin_p = math.sin(rad_pitch)
        sin_y = math.sin(rad_yaw)
        sin_r = math.sin(rad_roll)

        mat_roll = (  # X
            1, 0, 0,
            0, cos_r, -sin_r,
            0, sin_r, cos_r,
        )
        mat_yaw = (  # Z
            cos_y, -sin_y, 0,
            sin_y, cos_y, 0,
            0, 0, 1,
        )

        mat_pitch = (  # Y
            cos_p, 0, sin_p,
            0, 1, 0,
            -sin_p, 0, cos_p,
        )

        # Need to do transformations in roll, pitch, yaw order
        self.mat_mul(mat_roll)
        self.mat_mul(mat_pitch)
        self.mat_mul(mat_yaw)

        if round_vals:
            self.x = round(self.x, 3)
            self.y = round(self.y, 3)
            self.z = round(self.z, 3)

        return self

    def rotate_by_str(self, ang, pitch=0.0, yaw=0.0, roll=0.0, round_vals=True):
        """Rotate a vector, using a string instead of a vector."""
        pitch, yaw, roll = parse_str(ang, pitch, yaw, roll)
        return self.rotate(
            pitch,
            yaw,
            roll,
            round_vals,
        )

    @staticmethod
    def bbox(*points: 'Vec') -> Tuple['Vec', 'Vec']:
        """Compute the bounding box for a set of points.

        Pass either several Vecs, or an iterable of Vecs.
        """
        if len(points) == 1:  # Allow passing a single iterable
            (first, *points), = points
        else:
            first, *points = points
        bbox_min = first.copy()
        bbox_max = first.copy()
        for point in points:
            bbox_min.min(point)
            bbox_max.max(point)
        return bbox_min, bbox_max

    def axis(self):
        """For a normal vector, return the axis it is on.

        This will not function correctly if not a on-axis normal vector!
        """
        return (
            'x' if self.x != 0 else
            'y' if self.y != 0 else
            'z'
        )

    def to_angle(self, roll=0):
        """Convert a normal to a Source Engine angle."""
        # Pitch is applied first, so we need to reconstruct the x-value
        horiz_dist = math.sqrt(self.x ** 2 + self.y ** 2)
        return Vec(
            math.degrees(math.atan2(-self.z, horiz_dist)),
            math.degrees(math.atan2(self.y, self.x)) % 360,
            roll,
        )

    def __abs__(self):
        """Performing abs() on a Vec takes the absolute value of all axes."""
        return Vec(
            abs(self.x),
            abs(self.y),
            abs(self.z),
        )

    funcname = op = pretty = None

    # Use exec() to generate all the number magic methods. This reduces code
    # duplication since they're all very similar.

    for funcname, op in (('add', '+'), ('sub', '-')):
        exec(
            _VEC_ADDSUB_TEMP.format(func=funcname, op=op),
            globals(),
            locals(),
        )

    for funcname, op, pretty in (
            ('mul', '*', 'multiply'),
            ('truediv', '/', 'divide'),
            ('floordiv', '//', 'floor-divide'),
            ('mod', '%', 'modulus'),
    ):
        exec(
            _VEC_MULDIV_TEMP.format(func=funcname, op=op, pretty=pretty),
            globals(),
            locals(),
        )

    del funcname, op, pretty

    # Divmod is entirely unique.
    def __divmod__(self, other: float) -> Tuple['Vec', 'Vec']:
        """Divide the vector by a scalar, returning the result and remainder."""
        if isinstance(other, Vec):
            raise TypeError("Cannot divide 2 Vectors.")
        else:
            try:
                x1, x2 = divmod(self.x, other)
                y1, y2 = divmod(self.y, other)
                z1, z2 = divmod(self.z, other)
            except TypeError:
                return NotImplemented
            else:
                return Vec(x1, y1, z1), Vec(x2, y2, z2)

    def __rdivmod__(self, other: float) -> Tuple['Vec', 'Vec']:
        """Divide a scalar by a vector, returning the result and remainder."""
        if isinstance(other, Vec):
            return NotImplemented
        else:
            try:
                x1, x2 = divmod(other, self.x)
                y1, y2 = divmod(other, self.y)
                z1, z2 = divmod(other, self.z)
            except TypeError:
                return NotImplemented
            else:
                return Vec(x1, y1, z1), Vec(x2, y2, z2)

    def __bool__(self) -> bool:
        """Vectors are True if any axis is non-zero."""
        return self.x != 0 or self.y != 0 or self.z != 0

    def __eq__(
            self,
            other: Union['Vec', tuple, SupportsFloat],
            ) -> bool:
        """== test.

        Two Vectors are compared based on the axes.
        A Vector can be compared with a 3-tuple as if it was a Vector also.
        Otherwise the other value will be compared with the magnitude.
        """
        if isinstance(other, Vec):
            return other.x == self.x and other.y == self.y and other.z == self.z
        elif isinstance(other, tuple):
            return (
                self.x == other[0] and
                self.y == other[1] and
                self.z == other[2]
            )
        else:
            try:
                return self.mag() == float(other)
            except ValueError:
                return NotImplemented

    def __ne__(
            self,
            other: Union['Vec', tuple, SupportsFloat],
            ) -> bool:
        """!= test.

        Two Vectors are compared based on the axes.
        A Vector can be compared with a 3-tuple as if it was a Vector also.
        Otherwise the other value will be compared with the magnitude.
        """
        if isinstance(other, Vec):
            return other.x != self.x or other.y != self.y or other.z != self.z
        elif isinstance(other, tuple):
            return (
                self.x != other[0] or
                self.y != other[1] or
                self.z != other[2]
            )
        else:
            try:
                return self.mag() != float(other)
            except ValueError:
                return NotImplemented

    def __lt__(
            self,
            other: Union['Vec', abc.Sequence, SupportsFloat],
            ) -> bool:
        """A<B test.

        Two Vectors are compared based on the axes.
        A Vector can be compared with a 3-tuple as if it was a Vector also.
        Otherwise the other value will be compared with the magnitude.
        """
        if isinstance(other, Vec):
            return (
                self.x < other.x and
                self.y < other.y and
                self.z < other.z
            )
        elif isinstance(other, tuple):
            return (
                self.x < other[0] and
                self.y < other[1] and
                self.z < other[2]
            )
        else:
            try:
                return self.mag() < float(other)
            except ValueError:
                return NotImplemented

    def __le__(
            self,
            other: Union['Vec', tuple, SupportsFloat],
            ) -> bool:
        """A<=B test.

        Two Vectors are compared based on the axes.
        A Vector can be compared with a 3-tuple as if it was a Vector also.
        Otherwise the other value will be compared with the magnitude.
        """
        if isinstance(other, Vec):
            return (
                self.x <= other.x and
                self.y <= other.y and
                self.z <= other.z
            )
        elif isinstance(other, tuple):
            return (
                self.x <= other[0] and
                self.y <= other[1] and
                self.z <= other[2]
            )
        else:
            try:
                return self.mag() <= float(other)
            except ValueError:
                return NotImplemented

    def __gt__(
            self,
            other: Union['Vec', tuple, SupportsFloat],
            ) -> bool:
        """A>B test.

        Two Vectors are compared based on the axes.
        A Vector can be compared with a 3-tuple as if it was a Vector also.
        Otherwise the other value will be compared with the magnitude.
        """
        if isinstance(other, Vec):
            return (
                self.x > other.x and
                self.y > other.y and
                self.z > other.z
            )
        elif isinstance(other, tuple):
            return (
                self.x > other[0] and
                self.y > other[1] and
                self.z > other[2]
            )
        else:
            try:
                return self.mag() > float(other)
            except ValueError:
                return NotImplemented

    def __ge__(
            self,
            other: Union['Vec', tuple, SupportsFloat],
    ) -> bool:
        """A>=B test.

        Two Vectors are compared based on the axes.
        A Vector can be compared with a 3-tuple as if it was a Vector also.
        Otherwise the other value will be compared with the magnitude.
        """
        if isinstance(other, Vec):
            return (
                self.x >= other.x and
                self.y >= other.y and
                self.z >= other.z
            )
        elif isinstance(other, tuple):
            return (
                self.x >= other[0] and
                self.y >= other[1] and
                self.z >= other[2]
            )
        else:
            try:
                return self.mag() >= float(other)
            except ValueError:
                return NotImplemented

    def max(self, other: Union['Vec', Vec_tuple]):
        """Set this vector's values to the maximum of the two vectors."""
        if self.x < other.x:
            self.x = other.x
        if self.y < other.y:
            self.y = other.y
        if self.z < other.z:
            self.z = other.z

    def min(self, other: Union['Vec', Vec_tuple]):
        """Set this vector's values to be the minimum of the two vectors."""
        if self.x > other.x:
            self.x = other.x
        if self.y > other.y:
            self.y = other.y
        if self.z > other.z:
            self.z = other.z

    def __round__(self, n=0):
        return Vec(
            round(self.x, n),
            round(self.y, n),
            round(self.z, n),
        )

    def mag(self):
        """Compute the distance from the vector and the origin."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def join(self, delim=', '):
        """Return a string with all numbers joined by the passed delimiter.

        This strips off the .0 if no decimal portion exists.
        """
        # :g strips the .0 off of floats if it's an integer.
        return '{x:g}{delim}{y:g}{delim}{z:g}'.format(
            x=self.x,
            y=self.y,
            z=self.z,
            delim=delim,
        )

    def __str__(self):
        """Return the values, separated by spaces.

        This is the main format in Valve's file formats.
        """
        return "{:g} {:g} {:g}".format(self.x, self.y, self.z)

    def __repr__(self):
        """Code required to reproduce this vector."""
        return self.__class__.__name__ + "(" + self.join() + ")"

    def __iter__(self) -> Iterator[float]:
        """Allow iterating through the dimensions."""
        yield self.x
        yield self.y
        yield self.z

    def __getitem__(self, ind: Union[str, int]) -> float:
        """Allow reading values by index instead of name if desired.

        This accepts either 0,1,2 or 'x','y','z' to read values.
        Useful in conjunction with a loop to apply commands to all values.
        """
        if ind == 0 or ind == "x":
            return self.x
        elif ind == 1 or ind == "y":
            return self.y
        elif ind == 2 or ind == "z":
            return self.z
        raise KeyError('Invalid axis: {!r}'.format(ind))

    def __setitem__(self, ind: Union[str, int], val: float):
        """Allow editing values by index instead of name if desired.

        This accepts either 0,1,2 or 'x','y','z' to edit values.
        Useful in conjunction with a loop to apply commands to all values.
        """
        if ind == 0 or ind == "x":
            self.x = float(val)
        elif ind == 1 or ind == "y":
            self.y = float(val)
        elif ind == 2 or ind == "z":
            self.z = float(val)
        else:
            raise KeyError('Invalid axis: {!r}'.format(ind))

    def other_axes(self, axis: str) -> Tuple[float, float]:
        """Get the values for the other two axes."""
        if axis == 'x':
            return self.y, self.z
        if axis == 'y':
            return self.x, self.z
        if axis == 'z':
            return self.x, self.y

    def as_tuple(self):
        """Return the Vector as a tuple."""
        return Vec_tuple(self.x, self.y, self.z)

    def len_sq(self):
        """Return the magnitude squared, which is slightly faster."""
        return self.x**2 + self.y**2 + self.z**2

    def __len__(self):
        """The len() of a vector is the number of non-zero axes."""
        return (
            (self.x != 0) +
            (self.y != 0) +
            (self.z != 0)
        )

    def __contains__(self, val):
        """Check to see if an axis is set to the given value.
        """
        return val == self.x or val == self.y or val == self.z

    def __neg__(self):
        """The inverted form of a Vector has inverted axes."""
        return Vec(-self.x, -self.y, -self.z)

    def __pos__(self):
        """+ on a Vector simply copies it."""
        return Vec(self.x, self.y, self.z)

    def norm(self) -> 'Vec':
        """Normalise the Vector.

         This is done by transforming it to have a magnitude of 1 but the same
         direction.
         The vector is left unchanged if it is equal to (0,0,0)
         """
        if self.x == 0 and self.y == 0 and self.z == 0:
            # Don't do anything for this - otherwise we'd get division
            # by zero errors - we want this to be a valid normal!
            return self.copy()
        else:
            # Adding 0 clears -0 values - we don't want those.
            val = self / self.mag()
            val += 0
            return val

    def dot(self, other):
        """Return the dot product of both Vectors."""
        return (
            self.x * other.x +
            self.y * other.y +
            self.z * other.z
        )

    def cross(self, other):
        """Return the cross product of both Vectors."""
        return Vec(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def localise(
            self,
            origin: Union['Vec', tuple],
            angles: Union['Vec', tuple]=None,
    ):
        """Shift this point to be local to the given position and angles

        """
        if angles is not None:
            self.rotate(angles[0], angles[1], angles[2])
        self.__iadd__(origin)

    def norm_mask(self, normal: 'Vec') -> 'Vec':
        """Subtract the components of this vector not in the direction of the normal.

        If the normal is axis-aligned, this will zero out the other axes.
        If not axis-aligned, it will do the equivalent.
        """
        normal = normal.norm()
        return normal * self.dot(normal)

    len = mag
    mag_sq = len_sq
