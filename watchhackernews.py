from threading import Thread, Lock
from time import sleep
from simplejson import loads
from collections import defaultdict
from circuits.protocols.irc import PRIVMSG
from requests import get
import string

mutex = Lock()

class WatchHackerNews(Thread):
    def __init__(self, ircbot):
        Thread.__init__(self)

        self.ircbot = ircbot

        self.base_url = "https://hacker-news.firebaseio.com/v0/"

        self.watch = []
        self.sender = defaultdict(list)

        self.last_checked = 0

        self.running = True
        self.setDaemon(True)
        self.start()

    def execute(self, keywords, target, source, ircbot):
        # Check for right amount of keywords for command
        if len(keywords) != 2:
            ircbot.fire(PRIVMSG(target, usage()))

        # Only accept keywords 3 letters or more
        if len(keywords[1]) < 3:
            ircbot.fire(PRIVMSG(target, usage()))

        # Check for ascii only letters
        if not all(x in string.printable for x in keywords[1]):
            ircbot.fire(PRIVMSG(target, usage()))

        # Check we're not already watching this keyword for this target
        with mutex:
            if self.sender[keywords[1]] and target in self.sender[keywords[1]]:
                ircbot.fire(PRIVMSG(target, "Already watching for this keyword in this channel"))
                return

        with mutex:
            self.watch.append(keywords[1])
            self.sender[keywords[1]].append(target)

        self.ircbot.fire(PRIVMSG(target, "Now watching for '" + str(keywords[1] + "' on HN")))

    def usage(self):
        return "!hn <keyword> - keyword must be 3 or more letters and ascii only"

    def run(self):
        while self.running:
            try:

                with mutex:
                    keywords_exist = len(self.watch) > 0

                # Only need to do something once we have our first keyword to monitor
                if keywords_exist:
                    response = get(self.base_url + "newstories.json", timeout=3)
                    json = loads(response.text)

                    max_id = 0
                    for story_id in json:
                        # Update max_id
                        if story_id > max_id:
                            max_id = story_id

                        # Don't check posts we've already checked before
                        if story_id <= self.last_checked:
                            break

                        story_json = get(self.base_url + "item/" + str(story_id) + ".json", timeout=3)
                        story = loads(story_json.text)

                        with mutex:
                            watch = self.watch
                            sender = self.sender

                        for keyword in watch:
                            if keyword.lower() in story.get('title', '').lower():
                                for sender in sender[keyword]:
                                    self.ircbot.fire(PRIVMSG(sender,
                                    "Found new '" + str(keyword) + "' story on HN: " +
                                    "https://news.ycombinator.com/item?id=" + str(story_id)))

                    # Update last new thread seen so we only check newer ones next time
                    # Assumption here is HN API orders their new stories 'json' in desc order
                    self.last_checked = max_id

            except:
                pass

            sleep(120)
