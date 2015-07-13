from threading import Thread, Lock
from time import sleep
from simplejson import loads
from collections import defaultdict
from circuits.protocols.irc import PRIVMSG
from requests import get
from lxml.html import fromstring
import string
import re

mutex = Lock()

class WatchPasteBin(Thread):
    def __init__(self, ircbot):
        Thread.__init__(self)

        self.ircbot = ircbot

        self.base_url = "https://pastebin.com/"

        self.watch = []
        self.seen = []
        self.sender = defaultdict(list)

        self.running = True
        self.setDaemon(True)
        self.start()

    def execute(self, keywords, target, source, ircbot):
        if len(keywords) != 2:
            return -1

        # Only accept keywords 3 letters or more
        if len(keywords[1]) < 3:
            return -1

        # Check for ascii only letters
        if not all(x in string.printable for x in keywords[1]):
            return -1

        mutex.acquire()
        try:
            self.watch.append(keywords[1])
            self.sender[keywords[1]].append(target)
        finally:
            mutex.release()

        ircbot.fire(PRIVMSG(target, "Now watching for '" + str(keywords[1]) + "' on pastebin"))

    def usage(self):
        return "!pastebin <keyword> - keyword must be 3 or more letters and ascii only"

    def run(self):
        while self.running:
            if len(self.watch) > 0:
                response = get(self.base_url + "archive", timeout=3)
                html = response.text

                pastes = re.findall('<td><img src="/i/t.gif"  class="i_p0" alt="" border="0" /><a href="/(\w+)">.+</a></td>', html)

                for paste in pastes:
                    if paste in self.seen:
                        continue

                    paste_content = get(self.base_url + paste)
                    doc = fromstring(paste_content.text)
                    # wtf are all these deeply nested tags pastebin
                    content = doc.cssselect("div#super_frame div#monster_frame div#content_frame div#content_left form#myform.paste_form div.textarea_border textarea#paste_code.paste_code")
                    title = doc.cssselect("div#super_frame div#monster_frame div#content_frame div#content_left div.paste_box_frame div.paste_box_info div.paste_box_line1 h1")

                    # Search for keywords in paste content
                    for keyword in self.watch:
                        if ((keyword.lower() in title[0].text.lower()) or
                            len(re.findall(keyword, content[0].text, re.IGNORECASE)) > 0):

                            for sender in self.sender[keyword]:
                                self.ircbot.fire(PRIVMSG(sender, "New '" + str(keyword) +
                                "' paste found: https://pastebin.com/" + str(paste)))

                    self.seen.append(paste)        

            sleep(30)
