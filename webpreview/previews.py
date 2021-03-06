import re

from bs4 import BeautifulSoup

from .excepts import *
from .helpers import process_image_url


class PreviewBase(object):
    """
    Base for all web preview.
    """

    def __init__(
        self,
        url=None,
        properties=None,
        timeout=None,
        headers=None,
        content=None,
        parser="html.parser",
    ):
        if not properties:
            raise EmptyProperties("Please pass list of properties to be extracted.")
        self.url = url
        # its safe to assign properties
        self.properties = properties
        self._soup = BeautifulSoup(content, parser)


class GenericPreview(PreviewBase):
    """
    Extracts title, description, image from a webpage's body instead of the meta tags.
    """

    def __init__(
        self,
        url=None,
        properties=["title", "description", "image"],
        timeout=None,
        headers=None,
        content=None,
        parser=None,
    ):
        super(GenericPreview, self).__init__(
            url,
            properties,
            timeout=timeout,
            headers=headers,
            content=content,
            parser=parser,
        )
        self.title = self._get_title()
        self.description = self._get_description()
        self.image = self._get_image()

    def _get_title(self):
        """
        Extract title from the given web page.
        """
        soup = self._soup
        # if title tag is present and has text in it, return it as the title
        if soup.title and soup.title.text != "":
            return soup.title.text
        # else if h1 tag is present and has text in it, return it as the title
        if soup.h1 and soup.h1.text != "":
            return soup.h1.text
        # if no title, h1 return None
        return None

    def _get_description(self):
        """
        Extract description from the given web page.
        """
        soup = self._soup
        # extract content preview from meta[name='description']
        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description and meta_description["content"] != "":
            return meta_description["content"]
        # else extract preview from the first <p> sibling to the first <h1>
        first_h1 = soup.find("h1")
        if first_h1:
            first_p = first_h1.find_next("p")
            if first_p and first_p.string != "":
                return first_p.text
        # else extract preview from the first <p>
        first_p = soup.find("p")
        if first_p and first_p.string != "":
            return first_p.string
        # else
        return None

    def _get_image(self):
        """
        Extract preview image from the given web page.
        """
        soup = self._soup
        # extract the first image which is sibling to the first h1
        first_h1 = soup.find("h1")
        if first_h1:
            first_image = first_h1.find_next_sibling("img")
            if first_image and first_image["src"] != "":
                return first_image["src"]
        return None


class SocialPreviewBase(PreviewBase):
    """
    Abstract class for OpenGraph, TwitterCard and Google+.
    """

    def __init__(self, *args, **kwargs):
        super(SocialPreviewBase, self).__init__(*args, **kwargs)
        self._set_properties()
        # OpengGraph has <meta property="" content="">
        # TwitterCard  has <meta name="" content="">
        # Google+  has <meta itemprop="" content="">
        # override this self._target_attribute

    def _set_properties(self):
        soup = self._soup
        for property in self.properties:
            property_meta = soup.find("meta", attrs={self._target_attribute: property})
            # turn "og:title" to "title" and "og:price:amount" to price_amount
            if re.search(r":", property):
                new_property = property.split(":", 1)[1].replace(":", "_")
            # turn "camelCase" to "camel_case"
            elif re.search(r"[A-Z]", property):
                # regex taken from 2nd answer at http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case
                new_property = re.sub("(?!^)([A-Z]+)", r"_\1", property).lower()
            else:
                new_property = property

            if property_meta and property_meta["content"] != "":
                # dynamically attach property to instance
                self.__dict__[new_property] = property_meta["content"]
            else:
                self.__dict__[new_property] = None


class OpenGraph(SocialPreviewBase):
    """
    Gets OpenGraph meta properties of a webpage.
    """

    def __init__(self, *args, **kwargs):
        self._target_attribute = "property"
        super(OpenGraph, self).__init__(*args, **kwargs)


class TwitterCard(SocialPreviewBase):
    """
    Gets TwitterCard meta properties of a webpage.
    """

    def __init__(self, *args, **kwargs):
        self._target_attribute = "name"
        super(TwitterCard, self).__init__(*args, **kwargs)


class Schema(SocialPreviewBase):
    """
    Gets Schema meta properties from a website.
    """

    def __init__(self, *args, **kwargs):
        self._target_attribute = "itemprop"
        super(Schema, self).__init__(*args, **kwargs)


def web_preview(
    url, timeout=None, headers=None, absolute_image_url=False, content=None, parser=None
):
    """
    Extract title, description and image from OpenGraph or TwitterCard or Schema or GenericPreview. Which ever returns first.
    """
    og = OpenGraph(
        url,
        ["og:title", "og:description", "og:image"],
        timeout=timeout,
        headers=headers,
        content=content,
        parser=parser,
    )
    if og.title:
        return (
            og.title,
            og.description,
            process_image_url(url, og.image, absolute_image_url),
        )

    tc = TwitterCard(
        url,
        ["twitter:title", "twitter:description", "twitter:image"],
        timeout=timeout,
        headers=headers,
        content=content,
        parser=parser,
    )
    if tc.title:
        return (
            tc.title,
            tc.description,
            process_image_url(url, tc.image, absolute_image_url),
        )

    s = Schema(
        url,
        ["name", "description", "image"],
        timeout=timeout,
        headers=headers,
        content=content,
        parser=parser,
    )
    if s.name:
        return (
            s.name,
            s.description,
            process_image_url(url, s.image, absolute_image_url),
        )

    gp = GenericPreview(
        url, timeout=timeout, headers=headers, content=content, parser=parser
    )
    return (
        gp.title,
        gp.description,
        process_image_url(url, gp.image, absolute_image_url),
    )
