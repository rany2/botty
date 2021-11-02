"""
translate is a module for botty that translates text.
"""

import json
import urllib.parse

import requests
from regexes import *


class Translate:
    """
    Translate is a class that translates text to the specified language
    """
    def __init__(self):
        """
        __init__ is the constructor for Translate
        """
        self.session = requests.Session()

    def _translate(self, text, to_lang="en"):
        """
        _translate translates text to the specified language

        Args:
            text (str): text to translate
            to_lang (str): language to translate to

        Returns:
            str: translated text
        """
        url = f"https://translate.google.com/translate_a/single?client=gtx&sl=auto&tl={urllib.parse.quote_plus(to_lang)}&dt=t&q={urllib.parse.quote_plus(text)}"
        response = self.session.get(url)
        data = json.loads(response.text)
        new_data = ""
        for iter_data in data[0]:
            new_data += f"{iter_data[0]}"
        return new_data

    def translate(self, nick, source, privmsg, netmask, is_channel, send_message):
        """
        mktranslate translates a message into a different language.

        Args:
            nick (str): the nick of the user who sent the message
            source (str): the channel or nick the message came from
            privmsg (str): the message
            netmask (str): the netmask of the user who sent the message
            is_channel (bool): whether or not the message was sent in a channel
            send_message (function): a function used to send a message to the correct location

        Returns:
            None if translate was not used, True if it was used
        """
        ret = None
        if privmsg.startswith(".tr ") or privmsg.startswith(".tr:"):
            if privmsg.startswith(".tr:"):
                privmsg = privmsg[len(".tr") :]
                privmsg = privmsg.split(" ")
                tolang = privmsg[0][1:]
                text_to_trans = ircspecial.sub("", " ".join(privmsg[1:]))
            else:
                text_to_trans = ircspecial.sub("", privmsg[len(".tr ") :])
                tolang = "en"
            transed = f"{self._translate(text_to_trans, tolang)}"
            if is_channel:
                send_message(f"{nick}, {transed}", source)
            else:
                send_message(f"{transed}", source)
            ret = True
        return ret
