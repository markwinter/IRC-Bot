import time
import string
from requests import get
from lxml.html import fromstring
from enum import Enum

class Timer():
    def start_timer(self):
        self.start = time.time()

    def stop_timer(self):
        self.end = time.time()

    def elapsed_time(self):
        return self.end - self.start

class HTTPCode(Enum):
    """Make HTTP codes human readable.

    Enum used for making HTTP codes human readable from within the code.
    Also allows for easy extension of handling more HTTP codes.
    """
    OK = 200

class LinkResolver():
    """Gets title of a given html page.

    Uses the 'requests' python package to download the content of the given url.
    Will allow for only a single redirect to counter trying to resolve an
    endless loop.

    Checks are made for
        - HTTP 200 OK status code returned
        - Content-Type header contains text/html;
        - Content-Length header is less than max_content_size

    Whilst downloading the page checks are made for
        - Time downloading is less than receiving_timeout
        - Download size is less than max_content_size

    Args:
        url: the url of the page to download

    Returns:
        A formatted string containing the title and time for function to execute.
        For exmaple:
            "Title: Red Velvet Ice Creak Cake (0.27s)"

    Raises:
        ValueError: One of the aforementioned checks failed
        HTTPError:
    """
    def __init__(self):
        self.max_content_size = 3000000
        self.receiving_timeout = 2
        self.timer = Timer()

    def get_title(self, url):
        self.timer.start_timer()

        response = get(
            url,
            timeout=self.receiving_timeout,
            stream=True,
            allow_redirects=False
        )

        # Follow up to 3 redirects
        for i in range(0, 3):
            if response.headers.get('location'):
                response = get(
                    response.headers.get('location'),
                    timeout=self.receiving_timeout,
                    stream=True,
                    allow_redirects=False
                )
            else:
                break

        response.raise_for_status()

        # Only need to do anything for OK status code
        if response.status_code != HTTPCode.OK.value:
            raise ValueError('invalid http code')

        # Only process text/html pages
        if (response.headers.get('Content-Type') and
           "text/html" not in response.headers.get('Content-Type')):
            raise ValueError('invalid content type')

        # Check content-length for pages that are too big
        # Maybe this check is a little redundant as we check size
        # more precisely below
        if (response.headers.get('Content-Length') and
           int(response.headers.get('Content-Length')) > self.max_content_size):
            raise ValueError('reponse too large')

        # Download page in 1024 byte chunks, checking for time taken and max
        # size on the go
        size = 0
        start = time.time()
        chunks = ""
        for chunk in response.iter_content(1024, decode_unicode=True):
            if time.time() - start > self.receiving_timeout:
                raise ValueError('Took too long downloading page')

            size += len(chunk)

            if size > self.max_content_size:
                raise ValueError('response too large')

            chunks += chunk

        doc = fromstring(chunks)
        title = doc.cssselect("title")

        if title:
            title = title[0].text.strip()

            # Detect Korean language
            is_korean = False
            maxchar = max(title)
            if ((u'\u1100' <= maxchar <= u'\u11FF') or (u'\u3130' <= maxchar <= u'\u318F') or
                (u'\uAC00' <= maxchar <= u'\uD7AF')):
                is_korean = True

            title = filter(lambda x: x in string.printable, title)

            self.timer.stop_timer()

            if is_korean:
                return "Title: {0:s} ({1:.2f}s) \x02\x0304[Korean]\x03\x02".format(title, self.timer.elapsed_time())
            else:
                return "Title: {0:s} ({1:.2f}s)".format(title, self.timer.elapsed_time())
