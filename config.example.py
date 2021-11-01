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
# Order matters.
MODULES = [
    # These are commands and they must be specified first.
    modules.mkdeavmicomedy,
    modules.mkreversed,
    modules.mkrot13,
    modules.mkreversed,
    modules.mktranslate,
    # This function will always be run.
    modules.mkurltitle,
]
