# Generic-DiscordBot
# author: github/adibarra

# imports
import time
import random
import discord
import asyncio
import asgiref.sync
from uuid import uuid4
from threading import Thread
from DB_utils import Utils
from DB_logger import Logger, Importance


class GameThread(Thread):
    """ Class to house all of the games"""

    client = None
    game_id = None
    game_message = None
    game_endTime = None
    game_duration = None
    game_name_str = None
    command_message = None
    transactionID = None
    fee_percent = None

    @staticmethod
    @asgiref.sync.async_to_sync
    async def addReactionToMsg(messageToReact: discord.Message, reactionToReact: str):
        await messageToReact.add_reaction(reactionToReact)

    @staticmethod
    @asgiref.sync.async_to_sync
    async def getUsersWhoReacted(messageToCheck: discord.Message, reactionToCheckForStr: str):
        message_cache = await messageToCheck.channel.fetch_message(messageToCheck.id)
        users_reacted = []
        for reaction in message_cache.reactions:
            if str(reaction.emoji) == reactionToCheckForStr:
                async for user in reaction.users():
                    users_reacted.append(user)

        return users_reacted

    @staticmethod
    @asgiref.sync.async_to_sync
    async def send_message_sync(channel: discord.abc.Messageable, message: str):
        return await channel.send(message)

    @staticmethod
    @asgiref.sync.async_to_sync
    async def send_embed_sync(channel: discord.abc.Messageable, embed: discord.Embed):
        return await channel.send(embed=embed)

    @staticmethod
    @asgiref.sync.async_to_sync
    async def edit_embed_sync(message: discord.Message, embed: discord.Embed):
        return await message.edit(embed=embed)

    def getTimeUntilGameOver(self):
        return int(self.game_endTime - time.time())

    def __init__(self, disClient: discord.Client, gameMessage: discord.Message, gameDuration: int, fee_percent: int):
        Thread.__init__(self)
        self.fee_percent = fee_percent
        self.transactionID = uuid4()
        self.client = disClient
        self.game_message = gameMessage
        self.game_endTime = time.time()+gameDuration
        self.game_name_str = 'GameThreadGame'

    def run(self):
        if GameHandler.getCanStartGames():
            GameHandler.ongoingGames.append(self)
            try:
                Logger.log('>> DefaultGame Started', Importance.INFO, self.transactionID)
                Utils.send_message_sync(self.game_message.channel, self.game_name_str+': starting game')
                time.sleep(5)
                while time.time() < self.game_endTime:
                    Utils.send_message_sync(self.game_message.channel, self.game_name_str+'Time remaining: '+str(self.game_endTime - time.time()))
                    time.sleep(5)

                self.cleanup()
            except Exception as e:
                try:
                    Logger.log(('RUNTIME ERROR: '+str(e.args)), Importance.CRIT, (self.transactionID), final=True)
                    self.cleanup()
                finally:
                    e = None
                    del e

            else:
                return
        Utils.send_message_sync(self.game_message.channel, 'Pending bot restart, please try again in a few minutes')
        return None

    def cleanup(self):
        GameHandler.ongoingGames.remove(self)
        print(self.game_name_str+': game ended')
        Utils.send_message_sync(self.game_message.channel, self.game_name_str+': game ended')


