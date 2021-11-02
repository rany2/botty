"""
reversed is a module for botty to reverse text.
"""

def reversed(nick, source, privmsg, netmask, is_channel, send_message):
    """
    reversed reverses the text it receives.

    Args:
        nick (str): the nick of the user who sent the message
        source (str): the channel or nick the message came from
        privmsg (str): the message
        netmask (str): the netmask of the user who sent the message
        is_channel (bool): whether or not the message was sent in a channel
        send_message (function): a function used to send a message to the correct location

    Returns:
        None if mkreversed was not used, True if it was used
    """
    ret = None
    if privmsg.startswith(".rev "):
        if is_channel:
            send_message(f'{nick}, {privmsg[len(".rev ") :][::-1]}', source)
        else:
            send_message(f'{privmsg[len(".rev ") :][::-1]}', source)
        ret = True
    return ret