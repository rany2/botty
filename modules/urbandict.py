import urllib.parse

import requests

from common import shorten
from regexes import ircspecial


class UrbanDictionary:
    """
    UrbanDictionary class for getting definitions from Urban Dictionary.
    """

    def __init__(self):
        self.url = "http://api.urbandictionary.com/v0/define?term="
        self.session = requests.Session()

    def get_definition(self, word, item=1):
        """
        Get the definition of a word from Urban Dictionary.
        """
        url = self.url + urllib.parse.quote_plus(word)
        response = self.session.get(url)
        item -= 1  # item starts at 0, so we need to subtract 1
        if response.status_code == 200:
            data = response.json()
            if data["list"]:
                try:
                    return_data = []
                    return_data.append(
                        f"\x02Definition:\x02 {shorten(data['list'][item]['definition'], 140)}\n"
                    )
                    return_data.append(
                        f"\x02Example:\x02 {shorten(data['list'][item]['example'], 140)}\n"
                    )
                    return_data.append(
                        f"\x02Author:\x02 {data['list'][item]['author']}\n"
                    )
                    return_data.append(
                        f"\x02Permalink:\x02 {data['list'][item]['permalink']}"
                    )
                    return return_data
                except IndexError:
                    return ["No definition found."]
            else:
                return ["No definition found."]
        else:
            return ["Error: {}".format(response.status_code)]

    def mkurbandict(
        self,
        nick: str,
        source: str,
        privmsg: str,
        netmask: str,
        is_channel: bool,
        send_message: callable,
    ):
        """
        mkurbandict gets a definition from Urban Dictionary.

        Args:
            nick (str): the nick of the user who sent the message
            source (str): the channel or nick the message came from
            privmsg (str): the message
            netmask (str): the netmask of the user who sent the message
            is_channel (bool): whether or not the message was sent in a channel
            send_message (function): a function used to send a message to the correct location

        Returns:
            None if urbandict was not used, True if it was used
        """
        if privmsg.startswith(".ub ") or privmsg.startswith(".ub:"):
            if privmsg.startswith(".ub:"):
                privmsg = privmsg[len(".ub") :]
                privmsg = privmsg.split(" ")
                try:
                    def_num = int(privmsg[0][1:])
                except ValueError:
                    if is_channel:
                        send_message(f"{nick}, Invalid definition number.", source)
                    else:
                        send_message(f"Invalid definition number.", source)
                    return True
                query = ircspecial.sub("", " ".join(privmsg[1:]))
            else:
                query = ircspecial.sub("", privmsg[len(".ub ") :])
                def_num = 1
            if def_num <= 0:
                if is_channel:
                    send_message(f"{nick}, Invalid definition number.", source)
                else:
                    send_message(f"Invalid definition number.", source)
                return True
            ub_list = self.get_definition(query, def_num)
            for ub_item in ub_list:
                if is_channel:
                    send_message(f"{nick}, {ub_item}", source)
                else:
                    send_message(f"{ub_item}", source)
            return True
        return None
