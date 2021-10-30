#!/usr/bin/env python3

"""
Basic IRC bot.
"""

import json
import re
import socket
import threading
import urllib.parse
from datetime import datetime, timedelta

import humanize
import magic
import requests

from config import *
from webpreview import web_preview

"""
Regex patterns for the bot.
"""
ircspecial = re.compile(
    "\x1f|\x01|\x02|\x12|\x0f|\x1d|\x16|\x0f(?:\d{1,2}(?:,\d{1,2})?)?|\x03(?:\d{1,2}(?:,\d{1,2})?)?",
    re.UNICODE,
)
urlregex = re.compile("((https?://|[\S]*\.[\S])([\S]*))")
ytregex = re.compile(r"(\.|^)(youtube\.com|youtu\.be)$")
twregex = re.compile(r"(\.|^)twitter\.com$")
headers = {
    "User-Agent": "urlircbot/1.0",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.5",
}


def translate(text, to_lang="en"):
    """
    translate text to the specified language

    Args:
        text (str): text to translate
        to_lang (str): language to translate to

    Returns:
        str: translated text
    """

    url = f"https://translate.google.com/translate_a/single?client=gtx&sl=auto&tl={urllib.parse.quote_plus(to_lang)}&dt=t&q={urllib.parse.quote_plus(text)}"
    response = requests.get(url)
    data = json.loads(response.text)
    new_data = ""
    for iter_data in data[0]:
        new_data += f"{iter_data[0]}"
    return new_data


def ytoutput(video_id):
    """
    ytoutput gets the title, description, and other info of a youtube video
    and displays it in a nice IRC friendly format.

    Args:
        video_id (str): the video id of the video to get info for

    Returns:
        str: the formatted info
    """
    response = requests.get(
        f"https://invidious.snopyta.org/api/v1/videos/{video_id}",
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
        },
    )
    json_load = json.loads(response.content)
    title = json_load["title"]
    length = humanize.precisedelta(json_load["lengthSeconds"])
    upvote = json_load["likeCount"]
    downvote = json_load["dislikeCount"]
    try:
        ratio = f"{(upvote/(downvote+upvote) * 100):.1f}%"
    except:
        ratio = "0%"
    upvote = humanize.intcomma(upvote)
    downvote = humanize.intcomma(downvote)
    viewcount = humanize.intcomma(json_load["viewCount"])
    channel_name = json_load["author"]
    date_uploaded = (
        datetime(1970, 1, 1) + timedelta(seconds=int(json_load["published"]))
    ).strftime("%Y.%m.%d")
    yt_shortlink = f"https://youtu.be/{video_id}"
    msg = f"\x02{title}\x03\x0F - length \x02{length}\x03\x0F - "
    if upvote != 0 and downvote != 0:
        msg = f"{msg}\x0303↑{upvote}, \x0304↓{downvote} \x03\x0F (\x0303{ratio}\x03\x0F) - "
    msg = f"{msg}\x02{viewcount}"
    msg = f"{msg}\x03\x0F views - \x02{channel_name}\x03\x0F on \x02{date_uploaded}\x03\x0F - {yt_shortlink}"
    return msg


def mkurltitle(s, target, rmsg):
    """
    ATTENTION: THIS FUNCTION NEEDS IMPROVING
    """
    iterations = 0
    bypass = False
    for url_irc in urlregex.findall(rmsg):
        iterations += 1
        if iterations > 2:
            continue
        url_irc = url_irc[0]
        url_with_http = (
            url_irc
            if url_irc.startswith("http://") or url_irc.startswith("https://")
            else "http://" + url_irc
        )
        try:
            r = requests.head(url_with_http, allow_redirects=True, headers=headers)
        except:
            continue
        url = r.url
        p = urllib.parse.urlparse(url)
        if ytregex.search(p.netloc):
            try:
                p = urllib.parse.urlparse(
                    "".join(urllib.parse.parse_qs(p.query)["continue"])
                )
            except:
                pass

            try:
                finalmsg = [ytoutput(urllib.parse.parse_qs(p.query)["v"][0])]
                bypass = True
            except:
                p = p._replace(netloc="yewtu.be")
        elif twregex.search(p.netloc):
            p = p._replace(netloc="nitter.fdn.fr")
        if not bypass:
            urlNew = urllib.parse.urlunparse(p)
            try:
                r = requests.get(
                    urlNew, allow_redirects=True, stream=True, headers=headers
                )
            except:
                continue
            if r.status_code >= 400:
                continue
            # read x chunk only ... should be enough for title, description and image.
            for i in r.iter_content(chunk_size=2 ** 16, decode_unicode=False):
                content = i
                break
            # Get encoding from magic module
            f = magic.Magic(mime_encoding=True)
            encoding = f.from_buffer(content)
            length = ""
            try:
                if r.headers["Content-Length"]:
                    length = (
                        " (" + humanize.naturalsize(r.headers["Content-Length"]) + ")"
                    )
            except:
                pass

            try:
                title, description, image = web_preview(
                    urlNew, content=content.decode(encoding), parser="lxml"
                )
                # title = title + length
            except LookupError:
                title, description, image = None, None, None

            if title is None:
                g = magic.Magic()
                title, description, image = [
                    g.from_buffer(content) + length,
                    None,
                    None,
                ]

            if isinstance(title, str):
                title = f'[ \x0303{p.netloc}\x03\x0F ] \x02{ircspecial.sub("", " ".join(title.split()))}'
                finalmsg = [title]  # , description ]

        if finalmsg is not None:
            try:
                for msg in finalmsg:
                    s(msg, target)
            except:
                continue


