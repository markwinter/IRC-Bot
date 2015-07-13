from threading import Thread, Lock
from time import sleep
from simplejson import loads
from collections import defaultdict
from circuits.protocols.irc import PRIVMSG
from requests import get
import string

mutex = Lock()

class WatchEightChan(Thread):
    def __init__(self, ircbot):
        Thread.__init__(self)

        self.ircbot = ircbot

        self.base_url = "https://8ch.net/"

        self.watch = defaultdict(list)
        self.seen = defaultdict(list)
        self.sender = defaultdict(list)

        self.running = True
        self.setDaemon(True)
        self.start()

    def execute(self, keywords, target, source, ircbot):
        # Check for right amount of keywords for command
        if len(keywords) != 3:
            return -1

        board = keywords[1]
        keyword = keywords[2]

        # Only accept keywords 3 letters or more
        if len(keyword) < 3:
            return -1

        # Check for ascii only letters
        if not all(x in string.printable for x in keyword):
            return -1

        # Try-finally to make sure we release the lock
        mutex.acquire()
        try:
            self.watch[board].append(keyword)
            self.sender[keyword].append(target)
        finally:
            mutex.release()

        self.ircbot.fire(PRIVMSG(target, "Now watching for '" + keyword + "' on /" + board + "/"))

    def usage(self):
        return "!8ch <board> <keyword> - keyword must be at least 3 letters and ascii only"

    def run(self):
        while self.running:
            for board in self.watch:
                mutex.acquire()

                # Check there's keywords to monitor for this board
                if len(self.watch[board]) > 0:
                    url = "https://8ch.net/" + str(board) + "/catalog.json"
                    response = get(url, timeout=3)
                    json = loads(response.text)

                    for page in json:
                        for thread in page['threads']:
                            if thread['no'] in self.seen[board]:
                                continue

                            for keyword in self.watch[board]:
                                    if (keyword.lower() in thread.get('sub', '').lower() or
                                        keyword.lower() in thread.get('com', '').lower()):

                                        self.seen[board].append(thread['no'])

                                        for sender in self.sender[keyword]:
                                            self.ircbot.fire(PRIVMSG(sender, "New '" + str(keyword) +
                                                "' thread found: https://8ch.net/" + str(board) +
                                                "/res/" + str(thread['no']) + ".html")
                                            )

                mutex.release()

            sleep(60)
