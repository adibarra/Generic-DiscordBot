# Generic-DiscordBot

This project is based on [discord<span></span>.py](https://discordpy.readthedocs.io/en/latest/) and is meant to be a 'Quick Start Bot' to cut down on the time it takes to write complex discord bots.

NOTE: Written for python 3. Last updated [2020-12-20].

---

## Features:
- Full multi-server support
  - Per-server bot settings
  - Per-server command prefix
  - Global bot settings
  - Ban a user globally or a guild from using the bot
- Useful bot admin utilites
  - Get invite to requested server
  - Have the bot echo your message
  - Detailed logging
  - Automated testing
- Easy to add new commands and games
  - Add command aliases
  - Define permission levels
  - Set commands to DM only
  - Add command descriptions and usage information
  - No need to worry about restarting bot during any running games
- Custom help messages based on user's permission level (superadmin, server admin, user)
- Get notified if the bot is unable to access the database

And any other bot/server specific features you wish to write!

---

## Version 1.0 Checklist:
- [ ] Broadcast message to bot server admins
- [ ] Switch help and settings commands to use interactive embeds
- [ ] Enable/disable commands on global level
- [ ] Enable/disable commands on server level
- [ ] Restrict commands to certain channels on server level
- [x] Chunk and zip log files if size exceeds limit

---

## Setup Instructions:

1. **Install Python Dependencies:**
    - [discord.<span></span>py](https://pypi.org/project/discord.py/)
    - [PyMySQL](https://pypi.org/project/PyMySQL/)
    - [asgiref](https://pypi.org/project/asgiref/)

    ```
    $ python3 -m pip install discord.py
    $ python3 -m pip install pymysql
    $ python3 -m pip install asgiref
    ```

2. **Install MySQL:**
    - After installing make sure to [create a database](https://www.digitalocean.com/community/tutorials/a-basic-mysql-tutorial) for the bot to use.

3. **Place bot files directory in '/usr/local/lib/':**
    - After placing the files, make update the [file permissions](https://chmodcommand.com/chmod-644/)
        ```
        $ sudo chown root:root /usr/local/lib/Generic-DiscordBot/src/DB_main.py
        $ sudo chmod 644 /usr/local/lib/Generic-DiscordBot/src/DB_main.py
        ```

4. **Set up discord bot user**
    - Go to the [discord developer portal](https://discord.com/developers/applications) create an application.
    - Create a bot user for your application.
    - Enable the 'Server Members Intent' setting under the 'Privileged Gateway Intents' section.

5. **Update the bot's settings:**
    - Update the prefs.json file found in the /res folder.
    - If not present run the bot once to generate both the folder and file.
    - Bot tester client token is only necessary when running the tester bot.

6. **Allow bot's stop and start to be handled by systemd:**
    - Place 'generic_bot.service' in '/etc/systemd/system/'
    - Then run:
        ```
        $ sudo chown root:root /etc/systemd/system/generic_bot.service
        $ sudo chmod 644 /etc/systemd/system/generic_bot.service

        $ sudo systemctl daemon-reload
        $ sudo systemctl enable generic_bot
        ```

Visit [here](https://github.com/torfsen/python-systemd-tutorial) to learn more about systemd and unit files

7. **Check if the bot's service is enabled properly:**
    ```
    $ sudo systemctl list-unit-files | grep generic_bot
    generic_bot.service                enabled
    ```

8. **Start / stop the bot's service:**

    ```
    $ sudo systemctl start generic_bot
    $ sudo systemctl stop generic_bot
    $ sudo systemctl restart generic_bot
    $ sudo systemctl status generic_bot
    ```

---

And you're done! The bot automatically creates all of the folders, files, and database tables it uses as needed.
