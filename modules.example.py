import json
import re
import urllib.parse
from datetime import datetime, timedelta

import humanize
import magic
import requests

from webpreview import web_preview

"""
Regex patterns for the bot.
"""
ircspecial = re.compile(
    "\x1f|\x01|\x02|\x12|\x0f|\x1d|\x16|\x0f(?:\d{1,2}(?:,\d{1,2})?)?|\x03(?:\d{1,2}(?:,\d{1,2})?)?",
    re.UNICODE,
)
urlregex = re.compile("((https?://|[\S]*\.[\S]|\[[^\]]*\])([\S]*))")
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


def mkurltitle(nick, source, privmsg, netmask, is_channel, send_message):
    """
    mkuurl gets the title of a URL and displays it in a nice IRC friendly format.

    Args:
        nick (str): the nick of the user who sent the message
        source (str): the channel or nick the message came from
        privmsg (str): the message
        netmask (str): the netmask of the user who sent the message
        is_channel (bool): whether or not the message was sent in a channel
        send_message (function): a function used to send a message to the correct location

    Returns:
        None: this function does not return anything
    """
    iterations = 0
    bypass = False
    for url_irc in urlregex.findall(ircspecial.sub("", privmsg)):
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
                    send_message(msg, source)
            except:
                continue


def mktranslate(nick, source, privmsg, netmask, is_channel, send_message):
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
        None: this function does not return anything
    """
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
            send_message(f"{nick}, {transed}", source)
        else:
            send_message(f"{transed}", source)


def deavmicomedy(text):
    """
    deavmicomedy turns a message into a funny one.
    """
    haha = ""
    for ch in text:
        haha += f"{ch} "
    return haha[:-1]


def mkdeavmicomedy(nick, source, privmsg, netmask, is_channel, send_message):
    """
    mkdeavmicomedy turns the text it receives into something of comedic value
    for deavmi.

    Args:
        nick (str): the nick of the user who sent the message
        source (str): the channel or nick the message came from
        privmsg (str): the message
        netmask (str): the netmask of the user who sent the message
        is_channel (bool): whether or not the message was sent in a channel
        send_message (function): a function used to send a message to the correct location

    Returns:
        None: this function does not return anything
    """
    if privmsg.startswith(".deavmicomedy"):
        if is_channel:
            send_message(
                f'{nick}, {deavmicomedy(privmsg[len(".deavmicomedy "):])}', source
            )
        else:
            send_message(f'{deavmicomedy(privmsg[len(".deavmicomedy ") :])}', source)
