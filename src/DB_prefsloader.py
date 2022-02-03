# Generic-DiscordBot
# author: github/adibarra

# imports
import os
import json


class PreferenceLoader:
    """ Class to load preferences on startup """

    db_address = 'localhost'
    db_port = '3306'
    db_user = 'genericbot'
    db_pass = 'password'
    db_name = 'GenericBotDB'

    verbositySetting = 'WARN'

    superadmin_ids = [000000000000000000, 000000000000000000]
    emergency_alert_user_id = 000000000000000000

    client_token = ''
    tester_client_token = ''

    logger_enabled = True
    preferences_location = '../res/'
    preference_file = 'prefs.json'

    @staticmethod
    def generatePrefsFile():
        generated = False
        filecontents = {
            'database_host': 'localhost',
            'database_port': 3306,
            'database_username': 'genericbot',
            'database_password': 'password',
            'database_name': 'GenericBotDB',
            'verbosity_options': ['DBUG', 'INFO', 'WARN', 'CRIT'],
            'verbosity_choice': 'WARN',
            'superadmin_ids': [000000000000000000, 000000000000000000],
            'emergency_alert_user_id': 000000000000000000,
            'bot_token': '',
            'tester_bot_token': '',
            'logger_enabled': True
        }

        try:
            # check if path to preferences file exists else create
            if not os.path.exists(os.path.dirname(os.path.realpath(__file__))+'/'+PreferenceLoader.preferences_location):
                original_umask = os.umask(0)
                os.makedirs(os.path.dirname(os.path.realpath(__file__))+'/'+PreferenceLoader.preferences_location)
                os.umask(original_umask)
        except Exception as e:
            print('There was an error while trying to create the '+PreferenceLoader.preferences_location+' directory:')
            print(e)

        # check if preferences file exists else create
        fileName = os.path.dirname(os.path.realpath(__file__))+'/'+PreferenceLoader.preferences_location+PreferenceLoader.preference_file
        if not os.path.isfile(fileName):
            try:
                # create preferences file with default settings
                with open(fileName, 'w') as (json_file):
                    json.dump(filecontents, json_file, indent=4)
                    generated = True
            except Exception as e:
                print('There was an error while trying to create the '+PreferenceLoader.preference_file+' file:')
                print(e)

        return generated

    @staticmethod
    def loadPrefs():
        if PreferenceLoader.generatePrefsFile():
            print('Generated preferences file ('+PreferenceLoader.preferences_location+PreferenceLoader.preference_file+')')
            print('Fill it out then restart the bot when you are ready.')
            exit(0)

        try:
            filePath = os.path.dirname(os.path.realpath(__file__))+'/'+PreferenceLoader.preferences_location+PreferenceLoader.preference_file
            with open(filePath) as json_file:
                prefs = json.load(json_file)

                PreferenceLoader.db_address = prefs['database_host']
                PreferenceLoader.db_port = prefs['database_port']
                PreferenceLoader.db_user = prefs['database_username']
                PreferenceLoader.db_pass = prefs['database_password']
                PreferenceLoader.db_name = prefs['database_name']

                PreferenceLoader.verbositySetting = prefs['verbosity_choice']

                PreferenceLoader.superadmin_ids = prefs['superadmin_ids']
                PreferenceLoader.emergency_alert_user_id = prefs['emergency_alert_user_id']

                PreferenceLoader.client_token = prefs['bot_token']
                PreferenceLoader.tester_client_token = prefs['tester_bot_token']

                PreferenceLoader.logger_enabled = prefs['logger_enabled']
                return True

        except Exception as e:
            print('RUNTIME ERROR: Failed to open Prefs file.')
            print(e)
            return False
