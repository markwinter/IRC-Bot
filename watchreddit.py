from collections import defaultdict
from requests import get
from simplejson import loads
from threading import Thread, Lock
from time import sleep
from circuits.protocols.irc import PRIVMSG
import string

mutex = Lock()

class WatchReddit(Thread):
    def __init__(self, ircbot):
        Thread.__init__(self)

        self.ircbot = ircbot

        self.base_url = "https://reddit.com/r/"

        self.watch = defaultdict(list)
        self.seen = defaultdict(list)
        self.sender = defaultdict(list)

        self.running = True
        self.setDaemon(True)
        self.start()

    def execute(self, keywords, target, source, ircbot):
        if len(keywords) != 3:
            return -1

        sub = keywords[1]
        keyword = keywords[2]

        # Only accept keywords 3 letters or more
        if len(keyword) < 3:
            return -1

        # Check for ascii only letters
        if not all(x in string.printable for x in keyword):
            return -1

        mutex.acquire()
        try:
            self.watch[sub].append(keyword)
            self.sender[keyword].append(target)
        finally:
            mutex.release()

        self.ircbot.fire(PRIVMSG(target, "Now watching for '" + str(keyword) + "' on /r/" + str(sub)))

    def usage(self):
        return "!reddit <subreddit> <keyword> - keyword must be at least 3 letters and ascii only"

    def run(self):
        while self.running:
            for sub in self.watch:
                mutex.acquire()

                if len(self.watch[sub]) > 0:
                    # Reddit API policy says to use a unique user-agent
                    headers = { 'User-Agent': 'Fluffybot IRC Bot by /u/astonex'}
                    response = get(self.base_url + sub + "/new.json", timeout=3, headers=headers)
                    json = loads(response.text)

                    data = json['data']

                    for child in data['children']:
                        post = child['data']

                        if post['name'] in self.seen[sub]:
                            continue

                        for keyword in self.watch[sub]:
                            if (keyword.lower() in post.get('title', '').lower() or
                                keyword.lower() in post.get('selftext', '').lower()):

                                self.seen[sub].append(post['name'])

                                for sender in self.sender[keyword]:
                                    self.ircbot.fire(PRIVMSG(sender,
                                    "New '" + str(keyword) + "' thread found on /r/" +
                                    str(sub) + " " + self.base_url + str(post['permalink'][3:])))

                mutex.release()

            sleep(60)
