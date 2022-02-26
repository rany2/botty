def shorten(text, limit):
    """
    Shortens a string to a given length while attempting to
    preserve whole words.

    Args:
        text (str or bytes): The string to shorten.
        limit (int): The maximum length of the string.

    Returns:
        str: The shortened string.
    """
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    elif not isinstance(text, str):
        raise TypeError("text must be a string or bytes")

    if len(text) <= limit:
        return text

    text = text[:limit]
    if text.find(" ") != -1:
        text = text[: text.rfind(" ")] + "..."
    return text
