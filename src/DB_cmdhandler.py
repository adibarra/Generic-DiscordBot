# Generic-DiscordBot
# author: github/adibarra

# imports
import uuid
import discord
import traceback
from DB_commands import *
from DB_utils import Utils
from DB_logger import Logger, Importance


class CommandHandler:
    """ Class to handle commands """
    client = None
    commands_list = []

    # create command list
    def __init__(self, disClient: discord.Client):
        CommandHandler.commands_list = []
        CommandHandler.client = disClient

    # register commands to commandhandler
    def registerCommands(self):
        CommandHandler.commands_list = BotCommands.getCommands(
            CommandHandler.client)

    # return command by cmd_str lookup
    async def get_command(self, transactionID: uuid, bot_cmd_prefix: str, message: discord.Message):
        if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
            full_cmd_str = message.content
            full_cmd_str = full_cmd_str[len(bot_cmd_prefix):]
            cmd_str = full_cmd_str.split(' ')[0]
        else:
            # if in PM dont check for cmd prefix
            full_cmd_str = message.content
            cmd_str = full_cmd_str.split(' ')[0]

        # check via command name
        for cmd in CommandHandler.commands_list:
            if cmd.command_str.lower() == cmd_str.lower():
                return cmd

        # check via command aliases
        for cmd in CommandHandler.commands_list:
            for alias in cmd.command_aliases:
                if alias.lower() == cmd_str.lower():
                    return cmd

        Logger.log('> User('+str(message.author.id)+'), Command does not exist: '+full_cmd_str, Importance.INFO, transactionID)
        return None

    # check command validity then run command
    async def run_command(self, transactionID: uuid, bot_cmd_prefix: str, message: discord.Message):
        # remove prefix and split cmd from args
        if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
            full_cmd_str = message.content
            full_cmd_str = full_cmd_str[len(bot_cmd_prefix):]
            command = await self.get_command(transactionID, bot_cmd_prefix, message)
        else:
            # if in PM dont check for cmd prefix
            full_cmd_str = message.content
            command = await self.get_command(transactionID, bot_cmd_prefix, message)

        # if command is registered
        if command != None:
            # does user have permissions for command
            user_permitted = await Utils.is_user_allowed(transactionID, message, command)

            if user_permitted:
                if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                    if not command.is_PMOnly:
                        try:
                            return await command.run_command(command, transactionID, message, full_cmd_str)
                        except Exception as e:
                            Logger.log(('RUNTIME ERROR: (See Console for Details) '+str(e.args)), Importance.CRIT, transactionID)
                            print(traceback.format_exc())

                    else:
                        Logger.log('> Failed to run command (PM only): '+full_cmd_str, Importance.INFO, transactionID)
                        return False

                elif command.is_PMAllowed:
                    try:
                        return await command.run_command(command, transactionID, message, full_cmd_str)
                    except Exception as e:
                        Logger.log(('RUNTIME ERROR: (See Console for Details) '+str(e.args)), Importance.CRIT, transactionID)
                        print(traceback.format_exc())

                else:
                    await message.channel.send('This command cannot be run in PM')
                    Logger.log('> Failed to run command (PM not allowed): '+full_cmd_str, Importance.INFO, transactionID)
                    return False
            else:
                Logger.log('> Failed to run command (Silent fail: missing perms): '+full_cmd_str, Importance.INFO, transactionID)
                return user_permitted
        else:
            return False
