# Generic-DiscordBot
# author: github/adibarra

# imports
import re
import uuid
import time
import discord
import asgiref.sync
from DB_logger import Logger, Importance
from DB_database import DatabaseHandler
from DB_prefsloader import PreferenceLoader


class Command:
    """ Class to define what a command is """

    def run_command(self, transactionID: uuid, message: discord.Message, cmd_str: str):
        Logger.log('>> Called command: '+self.command_str, Importance.INFO, transactionID)
        Logger.log('>> Full command: '+cmd_str, Importance.INFO, transactionID)
        Logger.log(">> This is the default command's output", Importance.INFO, transactionID)
        Logger.log('>> Successfully ran default command', Importance.INFO, transactionID, final=True)
        return True

    def __init__(self, command_str: str, command_description: str, command_usage: str, command_aliases=[], command_action=run_command, is_enabled_global=True, is_enabled_server=True, is_superadmin_only=False, is_serveradmin_only=False, is_PMAllowed=False, is_PMOnly=False):
        self.command_str = command_str
        self.command_description = command_description
        self.command_usage = command_usage
        self.command_aliases = command_aliases
        self.run_command = command_action
        self.is_enabled_global = is_enabled_global
        self.is_enabled_server = is_enabled_server
        self.is_superadmin_only = is_superadmin_only
        self.is_serveradmin_only = is_serveradmin_only
        self.is_PMAllowed = is_PMAllowed
        self.is_PMOnly = is_PMOnly


