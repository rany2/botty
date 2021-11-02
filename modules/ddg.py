"""
DDG module for botty.
"""

import urllib.parse
import requests

from regexes import ircspecial


class DuckDuckGo:
    """
    DuckDuckGo is a class that contains functions for searching DuckDuckGo
    and returning the first result.
    """

    def __init__(self):
        """
        __init__ initializes the DuckDuckGo class.
        """
        self.session = requests.Session()

    def _duckduckgo(self, query):
        """
        _duckduckgo returns the first result from a duckduckgo search.

        Args:
            query (str): the query to be searched

        Returns:
            str: the first result from the search
        """
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote_plus(query)}&format=json&pretty=1"
        response = self.session.get(url)
        data = response.json()
        try:
            result = data["AbstractText"]
            if result == "":
                raise Exception
            return result
        except (KeyError, Exception):
            try:
                # Get the first result
                result = data["RelatedTopics"][0]["Text"]
                if result == "":
                    raise Exception
                return result
            except (KeyError, Exception):
                return "No results found."

    def duckduckgo(self, nick, source, privmsg, netmask, is_channel, send_message):
        """
        duckduckgo searches DuckDuckGo for the text it receives.

        Args:
            nick (str): the nick of the user who sent the message
            source (str): the channel or nick the message came from
            privmsg (str): the message
            netmask (str): the netmask of the user who sent the message
            is_channel (bool): whether or not the message was sent in a channel
            send_message (function): a function used to send a message to the correct location

        Returns:
            None if duckduckgo was not used, True if it was used
        """
        ret = None
        if privmsg.startswith(".ddg "):
            ret = True
            query = ircspecial.sub("", privmsg[len(".ddg ") :])
            if is_channel:
                send_message(f"{nick}, {self._duckduckgo(query)}", source)
            else:
                send_message(f"{self._duckduckgo(query)}", source)
            ret = True
        return ret