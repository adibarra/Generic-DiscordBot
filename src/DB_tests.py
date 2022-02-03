# Generic-DiscordBot
# author: github/adibarra

# imports
import sys
import discord
import asyncio
import unittest
from DB_utils import *
from DB_games import *
from DB_logger import *
from DB_commands import *
from DB_database import *
from DB_cmdhandler import *
from DB_prefsloader import *

allTestsPassed = False


class TestMethods(unittest.TestCase):
    """
    Make sure the test bot and the main bot are BOTH running from the same machine
    or else all tests will fail due to running off of two different databases.
    I know from experience...
    """

    testUUID = None

    # helper methods
    def setUp(self):
        # generate junk data and disable logging
        Logger.enabled = False
        self.testUUID = uuid.uuid4()

    def tearDown(self):
        global allTestsPassed
        allTestsPassed = (sys.exc_info() == (None, None, None))

    # begin tests

    def test_isValidInt(self):
        # test is valid int
        self.assertTrue(Utils.isValidInt('123456789123456789'))
        self.assertTrue(Utils.isValidInt('123456789'))
        self.assertTrue(Utils.isValidInt('0'))
        self.assertFalse(Utils.isValidInt('asdfghjklzxcvbnm,.'))
        self.assertFalse(Utils.isValidInt('a'))
        self.assertFalse(Utils.isValidInt('1.0'))

    def test_isValidFloat(self):
        # test is valid float
        self.assertTrue(Utils.isValidFloat('1'))
        self.assertTrue(Utils.isValidFloat('1.0'))
        self.assertTrue(Utils.isValidFloat('1.00000000'))
        self.assertTrue(Utils.isValidFloat('0000000001.0'))
        self.assertFalse(Utils.isValidFloat('asdfghjklzxcvbnm,.'))
        self.assertFalse(Utils.isValidFloat('a'))

    def test_floatToSats(self):
        # test float to sats
        self.assertEqual(Utils.floatToSats(0.00000001), 1)
        self.assertEqual(Utils.floatToSats(1.0), 100000000)
        self.assertEqual(Utils.floatToSats(0), 0)

    def test_satsToFloat(self):
        # test sats to float
        self.assertEqual(Utils.satsToFloat(1), '0.00000001')
        self.assertEqual(Utils.satsToFloat(100000000), '1')
        self.assertEqual(Utils.satsToFloat(0), '0')

    def test_sanitize_for_DB(self):
        # test sanitation
        self.assertEqual(Utils.sanitize_for_DB(''), '')
        self.assertEqual(Utils.sanitize_for_DB('test'), 'test')
        self.assertEqual(Utils.sanitize_for_DB('SelECT'), '')
        self.assertEqual(Utils.sanitize_for_DB("'"), '')
        self.assertEqual(Utils.sanitize_for_DB('"'), '')
        self.assertEqual(Utils.sanitize_for_DB('*'), '')
        self.assertEqual(Utils.sanitize_for_DB('oregano'), 'egano')
        self.assertEqual(Utils.sanitize_for_DB('created by me'), 'd  me')

    def test_secondsToTime(self):
        # test seconds
        self.assertEqual(Utils.secondsToTime(0), '0 seconds')
        self.assertEqual(Utils.secondsToTime(1), '1 second')
        self.assertEqual(Utils.secondsToTime(2), '2 seconds')
        # test minutes
        self.assertEqual(Utils.secondsToTime(60), '1 minute')
        self.assertEqual(Utils.secondsToTime(60*2), '2 minutes')
        # test hours
        self.assertEqual(Utils.secondsToTime(60*60), '1 hour')
        self.assertEqual(Utils.secondsToTime(60*60*2), '2 hours')
        # test days
        self.assertEqual(Utils.secondsToTime(60*60*24), '1 day')
        self.assertEqual(Utils.secondsToTime(60*60*24*2), '2 days')
        # test minutes mixed
        self.assertEqual(Utils.secondsToTime(60+1), '1 minute 1 second')
        self.assertEqual(Utils.secondsToTime(60+2), '1 minute 2 seconds')
        self.assertEqual(Utils.secondsToTime(60*2+1), '2 minutes 1 second')
        self.assertEqual(Utils.secondsToTime(60*2+2), '2 minutes 2 seconds')
        # test hours mixed
        self.assertEqual(Utils.secondsToTime(60*60+60), '1 hour 1 minute')
        self.assertEqual(Utils.secondsToTime(60*60+60*2), '1 hour 2 minutes')
        self.assertEqual(Utils.secondsToTime(60*60*2+60), '2 hours 1 minute')
        self.assertEqual(Utils.secondsToTime(60*60*2+60*2), '2 hours 2 minutes')
        # test days mixed
        self.assertEqual(Utils.secondsToTime(60*60*24+60*60), '1 day 1 hour')
        self.assertEqual(Utils.secondsToTime(60*60*24+60*60*2), '1 day 2 hours')
        self.assertEqual(Utils.secondsToTime(60*60*24*2+60*60), '2 days 1 hour')
        self.assertEqual(Utils.secondsToTime(60*60*24*2+60*60*2), '2 days 2 hours')

    def test_chunk_list(self):
        # test chunk list
        self.assertEqual(Utils.chunk_list([1, 2, 3, 4, 5, 6], 2), [[1, 2], [3, 4], [5, 6]])
        self.assertEqual(Utils.chunk_list([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])
        self.assertEqual(Utils.chunk_list([1, 2, 3, 4, 5], 3), [[1, 2, 3], [4, 5]])
        self.assertEqual(Utils.chunk_list([1, 2, 3, 4, 5], 1), [[1], [2], [3], [4], [5]])

    def test_GuildSettingsFunctions(self):
        # test database functions for guildsettings tables
        DatabaseHandler.createGuildSettingsTable(self.testUUID, 0)
        self.assertEqual(len(DatabaseHandler.getGuildSettingsTable(self.testUUID, 0)), 1)
        self.assertNotEqual(len(DatabaseHandler.getGuildSettingsTableContents(self.testUUID, 0)), 0)
        self.assertEqual(DatabaseHandler.getCMDPrefix(self.testUUID, 0), '$')
        DatabaseHandler.modifyGuildSettingsTable(self.testUUID, 0, 'prefix', '!')
        self.assertEqual(DatabaseHandler.getCMDPrefix(self.testUUID, 0), '!')
        DatabaseHandler.modifyGuildSettingsTable(self.testUUID, 0, 'prefix', '$')
        self.assertEqual(DatabaseHandler.getCMDPrefix(self.testUUID, 0), '$')
        DatabaseHandler.deleteGuildSettingsTable(self.testUUID, 0)
        self.assertEqual(len(DatabaseHandler.getGuildSettingsTable(self.testUUID, 0)), 0)

    def test_GuildAdminsFunctions(self):
        # test database functions for guildadmins tables
        DatabaseHandler.createGuildAdminsTable(self.testUUID, 0)
        self.assertEqual(len(DatabaseHandler.getGuildAdminsTable(self.testUUID, 0)), 1)
        self.assertEqual(len(DatabaseHandler.getGuildAdminsTableContents(self.testUUID, 0)), 0)
        self.assertTrue(DatabaseHandler.addGuildAdmin(self.testUUID, 0, 0))
        self.assertEqual(len(DatabaseHandler.getGuildAdminsTableContents(self.testUUID, 0)), 1)
        self.assertFalse(DatabaseHandler.removeGuildAdmin(self.testUUID, 0, 1))
        self.assertEqual(len(DatabaseHandler.getGuildAdminsTableContents(self.testUUID, 0)), 1)
        self.assertTrue(DatabaseHandler.removeGuildAdmin(self.testUUID, 0, 0))
        self.assertEqual(len(DatabaseHandler.getGuildAdminsTableContents(self.testUUID, 0)), 0)
        self.assertFalse(DatabaseHandler.removeGuildAdmin(self.testUUID, 0, 0))
        self.assertEqual(len(DatabaseHandler.getGuildAdminsTableContents(self.testUUID, 0)), 0)
        DatabaseHandler.deleteGuildAdminsTable(self.testUUID, 0)
        self.assertEqual(len(DatabaseHandler.getGuildAdminsTable(self.testUUID, 0)), 0)

    def test_GlobalBanFunctions(self):
        # test database functions for globalbans table
        DatabaseHandler.getGlobalBansTable(self.testUUID)
        global_bans_start = len(DatabaseHandler.getGlobalBansTableContents(self.testUUID))
        self.assertEqual(len(DatabaseHandler.getGlobalBansTable(self.testUUID)), 1)
        self.assertFalse(DatabaseHandler.isIDGlobalBanned(self.testUUID, 0))
        self.assertFalse(DatabaseHandler.isIDGlobalBanned(self.testUUID, 1))
        self.assertTrue(DatabaseHandler.addGlobalBan(self.testUUID, 0))
        self.assertTrue(DatabaseHandler.isIDGlobalBanned(self.testUUID, 0))
        self.assertEqual(len(DatabaseHandler.getGlobalBansTableContents(self.testUUID)), global_bans_start+1)
        self.assertFalse(DatabaseHandler.removeGlobalBan(self.testUUID, 1))
        self.assertEqual(len(DatabaseHandler.getGlobalBansTableContents(self.testUUID)), global_bans_start+1)
        self.assertTrue(DatabaseHandler.removeGlobalBan(self.testUUID, 0))
        self.assertFalse(DatabaseHandler.isIDGlobalBanned(self.testUUID, 0))
        self.assertEqual(len(DatabaseHandler.getGlobalBansTableContents(self.testUUID)), global_bans_start+0)
        self.assertFalse(DatabaseHandler.removeGlobalBan(self.testUUID, 0))
        self.assertEqual(len(DatabaseHandler.getGlobalBansTableContents(self.testUUID)), global_bans_start+0)


# start test bot
Logger.log.enabled = False
testUUID = uuid.uuid4()
testing_channel = None
bot_id = None
PreferenceLoader.loadPrefs()
client_token = PreferenceLoader.tester_client_token
clientIntents = discord.Intents.default()
clientIntents.members = True
client = discord.Client(intents=clientIntents)


class Test:
    testMethod = None
    response = None

    def __init__(self, testMethod):
        self.testMethod = testMethod

    async def runTest(self, testing_channel: discord.abc.Messageable):
        return await self.testMethod(self, testing_channel)

    async def blockUntilResponse(self):
        # block until response with 10s timeout
        counter = 0
        while self.response == None and counter < 10000:
            await asyncio.sleep(0.100)
            counter += 100
        response_copy = self.response
        self.response = None
        return response_copy


class TestHandler:
    tests = []
    currentTest = None

    @staticmethod
    async def registerTests():
        # add tests for bot commands here

        async def test_exampleCommand(test: Test, testing_channel: discord.abc.Messageable):
            print("Test not implemented")
            return True

        TestHandler.tests.append(Test(test_exampleCommand))

    @staticmethod
    async def runTests(testing_channel: discord.abc.Messageable):
        passed = 0
        for test in TestHandler.tests:
            TestHandler.currentTest = test
            if await test.runTest(testing_channel):
                passed += 1
            else:
                print('Failed on test: '+test.testMethod.__name__)

        print('Command test results: Passed '+str(passed)+'/'+str(len(TestHandler.tests)))
        if passed == len(TestHandler.tests):
            return True
        return False


@client.event
async def on_ready():
    # set testing channel
    testing_channel = None
    for channel in client.guilds[0].channels:
        if channel.name == 'automated-testing':
            testing_channel = channel
    if testing_channel == None:
        print('testing_channel is None!')
        client.logout()
    global bot_id
    bot_id = client.user.id

    # run tests
    await testing_channel.send('**Begin automated tests**')
    await testing_channel.send('Running unit tests...')
    unittest.main(verbosity=1, exit=False)

    await testing_channel.send('Running command tests...')
    await TestHandler.registerTests()

    if allTestsPassed:
        await testing_channel.send('All unit tests passed')
    else:
        await testing_channel.send('Some unit tests failed')

    if await TestHandler.runTests(testing_channel):
        await testing_channel.send('All command tests passed\n'+'‎')
    else:
        await testing_channel.send('Some command tests failed\n'+'‎')
    await client.logout()


@client.event
async def on_message(message):
    # ignore own messages
    if message.author == client.user:
        return
    TestHandler.currentTest.response = message

client.run(client_token)