'''
# EXAMPLE LOTTERY GAME
class LottoGame(GameThread):

    lotto_ticket_price = 0.00000000
    lotto_ticket_currency = 'TEST'
    
    # game runs under different transactionID
    def __init__(self, disClient: discord.Client, command_message: discord.Message, gameDuration: int, ticketPrice: float, ticketCurrency: str, fee_percent: int):
        Thread.__init__(self)
        self.transactionID = uuid4()
        self.client = disClient
        self.game_name_str = 'Lottery'
        self.command_message = command_message
        self.game_duration = gameDuration
        self.game_endTime = time.time()+gameDuration
        self.lotto_ticket_price = ticketPrice
        self.lotto_ticket_currency = ticketCurrency
        self.fee_percent = fee_percent

    # generate embed for displaying lotto progress
    def createLottoEmbed(self, time_left: int, num_entries: int):
        embed = discord.Embed(
            title=self.lotto_ticket_currency+' '+self.game_name_str,
            description='The cost to enter this lottery is '+'{:.5f}'.format(self.lotto_ticket_price)+' '+self.lotto_ticket_currency,
            color=0xffa500)
        embed.add_field(
            name='React with 🎟️ to buy a ticket\nMake sure your balance is high enough!',
            value='‎', # << BLANK CHARACTER
            inline=False)
        embed.add_field(
            name='Pot: ',
            value='{:.5f}'.format(self.lotto_ticket_price*num_entries)+' '+self.lotto_ticket_currency,
            inline=True)
        embed.add_field(
            name='# of Entries: ',
            value=str(int(num_entries)),
            inline=True)
        embed.set_footer(text='Time remaining to enter: '+Utils.secondsToTime(time_left))
        return embed

    # generate embed for displaying lotto winner
    def createLottoWinnerEmbed(self, winner: str, num_entries: int):
        embed = discord.Embed(
            title=self.lotto_ticket_currency+' '+self.game_name_str,
            color=0x00ff00)
        embed.add_field(
            name='And the winner is: ',
            value=winner,
            inline=False)
        embed.add_field(
            name='Pot: ',
            value='{:.5f}'.format(self.lotto_ticket_price*num_entries)+' '+self.lotto_ticket_currency,
            inline=True)
        embed.add_field(
            name='# of Entries: ',
            value=str(int(num_entries)),
            inline=True)
        embed.set_footer(text='Finished on '+time.strftime("%Y-%m-%d::%H:%M:%S"))
        return embed
    
    # generate embed for displaying lotto error
    def createLottoErrorEmbed(self):
        embed = discord.Embed(
            title=self.lotto_ticket_currency+' '+self.game_name_str,
            description='There were not enough entries into the lottery.',
            color=0xff0000)
        embed.set_footer(
            text='Finished on '+time.strftime("%Y-%m-%d::%H:%M:%S"))
        return embed
    
    # generate embed for displaying low balance error
    def createLottoLowBalanceEmbed(self, user_balance: str):
        embed = discord.Embed(
            title=self.lotto_ticket_currency+' '+self.game_name_str,
            description='Low Balance! Unable to purchase Lottery ticket.',
            color=0xff0000)
        embed.add_field(
            name='Current Balance: '+user_balance+' '+self.lotto_ticket_currency,
            value='Needed for ticket: '+str(self.lotto_ticket_price)+' '+self.lotto_ticket_currency,
            inline=True)
        return embed
    
    # generate embed for displaying refund info
    def createLottoRefundEmbed(self):
        embed = discord.Embed(
            title=self.lotto_ticket_currency+' '+self.game_name_str,
            description='The lotto was unable to continue due to low participation.',
            color=0xff0000)
        embed.add_field(
            name='You have been refunded '+str(self.lotto_ticket_price)+' '+self.lotto_ticket_currency,
            value='‎', # << BLANK CHARACTER
            inline=True)
        return embed
    
    # generate embed for displaying lotto winner DM
    def createLottoWinnerDMEmbed(self, winnings: int):
        embed = discord.Embed(
            title=self.lotto_ticket_currency+' '+self.game_name_str,
            color=0x00ff00)
        embed.add_field(
            name='You won a lottery!',
            value='Winnings: '+str(winnings)+' '+self.lotto_ticket_currency,
            inline=False)
        embed.set_footer(text='Finished on '+time.strftime("%Y-%m-%d::%H:%M:%S"))
        return embed
    
    def run(self):
        # if not awaiting shutdown, then start game+register with GameHandler
        # if game shorter than shutdown timer then allow anyways
        if GameHandler.getCanStartGames() or GameHandler.getLongestGameDuration() > self.game_duration:
            Logger.log('>> Lotto Started. Duration: '+str(Utils.secondsToTime(self.game_duration))+', Amount: '+str(self.lotto_ticket_price)
               +', Coin: '+self.lotto_ticket_currency, self.transactionID)
            GameHandler.registerGame(self)
            try:
                loop_counter = 0
                loop_time_increment = 5
                times_to_loop = self.game_duration / loop_time_increment

                # create and send initial lotto embed
                self.game_message = LottoGame.send_embed_sync(self.command_message.channel, self.createLottoEmbed(time_left=int(times_to_loop*loop_time_increment), num_entries=0))
                LottoGame.addReactionToMsg(self.game_message, '🎟️')

                # make time remaining counter use increments up 5 seconds
                while loop_counter < times_to_loop:
                    time.sleep(loop_time_increment)
                    loop_counter += 1

                    # dont update on last loop, wait for lottowinnerembed instead
                    if loop_counter < times_to_loop:
                        entries = LottoGame.getUsersWhoReacted(self.game_message, '🎟️')
                        LottoGame.edit_embed_sync(self.game_message, self.createLottoEmbed(time_left=int((times_to_loop-loop_counter)*loop_time_increment), num_entries=len(entries)-1))

                # done accepting tickets+remove self from entries list
                entries = LottoGame.getUsersWhoReacted(self.game_message, '🎟️')
                entries.remove(self.client.user)

                # only allow users with balance >= ticket cost then subtract amount from their balances
                final_entries = []
                rejected_entries = []
                for entry in entries:
                    if not DatabaseHandler.isIDGlobalBanned(self.transactionID, entry.id):
                        DatabaseHandler.getUserBalance(self.transactionID, entry.id, self.lotto_ticket_currency)
                        if DatabaseHandler.adjustUserBalance(self.transactionID, entry.id, self.lotto_ticket_currency, -Utils.floatToSats(self.lotto_ticket_price)) >= 0:
                            # user meets all requirements add to final entries list
                            final_entries.append(entry)
                        else:
                            # notify user they did not have a large enough balance to purchase a ticket in the lotto
                            rejected_entries.append(entry)
                    else:
                        # user was global banned ignoring
                        pass

                # determine winner of lottery
                if len(final_entries) > 1:
                    # nofity rejected entries of low balance
                    for entry in rejected_entries:
                        user_balance = DatabaseHandler.getUserBalance(self.transactionID, entry.id, self.lotto_ticket_currency)
                        user_balance = Utils.satsToFloat(user_balance)
                        Utils.send_user_embed_DM_sync(self.transactionID, self.client, entry.id, self.createLottoLowBalanceEmbed(user_balance))

                    # calculate results
                    pot_worth = self.lotto_ticket_price*len(final_entries) * (float(100 - self.fee_percent) / 100.0)
                    fee_worth = self.lotto_ticket_price*len(final_entries) - pot_worth
                    winner = random.choice(final_entries)

                    # nofity of results
                    LottoGame.edit_embed_sync(self.game_message, self.createLottoWinnerEmbed(winner.mention, len(final_entries)))
                    Utils.send_user_embed_DM_sync(self.transactionID, self.client, winner.id, self.createLottoWinnerDMEmbed(pot_worth))

                    # adjust balances
                    DatabaseHandler.adjustUserBalance(self.transactionID, winner.id, self.lotto_ticket_currency, Utils.floatToSats(pot_worth))
                    DatabaseHandler.adjustUserBalance(self.transactionID, self.client.user.id, self.lotto_ticket_currency, Utils.floatToSats(fee_worth))
                    Logger.log('>> Lotto finished Successfully. Winner:'+str(winner.id)+', Amount: '+str(self.lotto_ticket_price)
                       +', Coin: '+self.lotto_ticket_currency, self.transactionID, final=True)
                else:
                    # show cancellation embed
                    LottoGame.edit_embed_sync(self.game_message, self.createLottoErrorEmbed())
                    
                    # refund ticket price if anyone entered
                    for entry in final_entries:
                        DatabaseHandler.adjustUserBalance(self.transactionID, entry.id, self.lotto_ticket_currency, Utils.floatToSats(self.lotto_ticket_price))
                        # send embed after refund, just in case
                        Utils.send_user_embed_DM_sync(self.transactionID, self.client, entry.id, self.createLottoRefundEmbed())

                    # nofity rejected entries of low balance
                    for entry in rejected_entries:
                        user_balance = DatabaseHandler.getUserBalance(self.transactionID, entry.id, self.lotto_ticket_currency)
                        user_balance = Utils.satsToFloat(user_balance)
                        Utils.send_user_embed_DM_sync(self.transactionID, self.client, entry.id, self.createLottoLowBalanceEmbed(user_balance))

                    Logger.log('>> Lotto Cancelled (Not enough entries). Amount: '+str(self.lotto_ticket_price)+', Coin: '+self.lotto_ticket_currency, self.transactionID, final=True)

                self.cleanup()
            except Exception as e:
                Logger.log('RUNTIME ERROR: '+str(e.args), self.transactionID, final=True)
                self.cleanup()
            return
        else:
            time_until_shutdown = Utils.secondsToTime(GameHandler.getLongestGameDuration())
            LottoGame.send_message_sync(self.command_message.channel, 'Bot restart in about '+time_until_shutdown+', please try again later or set a shorter time limit.')
            return

    def cleanup(self):
        GameHandler.deregisterGame(self)
'''


class GameHandler:
    """ Class to handle managing all ongoing games """

    canStartGames = True
    ongoingGames = []

    @staticmethod
    def registerGame(game):
        if game not in GameHandler.ongoingGames:
            GameHandler.ongoingGames.append(game)

    @staticmethod
    def deregisterGame(game):
        if game in GameHandler.ongoingGames:
            GameHandler.ongoingGames.remove(game)

    @staticmethod
    def getCanStartGames():
        return GameHandler.canStartGames

    @staticmethod
    async def waitForGameEnd():
        GameHandler.canStartGames = False
        while len(GameHandler.ongoingGames) > 0:
            await asyncio.sleep(10)

    @staticmethod
    def getLongestGameDuration():
        longest_duration = 0
        for game in GameHandler.ongoingGames:
            if game.getTimeUntilGameOver() > longest_duration:
                longest_duration = game.getTimeUntilGameOver()
        return longest_duration
