from collections import defaultdict
from requests import get
from simplejson import loads
from threading import Thread, Lock
from time import sleep
from circuits.protocols.irc import PRIVMSG
import string

mutex = Lock()

class Watcher(Thread):
    def __init__(self, ircbot):
        Thread.__init__(self)

        self.ircbot = ircbot

        self.watch = defaultdict(list)
        self.seen = defaultdict(list)
        self.sender = defaultdict(list)

        # Prepopulate watch with all boards
        response = get("https://a.4cdn.org/boards.json", timeout=3)
        json = loads(response.text)
        for board in json['boards']:
            self.watch[board['board']] = []
            self.seen[board['board']] = []

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

        # Check its a valid board
        if board not in self.watch:
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
        return "!watch <board> <keyword> - keyword must be 3 or more letters long and ascii only"

    def run(self):
        while self.running:
            # Loop through self.watch for non empty lists in values
            # Download catalog corresponding to key
            # Search catalog for values in value list
            # If new result not previously seen then announce it
            for board in self.watch:
                mutex.acquire()

                if len(self.watch[board]) > 0:
                    url = "https://a.4cdn.org/" + board + "/catalog.json"
                    response = get(url, timeout=3)
                    json = loads(response.text)

                    for page in json:
                        for thread in page['threads']:
                            # Don't check threads we've already seen in order
                            # to only announce new found threads once
                            if thread['no'] in self.seen[board]:
                                continue

                            for keyword in self.watch[board]:
                                if keyword in thread.get('sub', '') or keyword in thread.get('com', ''):
                                    self.add_seen(board, thread, keyword)

                mutex.release()

            sleep(60)

    def add_seen(self, board, thread, keyword):
        self.seen[board].append(thread['no'])

        for sender in self.sender[keyword]:
            self.ircbot.fire(PRIVMSG(sender, "New '" + str(keyword) +
                "' thread found: https://boards.4chan.org/" + str(board) +
                "/thread/" + str(thread['no']))
            )

    def stop(self):
        print ("Stopping")
        self.running = False