class Utils:

    """ Class to hold misc. utility methods """

    # function to convert list to string for certain formats with padding
    # [[1, 1], [1,1], N] -> 1 : 1\n1 : 1\nN or [[1], [1], N] -> 1\n1\nN
    @staticmethod
    def list_to_str(list_to_convert: list, header1='Key', header2='Value', padding=10, headers=True):
        if len(list_to_convert) == 0:
            return '```asciidoc\nEmpty\n```'
        # str header
        if headers:
            longest_first = len(header1)
            longest_second = len(header2)
        else:
            longest_first = 0
            longest_second = 0

        inner_list = None
        for inner_list in list_to_convert:
            if len(inner_list) == 1:
                if len(str(inner_list[0])) > longest_first:
                    longest_first = len(str(inner_list[0]))
            if len(inner_list) == 2:
                if len(str(inner_list[0])) > longest_first:
                    longest_first = len(str(inner_list[0]))
                if len(str(inner_list[1])) > longest_second:
                    longest_second = len(str(inner_list[1]))

        longest_first += 4
        longest_second += 4

        full_str = '```asciidoc\n'
        if headers:
            if len(inner_list) == 2:
                full_str = '```asciidoc\n'+\
                    header1.center(longest_first, ' ')+'    '+header2.center(longest_second, ' ')+'\n'
                full_str += ''.center(longest_first, '=')+'----'+''.center(longest_second, '=')+'\n'

            elif len(inner_list) == 1:
                full_str = '```asciidoc\n'+header1.center(longest_first, ' ')+'\n'
                full_str += ''.center(longest_first, '=')+'\n'

        for inner_list in list_to_convert:
            if len(inner_list) == 2:
                full_str += (str(inner_list[0])+' ').rjust(longest_first)+' :: '+(' '+str(inner_list[1])).ljust(longest_second)+'\n'
            elif len(inner_list) == 1:
                full_str += str(inner_list[0])+'\n'
        return full_str+'```'

    # chunk a list
    @staticmethod
    def chunk_list(long_list, chunk_size):
        return [long_list[i*chunk_size:(i+1)*chunk_size] for i in range((len(long_list)+chunk_size-1) // chunk_size)]

    # get command prefix for a certain guild
    @staticmethod
    def getCmdPrefix(transactionID: uuid, guildID: int):
        return DatabaseHandler.getCMDPrefix(transactionID, guildID)

    # retreive whether a userid is globalbanned
    @staticmethod
    def isUserBanned(transactionID: uuid, userID: int):
        return DatabaseHandler.isUserIDGlobalBanned(transactionID, userID)

    # retreive whether a guildid is globalbanned
    @staticmethod
    def isGuildBanned(transactionID: uuid, guildID: int):
        return DatabaseHandler.isGuildIDGlobalBanned(transactionID, guildID)

    # retreive a list of server admins for a certain guild
    @staticmethod
    def get_serveradmins_for_guild(transactionID: uuid, guildID: int):
        serveradmin_ids = []
        server_admin_results = DatabaseHandler.getGuildAdminsTableContents(transactionID, guildID)

        # this table is structured differently from the others
        for user in server_admin_results:
            serveradmin_ids.append(int(user[0]))
        return serveradmin_ids

    # retreive list of all server admins for all guilds
    @staticmethod
    def get_all_serveradmins(transactionID: uuid):
        serveradmin_ids = []
        server_admin_tables = DatabaseHandler.sendQuery(transactionID, "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.tables WHERE TABLE_NAME LIKE '%GuildAdmins%';")

        # this table is structured differently from the others
        for server_admin_table_name in server_admin_tables:
            server_admins = DatabaseHandler.getGuildAdminsTableContents(
                transactionID, int(server_admin_table_name[0].split('GuildAdmins')[0]))
            for server_admin in server_admins:
                serveradmin_ids.append(int(server_admin[0]))
        return serveradmin_ids

    # retreive list of superadmins
    @staticmethod
    def get_superadmins():
        return PreferenceLoader.superadmin_ids

    # retreive and modify server settings table for a certain guild
    @staticmethod
    def modifyServerSettings(transactionID: uuid, guildID: int, key: str, value: str):
        server_settings_results = DatabaseHandler.getGuildSettingsTableContents(transactionID, guildID)
        for setting in server_settings_results:
            if setting[0].lower() == key.lower():
                DatabaseHandler.modifyGuildSettingsTable(transactionID, guildID, key, value)
                return True
        return False

    # retreive and modify global settings table for the bot
    @staticmethod
    def modifyGlobalSettings(transactionID: uuid, key: str, value: str):
        global_settings_results = DatabaseHandler.getGlobalSettingsTableContents(transactionID)
        for setting in global_settings_results:
            if setting[0].lower() == key.lower():
                DatabaseHandler.modifyGlobalSettingsTable(transactionID, key, value)
                return True
        return False

    # sanitize inputs for database
    @staticmethod
    def sanitize_for_DB(toSanitize: str):
        to_remove = ["'", '"', '\\*', 'CREATE', 'DATABASE', 'INSERT', 'SELECT', 'FROM', 'ALTER', 'ADD', 'DISTINCT',
                     'UPDATE', 'SET', 'DELETE', 'TRUNCATE', 'AS', 'ORDER', 'BY', 'ASC', 'DESC', 'BETWEEN', 'WHERE', 'AND',
                     'OR', 'NOT', 'LIMIT', 'NULL', 'DROP', 'IN', 'JOIN', 'UNION', 'ALL', 'EXISTS', 'LIKE', 'CASE', 'TABLES',
                     'SHOW']

        # remove all instances of strings in to_remove from input string
        for item in to_remove:
            toSanitize = re.sub(('(?i)'+item), '', toSanitize, flags=(re.IGNORECASE))
        return toSanitize

    @staticmethod
    def isValidInt(stringInt:str) -> bool:
        """Check if given str is valid int.
        
        Args:
            stringInt (str): The string to check for a valid int in
        
        Returns:
            bool: Indicates if the input was a valid int
        """
        
        try:
            int(stringInt)
            return True
        except ValueError:
            return False
    
    
    @staticmethod
    def isValidFloat(stringFloat:str) -> bool:
        """Check if given str is valid float.
        
        Args:
            stringFloat (str): The string to check for a valid float in
        
        Returns:
            bool: Indicates if the input was a valid float
        """
        
        try:
            float(stringFloat)
            return True
        except ValueError:
            return False

    @staticmethod
    def secondsToTime(secondsToConvert:int) -> str:
        """Convert from seconds to more readable format.\n
        Additionally, minutes will only be displayed if there are not enough seconds for a day and
        seconds will only be displayed if there are not enough seconds for an hour.\n
        This method does not support negative times, they will be forcibly made positive.\n
        Ex: 00181 secs (0 day(s), 0 hr(s), 3 min, 1 sec) -> 3 minutes 1 second
        Ex: 07381 secs (0 day(s), 2 hr(s), 3 min, 1 sec) -> 2 hours 3 minutes
        Ex: 93664 secs (1 day(s), 2 hr(s), 3 min, 1 sec) -> 1 day 2 hours
        
        Args:
            secondsToConvert (int): The number of seconds to convert into a time string
        
        Returns:
            str: The generated time string
        """
        
        days = 0
        hours = 0
        minutes = 0
        result_str = ''
        secondsToConvert = abs(secondsToConvert)

        while secondsToConvert >= 60*60*24:
            secondsToConvert -= 60*60*24
            days += 1
        while secondsToConvert >= 60*60:
            secondsToConvert -= 60*60
            hours += 1
        while secondsToConvert >= 60:
            secondsToConvert -= 60
            minutes += 1

        if days > 0:
            result_str += str(days)+' day'
            if days != 1:
                result_str += 's'
        
        if hours > 0:
            if result_str:
                result_str += ' '
            result_str += str(hours)+' hour'
            if hours != 1:
                result_str += 's'

        if minutes > 0 and days == 0:
            if result_str:
                result_str += ' '
            result_str += str(minutes)+' minute'
            if minutes != 1:
                result_str += 's'

        if secondsToConvert >= 0 and hours == 0 and days == 0 and not (secondsToConvert == 0 and minutes > 0):
            if result_str:
                result_str += ' '
            result_str += str(secondsToConvert)+' second'
            if secondsToConvert != 1:
                result_str += 's'
        return result_str

    # send a discord message without using async 'await'
    @staticmethod
    @asgiref.sync.async_to_sync
    async def send_message_sync(channel: discord.abc.Messageable, message: str):
        return await channel.send(message)

    # send a user a DM
    @staticmethod
    async def send_user_DM(transactionID: uuid, client: discord.Client, userID: int, message: str):
        dm_user = client.get_user(userID)
        if dm_user == None:
            Logger.log(">> Attempted DM: Not in mutual server with user("+str(userID)+")", transactionID)
        else:
            user_dm = dm_user.dm_channel
            if user_dm == None:
                user_dm = await dm_user.create_dm()
            await user_dm.send(message)
        return False

    # send user a DM without using async 'await'
    @staticmethod
    @asgiref.sync.async_to_sync
    async def send_user_DM_sync(transactionID: uuid, client: discord.Client, userID: int, message: str):
        return await Utils.send_user_DM(transactionID, client, userID, message)

    # send user an embed through DM
    @staticmethod
    async def send_user_embed_DM(transactionID: uuid, client: discord.Client, userID: int, embed: discord.Embed):
        dm_user = client.get_user(userID)
        if dm_user == None:
            Logger.log(">> Attempted DM: Not in mutual server with user("+str(userID)+")", transactionID)
        else:
            user_dm = dm_user.dm_channel
            if user_dm == None:
                user_dm = await dm_user.create_dm()
            await user_dm.send(embed=embed)
        return False

    # send user an embed through DM without using async 'await'
    @staticmethod
    @asgiref.sync.async_to_sync
    async def send_user_embed_DM_sync(transactionID: uuid, client: discord.Client, userID: int, embed: discord.Embed):
        return await Utils.send_user_embed_DM(transactionID, client, userID, embed)

    # check database connection
    @staticmethod
    async def checkDBConnection(client: discord.Client, importance: Importance = Importance.CRIT, transactionID: uuid = None):
        if DatabaseHandler.checkDBConnection():
            Logger.log('Connected to database!', importance)
            return True
        else:
            emergency_alert_user = client.get_user(
                PreferenceLoader.emergency_alert_user_id)

            if importance != None:
                Logger.log('!!! Unable to reach database !!! @ '+time.strftime('%Y-%m-%d %H:%M:%S'), importance)
            if emergency_alert_user == None:
                Logger.log("Not in a mutual server with the emergency alert user, can't DM them!", importance)
            else:
                alert_user_dm = emergency_alert_user.dm_channel
                if alert_user_dm == None:
                    alert_user_dm = await emergency_alert_user.create_dm()
                await alert_user_dm.send('!!! Unable to reach database !!! @ '+time.strftime('%Y-%m-%d %H:%M:%S')+'\n'+'DATABASE ERROR: '+DatabaseHandler.checkDBConnectionError())
                Logger.log('Sent the emergency alert user a DM!', importance)
            return False

    # check if user has permissions to use command
    @staticmethod
    async def is_user_allowed(transactionID: uuid, message: discord.Message, command: Command):
        if message.author.id in Utils.get_superadmins():
            Logger.log('> Permissions Success: SuperAdmin Permissions Override: User('+str(message.author.id)+')', Importance.INFO, transactionID)
            return True

        if command.is_superadmin_only:
            Logger.log('>> Permissions Error: Invalid Permissions: User('+str(message.author.id)+') attempted to use SuperAdmin command', Importance.INFO, transactionID)
            return False

        if command.is_enabled_global:
            if command.is_enabled_server:
                if command.is_serveradmin_only:
                    if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                        if message.author.id in Utils.get_serveradmins_for_guild(transactionID, message.guild.id):
                            Logger.log('> Permissions Success: User('+str(message.author.id)+') is registered as a server admin', Importance.INFO, transactionID)
                            return True
                        else:
                            # check if sender has administrator privilages in server, if so add them
                            if message.author.guild_permissions.administrator:
                                DatabaseHandler.addGuildAdmin(transactionID, message.guild.id, message.author.id)
                                Logger.log('> Permissions Success: User('+str(message.author.id)+') is a server administrator and has been registered as a server admin', Importance.INFO, transactionID)
                                return True
                            else:
                                Logger.log('>> Permissions Error: User('+str(message.author.id)+') is not registered as a server admin', Importance.INFO, transactionID)
                                return False
                    else:
                        await message.channel.send('This command can only be used in a server.')
                        Logger.log('>> Command Error: Command only works in servers', Importance.INFO, transactionID)
                        return False
                else:
                    Logger.log('> Permissions Success: User('+str(message.author.id)+') ran a Public Command / No Restrictions', Importance.INFO, transactionID)
                    return True
            else:
                Logger.log('>> Command Error: Command disabled on this server', Importance.INFO, transactionID)
                return False
        else:
            Logger.log('>> Command Error: Command disabled globaly', Importance.INFO, transactionID)
            return False
