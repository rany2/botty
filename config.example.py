"""
Configuration options for the IRC bot.
"""

import modules

SERVER_ADDR = "fdfb:1a20:a9bf:1000::7ab8"
SERVER_PORT = 6667
SERVER_PASS = "none"
SERVER_NICK = "ranybottyforrnb"
NICKSERV_PASS = None
CHANNELS_TO_JOIN = ["#rany2", "#general"]
MODULES = [
    modules.mktranslate,
    modules.mkdeavmicomedy,
    modules.mkrot13,
    modules.mkurltitle,
]
