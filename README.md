# IRC-Bot

Python IRC Bot


### Adding commands to the bot

- Create a new appropriately named file for your command
- In the new file implement a class that has the methods `execute(self, keywords, target, source, ircbot)` and `usage(self)`
- Import your command in ircbot.py
- Add your command to the list of commands in the `init` of Bot() in ircbot.py
