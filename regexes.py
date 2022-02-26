"""
Regex patterns for the bot.
"""

import re

ircspecial = re.compile(
    r"\x1f|\x01|\x02|\x12|\x0f|\x1d|\x16|\x0f(?:\d{1,2}(?:,\d{1,2})?)?|\x03(?:\d{1,2}(?:,\d{1,2})?)?",
    re.UNICODE,
)
# urlregex = re.compile(r"((https?://|[\S]*\.[\S]|\[[^\]]*\])([\S]*))")
urlregex = re.compile(r"((https?://[\S]+))")
ytregex = re.compile(r"(\.|^)(youtube\.com|youtu\.be)$")
twregex = re.compile(r"(\.|^)twitter\.com$")
