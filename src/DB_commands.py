# Generic-DiscordBot
# author: github/adibarra

# imports
import re
import uuid
import discord
from DB_games import *
from DB_utils import Utils, Command
from DB_database import DatabaseHandler
from DB_logger import Logger, Importance
from DB_prefsloader import PreferenceLoader


class BotCommands:
    """ Class to store all bot commands """
    client = None
    commands_list = []

    @staticmethod
    # add all bot commands here
    def getCommands(disClient: discord.Client):

        # initialize client
        BotCommands.client = disClient

        async def inviteCommand(self, transactionID, message, cmd_str):
            Logger.log('>> Called command: '+self.command_str, Importance.INFO, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            try:
                if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                    # try deleting original command call message to reduce spam if not in DMs
                    await message.delete()
            except Exception as e:
                # probably dont have perms, oh well
                pass

            else:
                inviteStr = ('Click this link to invite me to your server!\n'
                +'Invite Link: https://discord.com/api/oauth2/authorize?client_id='
                +str(disClient.user.id)+'&permissions=76865&scope=bot')
                await Utils.send_user_DM(transactionID, BotCommands.client, message.author.id, inviteStr)
                return True

        async def serverAdminsCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.INFO, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            cmd_prefix = '\u200e'  # << BLANK CHARACTER
            if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                cmd_prefix = Utils.getCmdPrefix(transactionID, message.guild.id)

                # check if all cmd arguments are present
                cmd_args = cmd_str.split(' ')
                if len(cmd_args) >= 2:
                    # check if cmd is show
                    if cmd_args[1].lower() == 'show':
                        bot_admins_str = ''
                        for user in DatabaseHandler.getGuildAdminsTableContents(transactionID, message.guild.id):
                            tempUser = discord.Client.get_user(BotCommands.client, int(user[0]))
                            if tempUser != None:
                                bot_admins_str += tempUser.name+'#'+tempUser.discriminator+'\n'
                            else:
                                bot_admins_str += 'Unable to resolve: '+str(user[0])+'\n'
                        await message.channel.send('__Bot Admins on this server:__\n'+bot_admins_str)
                        return True

                    # check if cmd is add
                    elif cmd_args[1].lower() == 'add':
                        if len(cmd_args) == 3:
                            # complete serveradmin table update
                            newUserID = int(''.join(re.findall('\\d+', cmd_args[2])))
                            tempUser = discord.Client.get_user(BotCommands.client, newUserID)

                            if DatabaseHandler.addGuildAdmin(transactionID, message.guild.id, newUserID):
                                await message.channel.send('Successfully added new server bot admin: '+tempUser.name+'#'+tempUser.discriminator)
                                return True
                            else:
                                await message.channel.send(tempUser.name+'#'+tempUser.discriminator+' is already a server bot admin!')
                                return False
                        else:
                            await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                            return False

                    # check if cmd is remove
                    elif cmd_args[1].lower() == 'remove':
                        if len(cmd_args) == 3:
                            # complete serveradmin table update
                            removeUserID = int(''.join(re.findall('\\d+', cmd_args[2])))
                            tempUser = discord.Client.get_user(BotCommands.client, removeUserID)

                            if message.guild.owner.id == removeUserID:
                                await message.channel.send('Can not remove server owner as bot admin')
                                return False
                            elif message.author.id == removeUserID:
                                await message.channel.send('Can not remove yourself as bot admin')
                                return False
                            else:
                                if DatabaseHandler.removeGuildAdmin(transactionID, message.guild.id, removeUserID):
                                    await message.channel.send('Successfully removed server bot admin: '+tempUser.name+'#'+tempUser.discriminator)
                                    return True
                                else:
                                    await message.channel.send(tempUser.name+'#'+tempUser.discriminator+" isn't a server bot admin!")
                                    return False
                    else:
                        await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                        return False
                # else invalid arg was used
                else:
                    await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                    return False
            # not enough args
            else:
                await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                return False

        async def serverSettingsCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.INFO, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            cmd_prefix = '\u200e'  # << BLANK CHARACTER
            if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                cmd_prefix = Utils.getCmdPrefix(transactionID, message.guild.id)

            # check if all cmd arguments are present
            cmd_args = cmd_str.split(' ')
            if len(cmd_args) >= 2:
                # check if cmd is show
                if cmd_args[1].lower() == 'show':
                    await message.channel.send('Current Server Settings:\n'+Utils.list_to_str(DatabaseHandler.getGuildSettingsTableContents(transactionID, message.guild.id)))
                    return True

                    # check if cmd is modify
                elif cmd_args[1].lower() == 'modify':
                    if len(cmd_args) == 4:

                        # check new prefix is between 1 and 3 chars inclusive
                        if cmd_args[2].lower() == 'prefix':
                            # sanitize inputs...
                            unsan_prefix = cmd_args[3]
                            cmd_args[3] = Utils.sanitize_for_DB(cmd_args[3])

                            if len(cmd_args[3]) > 3:
                                await message.channel.send("Unable to update key: '**prefix**' must be between 1 and 3 chars")
                                return False
                            elif len(cmd_args[3]) < 1:
                                await message.channel.send("Unable to update key: '**prefix**' must be between 1 and 3 chars. (You probably used a banned word sorry!)")
                                Logger.log('>> Attempted to update prefix to a banned word!', Importance.WARN, transactionID)
                                Logger.log('>> Failed to update prefix in Guild('+str(message.guild.id)+") to value '"+unsan_prefix+"'", Importance.WARN, transactionID)
                                return False

                        # only allow settings to update if handling for key is programmed in
                        else:
                            await message.channel.send("Unable to find key '**"+cmd_args[2]+"**'")
                            return False

                        # complete settings update
                        if Utils.modifyServerSettings(transactionID, message.guild.id, cmd_args[2], cmd_args[3]):
                            await message.channel.send("Successfully updated key '**"+cmd_args[2]+"**' to value '**"+cmd_args[3]+"**'")
                            Logger.log(">> Successfully updated key '"+cmd_args[2]+"' to value '"+cmd_args[3]+"'", Importance.INFO, transactionID)
                            return True
                        else:
                            await message.channel.send("Unable to find key '**"+cmd_args[2]+"**'")
                            return False
                    else:
                        await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                        return False

                # else invalid arg was used
                else:
                    await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                    return False

            # not enough args
            else:
                await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                return False

        async def globalSettingsCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.INFO, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            cmd_prefix = '\u200e'  # << BLANK CHARACTER
            if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                cmd_prefix = Utils.getCmdPrefix(transactionID, message.guild.id)

            # check if all cmd arguments are present
            cmd_args = cmd_str.split(' ')
            if len(cmd_args) >= 2:
                # check if cmd is show
                if cmd_args[1].lower() == 'show':
                    await message.channel.send('Current Global Settings:\n'+Utils.list_to_str(DatabaseHandler.getGlobalSettingsTableContents(transactionID)))
                    return True

                # check if cmd is modify
                elif cmd_args[1].lower() == 'modify':
                    if len(cmd_args) == 4:
                        # This is a superadmin command: only checks for existance of the key, not for validity of the new value
                        # complete settings update if key exists
                        if Utils.modifyGlobalSettings(transactionID, cmd_args[2], cmd_args[3]):
                            await message.channel.send("Successfully updated key '**"+cmd_args[2]+"**' to value '**"+cmd_args[3]+"**'")
                            return True
                        else:
                            await message.channel.send("Unable to find key '**"+cmd_args[2]+"**'")
                            return False
                    else:
                        await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                        return False

                # else invalid arg was used
                else:
                    await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                    return False

            # not enough args
            else:
                await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                return False

        async def userGlobalBansCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.INFO, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            cmd_prefix = '\u200e'  # << BLANK CHARACTER
            if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                cmd_prefix = Utils.getCmdPrefix(transactionID, message.guild.id)

            # check if all cmd arguments are present
            cmd_args = cmd_str.split(' ')
            if len(cmd_args) >= 2:
                # check if cmd is show
                if cmd_args[1].lower() == 'show':
                    bot_bans_str = ''
                    for user in DatabaseHandler.getUserGlobalBansTableContents(transactionID):
                        tempUser = discord.Client.get_user(BotCommands.client, int(user[0]))
                        if tempUser != None:
                            bot_bans_str += tempUser.name+'#'+tempUser.discriminator+'\n'
                        else:
                            bot_bans_str += 'Unable to resolve: UserID: '+str(user[0])+'\n'
                    if bot_bans_str == '':
                        bot_bans_str = '[Empty for now...]'
                    await message.channel.send('__All Globally Banned Users__\n'+bot_bans_str)
                    return True

                # check if cmd is add
                elif cmd_args[1].lower() == 'add':
                    if len(cmd_args) == 3:
                        # complete userbans table update
                        newUserID = int(''.join(re.findall('\\d+', cmd_args[2])))
                        tempUser = discord.Client.get_user(BotCommands.client, newUserID)

                        if newUserID in Utils.superadmin_ids:
                            await message.channel.send('Can not Globally Ban a SuperAdmin!')
                            return False

                        if message.author.id == newUserID:
                            await message.channel.send('Can not Globally Ban yourself!')
                            return False

                        if DatabaseHandler.addUserGlobalBan(transactionID, newUserID):
                            await message.channel.send('Successfully added new User Global Ban: '+tempUser.name+'#'+tempUser.discriminator)
                            return True
                        else:
                            await message.channel.send(tempUser.name+'#'+tempUser.discriminator+' is already Globally Banned!')
                            return False
                    else:
                        await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                        return False

                # check if cmd is remove
                elif cmd_args[1].lower() == 'remove':
                    if len(cmd_args) == 3:
                        # complete userbans table update
                        removeUserID = int(''.join(re.findall('\\d+', cmd_args[2])))
                        tempUser = discord.Client.get_user(BotCommands.client, removeUserID)

                        if tempUser != None:
                            if DatabaseHandler.removeUserGlobalBan(transactionID, removeUserID):
                                await message.channel.send('Successfully removed User Global Ban: '+tempUser.name+'#'+tempUser.discriminator)
                                return True
                            else:
                                await message.channel.send(tempUser.name+'#'+tempUser.discriminator+" isn't Globally Banned!")
                                return False
                        else:
                            if DatabaseHandler.removeUserGlobalBan(transactionID, removeUserID):
                                await message.channel.send('Successfully removed User Global Ban: UserID('+str(removeUserID)+')')
                                return True
                            else:
                                await message.channel.send('UserID('+str(removeUserID)+") isn't Globally Banned!")
                                return False
                    else:
                        await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                        return False

                # else invalid arg was used
                else:
                    await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                    return False

            # not enough args
            else:
                await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                return False

        async def guildGlobalBansCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.INFO, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            cmd_prefix = '\u200e'  # << BLANK CHARACTER
            if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                cmd_prefix = Utils.getCmdPrefix(transactionID, message.guild.id)

            # check if all cmd arguments are present
            cmd_args = cmd_str.split(' ')
            if len(cmd_args) >= 2:
                # check if cmd is show
                if cmd_args[1].lower() == 'show':
                    bot_bans_str = ''
                    for guild in DatabaseHandler.getGuildGlobalBansTableContents(transactionID):
                        tempGuild = discord.Client.get_guild(BotCommands.client, int(guild[0]))

                        if tempGuild != None:
                            bot_bans_str += tempGuild.name+' | GuildID:'+str(guild[0])+'\n'
                        else:
                            bot_bans_str += 'Unable to resolve: GulidID:'+str(guild[0])+'\n'

                    if bot_bans_str == '':
                        bot_bans_str = '[Empty for now...]'
                    await message.channel.send('__All Globally Banned Guilds__\n'+bot_bans_str)
                    return True

                # check if cmd is add
                if cmd_args[1].lower() == 'add':
                    if len(cmd_args) == 3:
                        # complete guildbans table update
                        newGuildID = int(''.join(re.findall('\\d+', cmd_args[2])))
                        tempGuild = discord.Client.get_guild(BotCommands.client, newGuildID)

                        if DatabaseHandler.addGuildGlobalBan(transactionID, newGuildID):
                            await message.channel.send('Successfully added new Guild Global Ban: '+tempGuild.name+' | GuildID:'+str(newGuildID))
                            return True
                        else:
                            await message.channel.send(tempGuild.name+' | GuildID:'+str(newGuildID)+' is already Globally Banned!')
                            return False
                    else:
                        await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                        return False

                # check if cmd is remove
                elif cmd_args[1].lower() == 'remove':
                    if len(cmd_args) == 3:
                        # complete guildbans table update
                        removeGuildID = int(''.join(re.findall('\\d+', cmd_args[2])))
                        tempGuild = discord.Client.get_guild(BotCommands.client, removeGuildID)

                        if tempGuild != None:
                            if DatabaseHandler.removeGuildGlobalBan(transactionID, removeGuildID):
                                await message.channel.send('Successfully removed Guild Global Ban: '+tempGuild.name+' | GuildID:'+str(removeGuildID))
                                return True
                            else:
                                await message.channel.send(tempGuild.name+' | GuildID:'+str(removeGuildID)+" isn't Globally Banned!")
                                return False
                        elif DatabaseHandler.removeGuildGlobalBan(transactionID, removeGuildID):
                            await message.channel.send('Successfully removed Guild Global Ban: GuildID('+str(removeGuildID)+')')
                            return True
                        else:
                            await message.channel.send('GuildID('+str(removeGuildID)+") isn't Globally Banned!")
                            return False
                    else:
                        await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                    return False

                # else invalid arg was used
                else:
                    await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                    return False

            # not enough args
            else:
                await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                return False

        async def echoCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.CRIT, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            cmd_prefix = '\u200e'  # << BLANK CHARACTER
            if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                cmd_prefix = Utils.getCmdPrefix(transactionID, message.guild.id)

            cmd_args = cmd_str.split(' ')
            if len(cmd_args) >= 2:

                Logger.log(">> Echoing: '"+' '.join(cmd_str.split(' ')[1:])+"'", Importance.CRIT, transactionID)
                await message.channel.send(' '.join(cmd_str.split(' ')[1:]))
                return True

            # not enough args
            else:
                await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                return False

        async def DBEchoCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.CRIT, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            cmd_prefix = '\u200e'  # << BLANK CHARACTER
            if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                cmd_prefix = Utils.getCmdPrefix(transactionID, message.guild.id)

            cmd_args = cmd_str.split(' ')
            if len(cmd_args) >= 2:

                DBCommandStr = ' '.join(cmd_str.split(' ')[1:])
                result = DatabaseHandler.sendQuery(transactionID, DBCommandStr)

                if type(result) == type(''):
                    if 'ERROR' in result:
                        return False
                    else:
                        await message.channel.send(result)
                        return True
                else:
                    await message.channel.send(Utils.list_to_str(result, headers=False))
                    return True

            # not enough args
            else:
                await message.channel.send('Command Usage: **'+cmd_prefix+'**'+self.command_usage)
                return False

        async def restartBotCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.CRIT, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            time_remaining = GameHandler.getLongestGameDuration()
            await message.channel.send('Restart Queued: ETA ~'+Utils.secondsToTime(time_remaining))
            Logger.log('>>> Restart Queued: ETA ~'+Utils.secondsToTime(time_remaining), Importance.CRIT, transactionID)
            await GameHandler.waitForGameEnd()
            await message.channel.send('Restarting...')
            Logger.log('>>> Restarting...', Importance.CRIT, transactionID)
            await BotCommands.client.close()
            return True

        async def serverInviteLinkCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.INFO, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            cmd_prefix = '\u200e'  # << BLANK CHARACTER
            if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                cmd_prefix = Utils.getCmdPrefix(transactionID, message.guild.id)

            cmd_args = cmd_str.split(' ')

            if len(cmd_args) == 2:
                if Utils.isValidInt(cmd_args[1]):
                    guild = BotCommands.client.get_guild(int(cmd_args[1]))
                    if len(guild.channels) > 0:
                        for g_channel in guild.channels:
                            try:
                                invite = await g_channel.create_invite()
                                await message.channel.send('Server\'s invite link: '+invite.url)
                                return True
                            except Exception as e:
                                # 404 happens sometimes if channel previously existed, just keep going if it happens
                                if not '404' in e.args[0]:
                                    await message.channel.send(str(e))
                                    # return False
                        await message.channel.send('Failed to create invite link to server.')
                        return False
                    else:
                        await message.channel.send('No channels in server?')
                        return False
                else:
                    return False
            else:
                await message.channel.send(self.command_str+': '+self.command_description+'\nUsage: **'+cmd_prefix+'**'+self.command_usage)
                return False

        async def reloadPrefsCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.CRIT, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            if PreferenceLoader.loadPrefs():
                Logger.log('> Successfully reloaded preferences', Importance.CRIT, transactionID)
                await message.channel.send('Successfully reloaded preferences')
                return True
            else:
                Logger.log('> Error: Failed to reload preferences', Importance.CRIT, transactionID)
                await message.channel.send('Error: Failed to reload preferences')
                return False

        async def helpCommand(self, transactionID: uuid, message: discord.Message, cmd_str: str):
            Logger.log('>> Called command: '+self.command_str, Importance.INFO, transactionID)
            Logger.log('>> Full command: '+cmd_str, Importance.DBUG, transactionID)

            cmd_prefix = '\u200e'  # << BLANK CHARACTER
            if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                cmd_prefix = Utils.getCmdPrefix(transactionID, message.guild.id)

            try:
                if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                    # try deleting original command call message to reduce spam if not in DMs
                    await message.delete()
            except Exception as e:
                # probably dont have perms, oh well
                pass

            # check if all cmd arguments are present
            cmd_args = cmd_str.split(' ')

            user_is_superadmin = False
            user_is_serveradmin = False

            if message.author.id in Utils.get_superadmins():
                user_is_superadmin = True

            if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
                # check if sender has administrator privilages in server, if so add them to serveradmin table
                if message.author.guild_permissions.administrator:
                    DatabaseHandler.addGuildAdmin(transactionID, message.guild.id, message.author.id)

                # check if sender is serveradmin in current guild
                if message.author.id in Utils.get_serveradmins_for_guild(transactionID, message.guild.id):
                    user_is_serveradmin = True

            # check if sender is a serveradmin in any server with the bot
            elif message.author.id in Utils.get_all_serveradmins(transactionID):
                user_is_serveradmin = True

            # normal help command
            if len(cmd_args) == 1:
                cmdListSuperAdmin = '__SuperAdmin Commands:__\n'
                cmdListServerAdmin = '__Server Admin Commands:__\n'
                cmdListPublic = ''
                cmdListDisplay = ''

                for cmd in BotCommands.commands_list:
                    if cmd.is_superadmin_only:
                        cmdListSuperAdmin += '**'+cmd_prefix+cmd.command_str+'**: '+cmd.command_description+'\n'
                    elif cmd.is_serveradmin_only:
                        cmdListServerAdmin += '**'+cmd_prefix+cmd.command_str+'**: '+cmd.command_description+'\n'
                    else:
                        cmdListPublic += '**'+cmd_prefix+cmd.command_str+'**: '+cmd.command_description+'\n'

                cmdListDisplay += cmdListPublic+'\n'
                if user_is_serveradmin or user_is_superadmin:
                    cmdListDisplay += cmdListServerAdmin+'\n'
                if user_is_superadmin:
                    cmdListDisplay += cmdListSuperAdmin+'\n'

                await Utils.send_user_DM(transactionID, BotCommands.client, message.author.id, '__Available Commands:__\n'+cmdListDisplay)
                return True

            # show subcategory or show cmd usage for given command
            if len(cmd_args) == 2:

                # check if looking for specific command
                if user_is_superadmin:
                    for cmd in BotCommands.commands_list:
                        if cmd.command_str.lower() == cmd_args[1].lower():
                            await Utils.send_user_DM(transactionID, BotCommands.client, message.author.id, cmd.command_str+': '+cmd.command_description+'\nUsage: **'+cmd_prefix+'**'+cmd.command_usage)
                            return True

                elif user_is_serveradmin:
                    for cmd in BotCommands.commands_list:
                        if cmd.command_str.lower() == cmd_args[1].lower():
                            if not cmd.is_superadmin_only:
                                await Utils.send_user_DM(transactionID, BotCommands.client, message.author.id, cmd.command_str+': '+cmd.command_description+'\nUsage: **'+cmd_prefix+'**'+cmd.command_usage)
                                return True
                            else:
                                Logger.log('>> Permissions Error: User('+str(message.author.id)+') attempted to lookup SuperAdmin command', Importance.WARN, transactionID)
                                return False

                else:
                    for cmd in BotCommands.commands_list:
                        if cmd.command_str.lower() == cmd_args[1].lower():
                            if not cmd.is_superadmin_only:
                                if not cmd.is_serveradmin_only:
                                    await Utils.send_user_DM(transactionID, BotCommands.client, message.author.id, cmd.command_str+': '+cmd.command_description+'\nUsage: **'+cmd_prefix+'**'+cmd.command_usage)
                                    return True
                                else:
                                    Logger.log('>> Permissions Error: User('+str(message.author.id)+') attempted to lookup ServerAdmin command', Importance.WARN, transactionID)
                                    return False
                        else:
                            Logger.log('>> Permissions Error: User('+str(message.author.id)+') attempted to lookup SuperAdmin command', Importance.WARN, transactionID)
                            return False

            # wrong number of args, show cmd usage
            else:
                await Utils.send_user_DM(transactionID, BotCommands.client, message.author.id, '**'+cmd_prefix+'**'+self.command_usage)
                return False

        # add all bot commands
        BotCommands.commands_list.clear()

        BotCommands.commands_list.append(Command(
            command_str='InviteLink',
            command_description="Get the bot's invite link via DM",
            command_usage='InviteLink',
            is_PMAllowed=True,
            command_action=inviteCommand))

        BotCommands.commands_list.append(Command(
            command_str='ServerAdmins',
            command_description='See and modify the users registered as bot server admins',
            command_usage='ServerAdmins [show|add|remove] (mention|userID)',
            is_serveradmin_only=True,
            command_action=serverAdminsCommand))

        BotCommands.commands_list.append(Command(
            command_str='ServerSettings',
            command_description="See and modify the bot's behavior on this server",
            command_usage='ServerSettings [show|modify] (key) (value)',
            is_serveradmin_only=True,
            command_action=serverSettingsCommand))

        BotCommands.commands_list.append(Command(
            command_str='GlobalSettings',
            command_description="See and modify the bot's behavior on all servers",
            command_usage='GlobalSettings [show|modify] (key) (value)',
            is_superadmin_only=True,
            is_PMAllowed=True,
            command_action=globalSettingsCommand))

        BotCommands.commands_list.append(Command(
            command_str='UserGlobalBans',
            command_description="See and modify the bot's global user bans",
            command_usage='UserGlobalBans [show|add|remove] (mention|userID)',
            is_superadmin_only=True,
            is_PMAllowed=True,
            command_action=userGlobalBansCommand))

        BotCommands.commands_list.append(Command(
            command_str='GuildGlobalBans',
            command_description="See and modify the bot's global guild bans",
            command_usage='GuildGlobalBans [show|add|remove] (guildID)',
            is_superadmin_only=True,
            is_PMAllowed=True,
            command_action=guildGlobalBansCommand))

        BotCommands.commands_list.append(Command(
            command_str='Echo',
            command_description='Simon says repeat after me',
            command_usage='Echo [message]',
            is_superadmin_only=True,
            is_PMAllowed=True,
            command_action=echoCommand))

        BotCommands.commands_list.append(Command(
            command_str='DBEcho',
            command_description='Query the database directly. Danger! Here be dragons',
            command_usage='DBEcho [DB query]',
            is_superadmin_only=True,
            is_PMAllowed=True,
            command_action=DBEchoCommand))

        BotCommands.commands_list.append(Command(
            command_str='RestartBot',
            command_description='Fully shutdown bot then allow daemon to restart it',
            command_usage='RestartBot',
            is_superadmin_only=True,
            is_PMAllowed=True,
            command_action=restartBotCommand))

        BotCommands.commands_list.append(Command(
            command_str='ServerInviteLink',
            command_description='Get an invite link a specific server the bot is on',
            command_usage='ServerInviteLink [guild ID]',
            is_superadmin_only=True,
            is_PMAllowed=True,
            command_action=serverInviteLinkCommand))

        BotCommands.commands_list.append(Command(
            command_str='ReloadPrefs',
            command_description='Reload preferences without restarting',
            command_usage='ReloadPrefs',
            is_superadmin_only=True,
            is_PMAllowed=True,
            command_action=reloadPrefsCommand))

        BotCommands.commands_list.append(Command(
            command_str='Help',
            command_description='List of all bot commands via DM',
            command_usage='Help (command)',
            command_aliases=['?'],
            is_PMAllowed=True,
            command_action=helpCommand))

        return BotCommands.commands_list
