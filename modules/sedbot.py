"""
sedbot module for botty.
"""

import re


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
            else:
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
            else:
                break

        # Add the character to the re_replacement
        re_replacement += character

    # Do the replacement
    return re.sub(re_pattern, re_replacement, text)


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
        if not privmsg.startswith("s/"):
            try:
                self.messages[source][_netmask] = privmsg
            except KeyError:
                self.messages[source] = {}
                self.messages[source][_netmask] = privmsg
            return None

        try:
            sed_result = a_poor_mans_sed_implementation(
                self.messages[source][_netmask], privmsg
            )
            send_message(f"{nick}, {sed_result}", source)
        except KeyError:
            pass

        return True
