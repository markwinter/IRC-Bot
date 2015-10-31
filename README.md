# IRC-Bot

Python IRC Bot

### Using this bot

Everything that needs to be changed to make the bot your own is in the parameters of `init` of `Bot` in ircbot.py.

You will also need to create two files in the directory ircbot.py resides in, one for your password and one for your host.
By default these files are called `password` and `host` but can be changed for each bot using the `password_file` and `host_file`
parameters.

To create multiple instances of bots, you use the channel variable passed to `init` using a unique
name each time.

### Adding commands to the bot

- Create a new appropriately named file for your command
- In the new file implement a class that has the method `execute(self, keywords, target, source, ircbot)`
- Improper usage of a command should return -1 in `execute` and define the usage string in `usage`
- Import your class in ircbot.py
- Add your command to the list of commands in the `init` of Bot() in ircbot.py