class IRCClient:
    """
    IRCClient class is a simple IRC client.
    """

    def __init__(
        self,
        _server_addr,
        _server_port,
        _server_pass,
        _server_nick,
        _channels_to_join,
        _nickserv_pass,
    ):
        """
        __init__ is the constructor for the IRCClient class.

        Args:
            _server_addr: The address of the IRC server.
            _server_port: The port of the IRC server.
            _server_pass: The password to use when connecting to the IRC server.
            _server_nick: The nickname to use when connecting to the IRC server.
            _channels_to_join: A list of channels to join when connecting to the IRC server.
            _nickserv_pass: The password to use when connecting to the NickServ service.

        Returns:
            None

        Raises:
            socket.gaierror if the server address is invalid.
            socket.error if the server is unreachable.
        """
        self.server_addr = _server_addr
        self.server_port = _server_port
        self.server_pass = _server_pass
        self.server_nick = _server_nick
        self.channels_to_join = _channels_to_join
        self.nickserv_pass = _nickserv_pass
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.sock.connect((self.server_addr, self.server_port))
        self.initialize()

    def initialize(self):
        """
        initialize initializes the IRC connection by setting up the nickname,
        username, and password. It also joins the channels specified in the
        channels_to_join list.

        Args:
            None

        Returns:
            None
        """
        self.send(f"PASS {self.server_pass}")
        self.send(f"NICK {self.server_nick}")
        self.send(
            f"USER {self.server_nick} {self.server_nick} {self.server_nick} :{self.server_nick}"
        )
        # We must wait for the server to send us data before joining any channels
        self.recv()
        self.recv()
        if self.nickserv_pass is not None:
            self.send(
                f"PRIVMSG NickServ :IDENTIFY {self.nickserv_pass} {self.server_nick}"
            )
            self.recv()
        for channel in CHANNELS_TO_JOIN:
            self.send(f"JOIN {channel}")
        self.decider()

    def send(self, msg):
        """
        send is a helper function that sends a message to the IRC server.

        Args:
            msg: The message to send to the IRC server.

        Returns:
            None
        """
        print(f"> {msg}")
        self.sock.send(f"{msg}".encode("utf-8")[:510] + b"\r\n")

    def recv(self):
        """
        recv is a helper function that receives a message from the IRC server.

        Args:
            None

        Returns:
            data - The message received from the IRC server.
        """
        data = self.sock.recv(1024)
        # Keep receiving data until we get a complete message
        while not data.endswith(b"\r\n"):
            data += self.sock.recv(1)
        # Return the message
        return data

    def ctcp_handler(self, msg, nick, source, privmsg, netmask, is_channel):
        """
        ctcp_handler is a helper function that handles CTCP messages.

        Args:
            msg: The message received from the IRC server.
            nick: The nickname of the user who sent the message.
            source: The source of the message.
            privmsg: The message itself.
            netmask: The netmask of the user who sent the message.
            is_channel: Whether or not the message was sent in a channel.

        Returns:
            None
        """

    def privmsg_handler(self, msg):
        """
        privmsg_handler is a helper function that handles a PRIVMSG message.

        Args:
            msg: The message received from the IRC server.

        Returns:
            None
        """
        nick = msg.split("!", 1)[0][1:]
        source = msg.split("PRIVMSG", 1)[1].split(":", 1)[0].split(" ")[1]
        privmsg = msg.split("PRIVMSG", 1)[1].split(":", 1)[1]
        netmask = "@".join(msg.split("@")[0:2]).split(" ", maxsplit=1)[0]
        is_channel = True
        # If the message was not received from the channel,
        # we set the source to the nick so the rest of the code
        # is not broken by the fact that the source is not a channel
        if not source.startswith("#"):
            source = nick
            is_channel = False
        print("Received PRIVMSG:", nick, source, privmsg, netmask, is_channel)

        # Handle CTCP requests in a separate function
        if privmsg.startswith("\x01"):
            self.ctcp_handler(msg, nick, source, privmsg, netmask, is_channel)
            return

        # If translate command is used, translate the message
        if privmsg.startswith(".tr ") or privmsg.startswith(".tr:"):
            if privmsg.startswith(".tr:"):
                privmsg = privmsg[len(".tr") :]
                privmsg = privmsg.split(" ")
                tolang = privmsg[0][1:]
                text_to_trans = " ".join(privmsg[1:])
            else:
                text_to_trans = privmsg[len(".tr ") :]
                tolang = "en"
            transed = f"{translate(text_to_trans, tolang)}"
            if is_channel:
                self.send_message(f"{nick}, {transed}", source)
            else:
                self.send_message(f"{transed}", source)

        # Run mkurltitle regardless
        mkurltitle(self.send_message, source, privmsg)

    def send_message(self, msg, target):
        """
        send_message is a helper function that sends a message to a target.

        Args:
            msg: The message to send to the target.
            target: The target to send the message to.

        Returns:
            None
        """
        self.send(f"PRIVMSG {target} :{msg}".encode("utf-8")[:510].decode("utf-8"))

    def decider(self):
        """
        decider is a helper function that decides what to do with the message
        received from the IRC server.

        Args:
            None

        Returns:
            None
        """
        while True:
            ircmsgs = self.recv().decode("utf-8")
            ircmsgs = ircmsgs.rstrip("\r\n").split("\r\n")
            for ircmsg in ircmsgs:
                print(f"< {ircmsg}")
                if ircmsg.startswith("PING"):
                    self.send(ircmsg.replace("PING", "PONG"))
                elif ircmsg.split(" ")[1] == "PRIVMSG":
                    threading.Thread(
                        target=self.privmsg_handler, args=(ircmsg,)
                    ).start()


if __name__ == "__main__":
    IRCClient(SERVER_ADDR, SERVER_PORT, SERVER_PASS, SERVER_NICK, CHANNELS_TO_JOIN)
