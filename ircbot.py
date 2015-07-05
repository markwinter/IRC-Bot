#!/usr/bin/env python
import sys
from linkresolver import LinkResolver
from watcher import Watcher
from re import findall
from circuits import Debugger
from circuits import Component
from circuits.net.sockets import TCPClient, connect
from circuits.protocols.irc import IRC, PRIVMSG, USER, NICK, JOIN
from circuits.protocols.irc import ERR_NICKNAMEINUSE
from circuits.protocols.irc import RPL_ENDOFMOTD, ERR_NOMOTD

class Source():
    def execute(self, keywords, target, source, ircbot):
        ircbot.fire(PRIVMSG(target, "Source available here: https://github.com/Astonex/IRC-Bot/"))

    def usage(self):
        pass

class Join():
    def execute(self, keywords, target, source, ircbot):
        if len(keywords) != 2:
            return -1

        if source[0] == "astonex" or source[0] == "softkitty":
            ircbot.fire(JOIN(keywords[1]))
        else:
            ircbot.fire(PRIVMSG(target, "Must be authorised to use this command"))

    def usage(self):
        return "Usage: !join <channel name>"

class Commands():
    def execute(self, keywords, target, source, ircbot):
        ircbot.fire(PRIVMSG(target, ircbot.list_commands()))

    def usage(self):
        pass

class Bot(Component):
    def init(self, host="irc.freenode.net", port="6667", channel="softkitty"):
        self.host = host
        self.port = int(port)
        self.nick = "fluffybot"
        self.password = open("password").read().strip()

        self.command_char = "!"

        self.linkresolver = LinkResolver()

        self.commands = {
            'commands': Commands(),
            'help': Commands(),
            'join': Join(),
            'source': Source(),
            'watch': Watcher()
        }

        TCPClient(channel=self.channel).register(self)
        IRC(channel=self.channel).register(self)

    def ready(self, component):
        """ Ready Event.

        Triggered by the underlying tcpclient Component when it is ready to
        start making a new connection.
        """

        self.fire(connect(self.host, self.port))

    def connected(self, host, port):
        """Connected Event.

        Triggered by the underlying tcpclient Component when a successfully
        connection has been made.
        """

        self.fire(NICK(self.nick))
        self.fire(USER(self.nick, self.nick, host, "Link Resolver Bot"))

    def disconnected(self):
        """Disconnected Event.

        Triggered by the underlying tcpclient Component when the connection is lost
        """

        raise SystemExit(0)

    def numeric(self, source, numeric, *args):
        """Numeric Event.

        Triggered by the irc Protocol Component when we have received an irc
        Numberic Event from server we are connected to
        """

        # if nick is in use add an _ to the end of our name
        if numeric == ERR_NICKNAMEINUSE:
            self.fire(NICK("{0:s}_".format(args[0])))

        # else wait for end of motd to start sending commands
        elif numeric in (RPL_ENDOFMOTD, ERR_NOMOTD):
            self.fire(PRIVMSG("NICKSERV", "IDENTIFY " + self.password))

    def privmsg(self, source, target, message):
        """Message Event.

        Triggered by the irc Protocol Component for each message we receieve
        from the server
        """

        if message[:1] == self.command_char:
            self.parse(message, source, target)

        else:
            urls = findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", message)
            if urls:
                title = self.linkresolver.get_title(urls[0])
                self.fire(PRIVMSG(target, title))

    def parse(self, message, source, target):
        keywords = message.split(' ')

        for key in self.commands:
            if key == keywords[0][1:]:
                response = self.commands[key].execute(keywords, target, source, self)

                if response == -1:
                    self.fire(PRIVMSG(target, self.commands[key].usage()))

                break

    def list_commands(self):
        list = ""

        for key in self.commands:
            list += self.command_char + str(key) + " "

        return "Available commands: " + list

bot = Bot(*sys.argv[1:])
Debugger().register(bot)
bot.run()
