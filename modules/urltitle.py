"""
urltitle is a module for botty that returns the title of a URL.
"""

import json
import urllib.parse
from datetime import datetime, timedelta

import humanize
import magic
import requests
import urllib3.exceptions

from common import shorten
from regexes import ircspecial, twregex, urlregex, ytregex
from webpreview import web_preview


class UrlTitle:
    """
    UrlTitle is a class that provides methods for getting the title of a URL.
    """

    def __init__(self):
        self.session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept": "text/html,application/xhtml+xml,*/*",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.session.headers.update(headers)

    def ytoutput(self, video_id):
        """
        ytoutput gets the title, description, and other info of a youtube video
        and displays it in a nice IRC friendly format.

        Args:
            video_id (str): the video id of the video to get info for

        Returns:
            str: the formatted info
        """
        response = self.session.get(
            f"https://invidious.snopyta.org/api/v1/videos/{video_id}",
        )
        response2 = self.session.get(
            f"https://returnyoutubedislikeapi.com/Votes?videoId={video_id}",
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
            },
        )
        json_load = json.loads(response.content)
        title = json_load["title"]
        length = json_load["lengthSeconds"]
        upvote = json_load["likeCount"]
        json_load2 = json.loads(response2.content)
        downvote = json_load2["dislikes"]
        try:
            ratio = f"{(upvote/(downvote+upvote) * 100):.1f}%"
        except ZeroDivisionError:
            ratio = "0%"
        upvote = humanize.intcomma(upvote)
        downvote = humanize.intcomma(downvote)
        viewcount = humanize.intcomma(json_load["viewCount"])
        channel_name = json_load["author"]
        date_uploaded = (
            datetime(1970, 1, 1) + timedelta(seconds=int(json_load["published"]))
        ).strftime("%Y.%m.%d")
        yt_shortlink = f"https://youtu.be/{video_id}"
        msg = f"\x02{title}\x03\x0F - "
        if length > 0:
            msg += f"length \x02{humanize.precisedelta(length)}\x03\x0F - "
        if upvote != 0 and downvote != 0:
            msg = f"{msg}\x0303↑{upvote}, \x0304↓{downvote} \x03\x0F (\x0303{ratio}\x03\x0F) - "
        msg = f"{msg}\x02{viewcount}"
        msg = f"{msg}\x03\x0F views - \x02{channel_name}\x03\x0F on \x02{date_uploaded}\x03\x0F - {yt_shortlink}"
        return msg

    def urltitle(self, nick, source, privmsg, netmask, is_channel, send_message):
        """
        urltitle gets the title of a URL and displays it in a nice IRC friendly format.

        Args:
            nick (str): the nick of the user who sent the message
            source (str): the channel or nick the message came from
            privmsg (str): the message
            netmask (str): the netmask of the user who sent the message
            is_channel (bool): whether or not the message was sent in a channel
            send_message (function): a function used to send a message to the correct location

        Returns:
            None if urltitle was not used, True if it was used
        """
        ret = None
        bypass = False
        for iterations, url_irc in enumerate(
            urlregex.findall(ircspecial.sub("", privmsg))
        ):
            if iterations > 2:
                continue
            url_irc = url_irc[0]
            url_with_http = (
                url_irc
                if url_irc.startswith("http://") or url_irc.startswith("https://")
                else "http://" + url_irc
            )
            try:
                response = self.session.head(
                    url_with_http,
                    allow_redirects=True,
                )
            except requests.exceptions.RequestException:
                continue
            except urllib3.exceptions.LocationParseError:
                continue
            url = response.url
            parsed_url = urllib.parse.urlparse(url)
            if ytregex.search(parsed_url.netloc):
                try:
                    parsed_url = urllib.parse.urlparse(
                        "".join(urllib.parse.parse_qs(parsed_url.query)["continue"])
                    )
                except KeyError:
                    pass

                try:
                    finalmsg = [
                        self.ytoutput(urllib.parse.parse_qs(parsed_url.query)["v"][0])
                    ]
                    bypass = True
                except KeyError:
                    parsed_url = parsed_url._replace(netloc="yewtu.be")
            elif twregex.search(parsed_url.netloc):
                parsed_url = parsed_url._replace(netloc="nitter.fdn.fr")
            if not bypass:
                url_new = urllib.parse.urlunparse(parsed_url)
                try:
                    response = self.session.get(
                        url_new,
                        allow_redirects=True,
                        stream=True,
                    )
                except requests.exceptions.RequestException:
                    continue
                if response.status_code >= 400:
                    continue
                # Read first 65536 bytes of the response which should be enough to get the title
                # and the first few lines of the body.
                for i in response.iter_content(chunk_size=65536, decode_unicode=False):
                    content = i
                    break
                # Get encoding from magic module
                encoding = magic.Magic(mime_encoding=True).from_buffer(content)
                length = ""
                try:
                    if response.headers["Content-Length"]:
                        length = (
                            " ("
                            + humanize.naturalsize(response.headers["Content-Length"])
                            + ")"
                        )
                except KeyError:
                    pass

                try:
                    title, description, image = web_preview(
                        url_new, content=content.decode(encoding), parser="lxml"
                    )
                    # title = title + length
                except LookupError:
                    title, description, image = None, None, None

                if title is None:
                    title, description, image = [
                        magic.Magic().from_buffer(content) + length,
                        None,
                        None,
                    ]

                if isinstance(title, str):
                    title = shorten(title, 500)
                    title = f'[ \x0303{parsed_url.netloc}\x03\x0F ] \x02{ircspecial.sub("", " ".join(title.split()))}'
                    finalmsg = [title]  # , description ]

            if finalmsg is not None:
                for msg in finalmsg:
                    send_message(msg, source)
                    ret = True
        return ret
