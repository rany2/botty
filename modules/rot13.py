"""
rot13 is a module for botty to rotate text 13 characters to the right.
"""

import codecs


def _rot13(text):
    """
    rot13 rotates the text it receives 13 characters to the right.

    Args:
        text (str): the text to be rotated

    Returns:
        str: the rotated text
    """
    return codecs.encode(text, "rot13")


def rot13(nick, source, privmsg, netmask, is_channel, send_message):
    """
    rot13 rotates the text it receives 13 places.

    Args:
        nick (str): the nick of the user who sent the message
        source (str): the channel or nick the message came from
        privmsg (str): the message
        netmask (str): the netmask of the user who sent the message
        is_channel (bool): whether or not the message was sent in a channel
        send_message (function): a function used to send a message to the correct location

    Returns:
        None if rot13 was not used, True if it was used
    """
    ret = None
    if privmsg.startswith(".rot13 "):
        if is_channel:
            send_message(f'{nick}, {_rot13(privmsg[len(".rot13 ") :])}', source)
        else:
            send_message(f'{_rot13(privmsg[len(".rot13 ") :])}', source)
        ret = True
    return ret
