"""
sedbot module for botty.
"""

import re

from common import shorten
from regexes import ircspecial


def a_poor_mans_sed_implementation(text, sed_pattern):
    """
    A poor mans sed implementation.

    Args:
        text (str): The text to search in.
        sed_pattern (str): The sed pattern to search for.

    Returns:
        str: The text with the sed pattern replaced.
    """
    re_pattern = ""
    re_replacement = ""

    # By default, sed only matches the first occurrence of the pattern.
    re_count = 1

    # Sed matches all characters (including the \n ) using a dot .
    re_flags = re.DOTALL

    # Remove the substitution pattern from the sed pattern
    # if it is present.
    if sed_pattern[0] == "s":
        sed_pattern = sed_pattern[2:]

    # Split sed_pattern into re_pattern
    old_character = ""
    for character in sed_pattern:
        # Respect the escape character
        if character == "\\":
            old_character = character
            re_pattern += character
            continue

        # If the character is a backslash, we need to check
        # it it was escaped from old_character
        if character == "/":
            if old_character == "\\":
                re_pattern += character
                old_character = ""
                continue
            break

        # Add the character to the re_pattern
        re_pattern += character

    # Split sed_pattern into re_replacement
    old_character = ""
    for character in sed_pattern[len(re_pattern) + 1 :]:
        # Respect the escape character
        if character == "\\":
            old_character = character
            re_replacement += character
            continue

        # If the character is a backslash, we need to check
        # it it was escaped from old_character
        if character == "/":
            if old_character == "\\":
                re_replacement += character
                old_character = ""
                continue
            break

        # Add the character to the re_replacement
        re_replacement += character

    # Split sed_pattern into re_flags
    for character in sed_pattern[len(re_pattern) + len(re_replacement) + 2 :]:
        if character == "g":
            re_count = 0
        elif character.lower() == "i":
            re_flags |= re.IGNORECASE
        elif character.lower() == "m":
            re_flags |= re.MULTILINE

    # Do the replacement
    return re.sub(
        re_pattern,
        re_replacement,
        text,
        count=re_count,
        flags=re_flags,
    )


class SedBot:
    """
    Implements a SedBot
    """

    def __init__(self) -> None:
        """
        Initializes the SedBot.
        """
        self.messages = {}

    def sed(self, nick, source, privmsg, netmask, is_channel, send_message):
        """
        Handles the sed command.

        Args:
            nick (str): the nick of the user who sent the message
            source (str): the channel or nick the message came from
            privmsg (str): the message
            netmask (str): the netmask of the user who sent the message
            is_channel (bool): whether or not the message was sent in a channel
            send_message (function): a function used to send a message to the correct location

        Returns:
            None if sed was not used, True if it was used
        """
        if not is_channel:
            return None

        _netmask = "!".join(netmask.split("!")[1:])
        _privmsg = ircspecial.sub("", privmsg.strip())
        if not privmsg.startswith("s/"):
            try:
                self.messages[source][_netmask] = _privmsg
            except KeyError:
                self.messages[source] = {}
                self.messages[source][_netmask] = _privmsg
            return None

        try:
            sed_result = shorten(
                a_poor_mans_sed_implementation(
                    self.messages[source][_netmask], _privmsg
                ),
                500,
            )
            send_message(f"{sed_result}", source)
        except (KeyError, re.error):
            pass

        return True
