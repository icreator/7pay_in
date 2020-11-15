from core import *

try:
    import version
    __version__ = version.version

except ImportError:
    __version__ = 'nobuild'
