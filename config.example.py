"""
Configuration options for the IRC bot.
"""

from modules.ddg import DuckDuckGo
from modules.deavmicomedy import deavmicomedy
from modules.reversed import mkreversed
from modules.rot13 import rot13
from modules.sedbot import SedBot
from modules.translate import Translate
from modules.urltitle import UrlTitle

duckduckgo = DuckDuckGo()
sedbot = SedBot()
translate = Translate()
urltitle = UrlTitle()

SERVER_ADDR = "fdfb:1a20:a9bf:1000::7ab8"
SERVER_PORT = 6667
SERVER_PASS = "none"
SERVER_NICK = "ranybottyforrnb"
NICKSERV_PASS = None
CHANNELS_TO_JOIN = ["#rany2", "#general"]
# Order matters.
MODULES = [
    # These are commands and they must be specified first.
    sedbot.sed,
    duckduckgo.duckduckgo,
    deavmicomedy,
    rot13,
    mkreversed,
    translate.translate,
    # This function will always be run.
    urltitle.urltitle,
]
