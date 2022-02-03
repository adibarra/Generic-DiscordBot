# Generic-DiscordBot
# author: github/adibarra

# imports
import time
import discord
from uuid import uuid4
from DB_utils import *
from DB_logger import *
from DB_commands import *
from DB_database import *
from DB_cmdhandler import *

# start main bot
Logger.log('-----------------------', importance=None)
if PreferenceLoader.loadPrefs():
    Logger.log('Loaded Preferences.', importance=None)
else:
    Logger.log('Failed to load Preferences. (See console for details).', importance=None)

# setup
clientIntents = discord.Intents.default()
clientIntents.members = True
client = discord.Client(intents=clientIntents)
commandHandler = CommandHandler(client)


@client.event
async def on_ready():
    Logger.log('Logged in as {0.user}'.format(client)+' @ '+time.strftime("%Y-%m-%d %H:%M:%S")+'\n'+'Registering commands...', importance=None)
    commandHandler.registerCommands()
    if await Utils.checkDBConnection(client, importance=None):
        Logger.log('Ready to go!', importance=None)
    Logger.log('-----------------------\n', importance=None)


@client.event
async def on_disconnect():
    Logger.log('!!! Disconnected from discord API !!!\n',
               Importance.WARN, transactionID=uuid4())


@client.event
async def on_resumed():
    Logger.log('!!! Reconnected to discord API !!!\n',
               Importance.WARN, transactionID=uuid4())


@client.event
async def on_guild_join(guild):
    # generate tables for new guild
    transactionID = uuid4()
    Logger.log('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', transactionID)
    Logger.log('>>> Joining a new Guild('+str(guild.id)+')!', transactionID)
    Logger.log('>>> Generating new guild tables, Setting Guild owner User('+str(guild.owner.id)+') to serverAdmin by default', transactionID)
    DatabaseHandler.createGuildAdminsTable(transactionID, guild.id)
    DatabaseHandler.addGuildAdmin(transactionID, guild.id, guild.owner.id)
    DatabaseHandler.createGuildSettingsTable(transactionID, guild.id)
    await Utils.send_user_DM(transactionID, client, guild.owner.id, "**Thanks for adding me to your server!**\n"
         + "Try writing `help` for a list of commands.\nThe default command prefix for your server is `$`.")
    Logger.log('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>',
               transactionID, final=True)


@client.event
async def on_guild_remove(guild):
    # delete tables for guild
    transactionID = uuid4()
    Logger.log('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<', transactionID)
    Logger.log('>>> Removed from a Guild('+str(guild.id)+')!', transactionID)
    Logger.log('>>> Deleting all guild tables...', transactionID)
    DatabaseHandler.deleteGuildAdminsTable(transactionID, guild.id)
    DatabaseHandler.deleteGuildSettingsTable(transactionID, guild.id)
    Logger.log('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<',
               transactionID, final=True)


@client.event
async def on_message(message):
    # ignore own messages
    if message.author == client.user:
        return

    # assign each transaction a unique ID
    transactionID = uuid4()

    # determine how to handle message
    bot_cmd_prefix = '\u200e'  # << BLANK CHARACTER
    # initialize false, in case of PM, check for actual status if from a server
    isGuildBanned = False
    isUserBanned = Utils.isUserBanned(transactionID, message.author.id)
    isUserSuperAdmin = message.author.id in Utils.get_superadmins()

    # check if user is globally banned, should not be possible to ban superadmin but just in case.
    if isUserBanned and not isUserSuperAdmin:
        Logger.log('> Ignoring User('+str(message.author.id)+'): Globally Banned', Importance.DBUG, transactionID, final=True)
        return

    # get cmd prefix if public server
    if str(type(message.channel)) == "<class 'discord.channel.TextChannel'>":
        bot_cmd_prefix = Utils.getCmdPrefix(transactionID, message.guild.id)
        isGuildBanned = Utils.isGuildBanned(transactionID, message.guild.id)

    # check if server is globally banned, override if user is superadmin
    if not isGuildBanned or isUserSuperAdmin:

        # if message from PM dont check for prefix
        if bot_cmd_prefix == '\u200e':
            pass
        # if message from server check for prefix
        elif message.content.startswith(bot_cmd_prefix):
            pass
        # wrong prefix, ignore message
        else:
            Logger.log("> Message prefix does not match server prefix '"+bot_cmd_prefix+"', not a command", Importance.DBUG, transactionID, final=True)
            return

        # allow command if user is a superadmin even if used in globally banned guild
        if isGuildBanned and isUserSuperAdmin:
            Logger.log('> SuperAdmin Permissions Override: User('+str(message.author.id)+'). Ignoring Guild Ban.', Importance.DBUG, transactionID, final=True)

        # continue if guild is not globally banned, no need to check for superadmin
        elif not isGuildBanned:
            pass

        # if guild is globally banned and user is not a superadmin stop here
        else:
            Logger.log('> Guild('+str(message.author.id)+') Globally Banned: Ignoring command.', Importance.DBUG, transactionID, final=True)
            return

        # run command
        result = await commandHandler.run_command(transactionID, bot_cmd_prefix, message)
        Logger.log('> Successfully ran command? '+str(result), Importance.DBUG, transactionID, final=True)
        return


client.run(PreferenceLoader.client_token)
Logger.log('-----------------------\nGoodbye...\n-----------------------\n\n', importance=None)
