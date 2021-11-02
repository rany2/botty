"""
DeavmiComedy is a module for botty that turns boring text into funny text.
"""

from regexes import ircspecial


def _deavmicomedy(text):
    """
    _deavmicomedy turns a boring text into a funny one.

    Args:
        text (str): the text to be funnyified

    Returns:
        str: the funnyified text
    """
    haha = ""
    for character in text:
        haha += f"{character} "
    return haha[:-1]


def deavmicomedy(nick, source, privmsg, netmask, is_channel, send_message):
    """
    deavmicomedy turns the text it receives into something of comedic value
    for deavmi.

    Args:
        nick (str): the nick of the user who sent the message
        source (str): the channel or nick the message came from
        privmsg (str): the message
        netmask (str): the netmask of the user who sent the message
        is_channel (bool): whether or not the message was sent in a channel
        send_message (function): a function used to send a message to the correct location

    Returns:
        None if deavmicomedy was not used, True if it was used
    """
    ret = None
    if privmsg.startswith(".deavmicomedy "):
        to_be_funnied = ircspecial.sub("", privmsg[len(".deavmicomedy ") :])
        if is_channel:
            send_message(f"{nick}, {_deavmicomedy(to_be_funnied)}", source)
        else:
            send_message(f"{_deavmicomedy(to_be_funnied)}", source)
        ret = True
    return ret
