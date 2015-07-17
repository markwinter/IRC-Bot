from threading import Thread
from circuits.protocols.irc import PRIVMSG
import random
import time

class Quote(Thread):
    def __init__(self):
        Thread.__init__(self)

        self.quotes = []

        self.running = False
        self.setDaemon(True)
        self.start()

    def execute(self, keywords, target, source, ircbot):
        if len(keywords) < 2:
            return -1

        if keywords[1] == "add":
            # Check they gave a quote
            if len(keywords) < 3:
                return -1

            # Combine list into string
            quote = ' '.join(keywords[2:])

            # Prefix date and time
            quote_time = time.strftime("%H:%M:%S")
            quote_date = time.strftime("%d/%m/%Y")

            quote = "" + quote_date + " " + quote_time + " || " + quote

            self.quotes.append(quote)
            ircbot.fire(PRIVMSG(target, "Added quote #" + str(len(self.quotes) - 1)))

        elif keywords[1] == "del":
            if len(keywords) != 3:
                return -1

            quote = int(keywords[2])

            if quote < 0 or quote >= len(self.quotes):
                ircbot.fire(PRIVMSG(target, "Invalid quote id"))
                return

            del self.quotes[quote]
            ircbot.fire(PRIVMSG(target, "Deleted quote"))

        elif keywords[1] == "random":
            if len(self.quotes) == 0:
                ircbot.fire(PRIVMSG(target, "No quotes in system"))
                return
            elif len(self.quotes) == 1:
                quote = self.quotes[0]
                quote = "#0 " + quote
                ircbot.fire(PRIVMSG(target, quote))
            else:
                num = random.randrange(len(self.quotes) - 1)
                quote = self.quotes[num]
                ircbot.fire(PRIVMSG(target, quote))

        elif keywords[1] == "get":
            if len(keywords) != 3:
                return -1

            if self.quotes[int(keywords[2])]:
                quote = self.quotes[int(keywords[2])]
                quote = "#" + str(int(keywords[2])) + " " + quote
                ircbot.fire(PRIVMSG(target, quote))
            else:
                ircbot.fire(PRIVMSG(target, "Invalid quote id"))

        else:
            return -1

    def usage(self):
        return "!quote [add <quote> | del <id> | random | get <id>]"
