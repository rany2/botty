#!/usr/bin/env python3

"""
Basic IRC bot.
"""

import socket
import threading
import time

from config import (
    CHANNELS_TO_JOIN,
    MODULES,
    NICKSERV_PASS,
    SERVER_ADDR,
    SERVER_NICK,
    SERVER_PASS,
    SERVER_PORT,
)


def split_text_by_bytes(text, max_length):
    """
    split_text_by_bytes is a helper function that splits a utf-8 string
    into multiple strings of a maximum byte length.

    Args:
        text (str or bytes): The string to split.
        max_length (int): The maximum length of each string.

    Yields:
        The split string.
    """
    if isinstance(text, str):
        data = text
    elif isinstance(text, bytes):
        data = text.decode("utf-8")
    else:
        raise TypeError("text must be a string or bytes")
    del text

    new_data = ""
    for character in data:
        new_data += character
        if len(new_data.encode("utf-8")) > max_length:
            new_new_data = new_data
            new_data = ""
            while len(new_new_data.encode("utf-8")) > max_length:
                new_data += new_new_data[-1]
                new_new_data = new_new_data[:-1]

            # Attempt to split at complete word.
            if new_new_data.find(" ") != -1:
                while new_new_data[-1] != " ":
                    new_data = new_new_data[-1] + new_data
                    new_new_data = new_new_data[:-1]

            yield new_new_data
            del new_new_data

    if len(new_data) > 0:
        yield new_data


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
        self.decider(run_once=True)
        self.send(f"NICK {self.server_nick}")
        self.decider(run_once=True)
        self.send(
            f"USER {self.server_nick} {self.server_nick} {self.server_nick} :{self.server_nick}"
        )
        self.decider(run_once=True)
        if self.nickserv_pass is not None:
            self.send(f"PRIVMSG NickServ :IDENTIFY {self.nickserv_pass}\r\n")
            self.decider(run_once=True)
        time.sleep(1)
        for channel in CHANNELS_TO_JOIN:
            self.send(f"JOIN {channel}")
            self.decider(run_once=True)
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
        self.sock.send(f"{msg}".encode("utf-8") + b"\r\n")

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
        raise SystemExit(0)

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

        # Run the functions
        try:
            for module in MODULES:
                if (
                    module(
                        nick, source, privmsg, netmask, is_channel, self.send_message
                    )
                    == True
                ):
                    break
        finally:
            raise SystemExit(0)

    def send_message(self, msg, target):
        """
        send_message is a helper function that sends a message to a target.

        Args:
            msg: The message to send to the target.
            target: The target to send the message to.

        Returns:
            None
        """
        # ref:
        #  - https://github.com/hexchat/hexchat/blob/9039a5d75ba854d00bfbd9bb5235ec547eeffbe1/src/common/outbound.c#L2641-L2695
        #  - https://github.com/hexchat/hexchat/blob/f42f6af1b96f80280a2e5a5e2431dc32d2b8fd55/src/common/proto-irc.c
        #
        # :nickname!username@host.com cmd_length
        max_msg_length = 512  # rfc 2812
        max_msg_length -= 3  # :, !, @
        max_msg_length -= len(f"PRIVMSG {target} :".encode("utf-8"))  # cmd length
        max_msg_length -= len("\r\n".encode("utf-8"))  # \r\n is sent automatically
        max_msg_length -= 9  # max possible username length
        max_msg_length -= 65  # max possible hostname length

        if isinstance(msg, bytes):
            msg = msg.decode("utf-8")

        for line in msg.splitlines():
            for split_line in split_text_by_bytes(line, max_length=max_msg_length):
                self.send(f"PRIVMSG {target} :{split_line}")

    def decider(self, run_once=False):
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

            if run_once:
                break


if __name__ == "__main__":
    IRCClient(
        SERVER_ADDR,
        SERVER_PORT,
        SERVER_PASS,
        SERVER_NICK,
        CHANNELS_TO_JOIN,
        NICKSERV_PASS,
    )
