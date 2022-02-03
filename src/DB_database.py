# Generic-DiscordBot
# author: github/adibarra

# imports
import uuid
import pymysql
from DB_logger import Logger, Importance
from DB_prefsloader import PreferenceLoader


class DatabaseHandler:
    """ This is a class to handle database queries """

    # functions to make retreiving data from the database easier
    @staticmethod
    def checkDBConnection():
        """Checks connection to database.

        Returns:
            bool: True if connection successful, else False
        """

        try:
            # Open database connection || unix_socket=PreferenceLoader.db_unix_socket
            db = pymysql.connect(host=PreferenceLoader.db_address, user=PreferenceLoader.db_user,
                                 password=PreferenceLoader.db_pass, database=PreferenceLoader.db_name, autocommit=True)

            # prepare a cursor object using cursor() method
            cursor = db.cursor()

            # execute SQL query using execute() method.
            rows_affected = cursor.execute('show tables;')

            # Fetch all results
            results = cursor.fetchall()

            # disconnect from server
            db.close()
        except pymysql.Error as e:
            return False
        return True

    @staticmethod
    def checkDBConnectionError():
        """Checks database connection error.

        Returns:
            str: String representing error, None otherwise
        """

        try:
            # Open database connection || unix_socket=PreferenceLoader.db_unix_socket,
            db = pymysql.connect(host=PreferenceLoader.db_address, user=PreferenceLoader.db_user,
                                 password=PreferenceLoader.db_pass, database=PreferenceLoader.db_name, autocommit=True)

            # prepare a cursor object using cursor() method
            cursor = db.cursor()

            # execute SQL query using execute() method.
            rows_affected = cursor.execute('show tables;')

            # Fetch all results
            results = cursor.fetchall()

            # disconnect from server
            db.close()
        except pymysql.Error as e:
            return str(e.args[0])+': '+str(e.args[1])
        return 'No Error'

    @staticmethod
    def doesTableExist(transactionID: uuid, tableName: str):
        """Checks for table with given name.

        Args:
            transactionID (uuid): The transactionID for current transaction
            tableName (str): Name of the table to check for

        Returns:
            bool: returns true if table with given name does exist
        """

        results = DatabaseHandler.sendQuery(transactionID, 'SHOW tables like "'+tableName+'";')

        if len(results) == 0:
            return False
        return True

    @staticmethod
    def getCMDPrefix(transactionID: uuid, guildID: int):
        """Get the command prefix for a guild.

        Parameters:
            transactionID (uuid): The transactionID for current transaction
            guildID (int): The ID of guild to check prefix for

        Returns:
            str: Command prefix for the guild
        """

        return DatabaseHandler.sendQuery(transactionID, 'SELECT configValue FROM '+str(guildID)+"GuildSettings WHERE configKey = 'prefix';")[0][0]

    @staticmethod
    def isUserIDGlobalBanned(transactionID: uuid, userID: int):
        """Get whether a user is Globally Banned.

        Parameters:
            transactionID (uuid): The transactionID for current transaction
            userID (int): The ID of user to check for

        Returns:
            bool: True if userID is Globally Banned, else False
        """

        banned_ids = []
        banned_results = DatabaseHandler.getUserGlobalBansTableContents(transactionID)

        # this table is structured differently from the others
        for user in banned_results:
            banned_ids.append(int(user[0]))

        return userID in banned_ids

    @staticmethod
    def isGuildIDGlobalBanned(transactionID: uuid, guildID: int):
        """Get whether a guild is Globally Banned.

        Parameters:
            transactionID (uuid): The transactionID for current transaction
            guildID (int): The ID of user to check for

        Returns:
            bool: True if guildID is Globally Banned, else False
        """

        banned_ids = []
        banned_results = DatabaseHandler.getGuildGlobalBansTableContents(transactionID)

        # this table is structured differently from the others
        for guild in banned_results:
            banned_ids.append(int(guild[0]))

        return guildID in banned_ids

    @staticmethod
    def sendQuery(transactionID: uuid, message: str):
        """Send a querty to the database server.

        Parameters:
            transactionID (uuid): The transactionID for current transaction
            message (str): The command to send to the MySQL database

        Returns:
            tuple: Will return tuple of tuples containing the result if no error was encountered
            str: Will return a string if an error was encountered
        """

        try:
            # Open database connection || unix_socket=PreferenceLoader.db_unix_socket,
            db = pymysql.connect(host=PreferenceLoader.db_address, user=PreferenceLoader.db_user,
                                 password=PreferenceLoader.db_pass, database=PreferenceLoader.db_name, autocommit=True)

            # prepare a cursor object using cursor() method
            cursor = db.cursor()

            # execute SQL query using execute() method.
            Logger.log('>>> Executing DB Query: '+message, Importance.DBUG, transactionID)
            rows_affected = cursor.execute(message)
            # print(message+' || Affected '+str(rows_affected)+' row(s)')

            # Fetch all results
            results = cursor.fetchall()

            # disconnect from server
            db.close()
        except pymysql.Error as e:
            return ':rage: ERROR '+str(e)
        return results

    """ Functions to handle Global User Bans table """
    @staticmethod
    def createUserGlobalBansTable(transactionID: uuid):
        """Creates new table for bot's user global bans called 'UserGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            tuple: Will return tuple of tuples containing the new table
        """

        Logger.log('>>> Creating new Table: UserGlobalBans', Importance.CRIT, transactionID)
        DatabaseHandler.sendQuery(transactionID, 'CREATE TABLE UserGlobalBans(Discord_UID BIGINT(18));')
        return DatabaseHandler.sendQuery(transactionID, 'SHOW tables like "UserGlobalBans";')

    @staticmethod
    def getUserGlobalBansTable(transactionID: uuid):
        """Gets table for bot's user global bans called 'UserGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            tuple: Will return tuple of tuples containing the table
        """

        results = DatabaseHandler.sendQuery(transactionID, 'SHOW tables like "UserGlobalBans";')

        if len(results) == 0:
            DatabaseHandler.createUserGlobalBansTable(transactionID)
        return results

    @staticmethod
    def getUserGlobalBansTableContents(transactionID: uuid):
        """Gets the contents of the table for bot's user global bans called 'UserGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            tuple: Will return tuple of tuples containing the table's contents
        """

        results = DatabaseHandler.getUserGlobalBansTable(transactionID)

        if len(results) == 0:
            DatabaseHandler.createUserGlobalBansTable(transactionID)
        return DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM UserGlobalBans;')

    @staticmethod
    def addUserGlobalBan(transactionID: uuid, userID: int):
        """Adds userID to table for bot's user global bans called 'UserGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction
            userID (int): The ID of user to Globally Ban

        Returns:
            bool: True if userID was added to GlobalBans table, else False
        """

        matchesFoundInDB = DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM UserGlobalBans WHERE Discord_UID = '+str(userID)+';')

        if len(matchesFoundInDB) == 0:
            Logger.log('>>> Adding new User('+str(userID)+') to: UserGlobalBans', Importance.CRIT, transactionID)
            DatabaseHandler.sendQuery(transactionID, 'INSERT INTO UserGlobalBans (Discord_UID) VALUES ('+str(userID)+');')
            return True
        Logger.log('>>> Attempted to add pre-existing User('+str(userID)+') to: UserGlobalBans', Importance.CRIT, transactionID)
        return False

    @staticmethod
    def removeUserGlobalBan(transactionID: uuid, userID: int):
        """Removes userID from table for bot's user global bans called 'UserGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction
            userID (int): The ID of user to pardon from Global Ban

        Returns:
            bool: True if userID was removed from GlobalBans table, else False
        """

        matchesFoundInDB = DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM UserGlobalBans WHERE Discord_UID = '+str(userID)+';')

        if len(matchesFoundInDB) != 0:
            Logger.log('>>> Removing User('+str(userID)+') from: UserGlobalBans', Importance.CRIT, transactionID)
            DatabaseHandler.sendQuery(transactionID, 'DELETE FROM UserGlobalBans WHERE Discord_UID = '+str(userID)+';')
            return True
        return False

    @staticmethod
    def deleteUserGlobalBansTable(transactionID: uuid):
        """Deletes table for bot's user global bans called 'UserGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            None
        """

        DatabaseHandler.sendQuery(transactionID, 'DROP tables UserGlobalBans;')

    """ Functions to handle Global Guild Bans table """
    @staticmethod
    def createGuildGlobalBansTable(transactionID: uuid):
        """Creates new table for bot's guild global bans called 'GuildGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            tuple: Will return tuple of tuples containing the new table
        """

        Logger.log('>>> Creating new Table: GuildGlobalBans', Importance.CRIT, transactionID)
        DatabaseHandler.sendQuery(transactionID, 'CREATE TABLE GuildGlobalBans(Discord_GID BIGINT(18));')
        return DatabaseHandler.sendQuery(transactionID, 'SHOW tables like "GuildGlobalBans";')

    @staticmethod
    def getGuildGlobalBansTable(transactionID: uuid):
        """Gets table for bot's guild global bans called 'GuildGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            tuple: Will return tuple of tuples containing the table
        """

        results = DatabaseHandler.sendQuery(transactionID, 'SHOW tables like "GuildGlobalBans";')

        if len(results) == 0:
            DatabaseHandler.createGuildGlobalBansTable(transactionID)
        return results

    @staticmethod
    def getGuildGlobalBansTableContents(transactionID: uuid):
        """Gets the contents of the table for bot's guild guild global bans called 'GuildGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            tuple: Will return tuple of tuples containing the table's contents
        """

        results = DatabaseHandler.getGuildGlobalBansTable(transactionID)

        if len(results) == 0:
            DatabaseHandler.createGuildGlobalBansTable(transactionID)
        return DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM GuildGlobalBans;')

    @staticmethod
    def addGuildGlobalBan(transactionID: uuid, guildID: int):
        """Adds guildID to table for bot's guild global bans called 'GuildGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction
            guildID (int): The ID of guild to Globally Ban

        Returns:
            bool: True if guildID was added to GuildGlobalBans table, else False
        """

        matchesFoundInDB = DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM GuildGlobalBans WHERE Discord_GID = '+str(guildID)+';')

        if len(matchesFoundInDB) == 0:
            Logger.log('>>> Adding new Guild('+str(guildID)+') to: GuildGlobalBans', Importance.CRIT, transactionID)
            DatabaseHandler.sendQuery(transactionID, 'INSERT INTO GuildGlobalBans (Discord_GID) VALUES ('+str(guildID)+');')
            return True
        Logger.log('>>> Attempted to add pre-existing Guild('+str(guildID)+') to: GuildGlobalBans', Importance.CRIT, transactionID)
        return False

    @staticmethod
    def removeGuildGlobalBan(transactionID: uuid, guildID: int):
        """Removes guildID from table for bot's guild global bans called 'GuildGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction
            guildID (int): The ID of guild to pardon from Global Ban

        Returns:
            bool: True if guildID was removed from GuildGlobalBans table, else False
        """

        matchesFoundInDB = DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM GuildGlobalBans WHERE Discord_GID = '+str(guildID)+';')

        if len(matchesFoundInDB) != 0:
            Logger.log('>>> Removing Guild('+str(guildID)+') from: GuildGlobalBans', Importance.CRIT, transactionID)
            DatabaseHandler.sendQuery(transactionID, 'DELETE FROM GuildGlobalBans WHERE Discord_GID = '+str(guildID)+';')
            return True
        return False

    @staticmethod
    def deleteGuildGlobalBansTable(transactionID: uuid):
        """Deletes table for bot's guild global bans called 'GuildGlobalBans'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            None
        """

        DatabaseHandler.sendQuery(
            transactionID, 'DROP tables GuildGlobalBans;')

    """ Functions to handle Global Settings table """
    @staticmethod
    def createGlobalSettingsTable(transactionID: uuid):
        """Creates table for bot's global settings called 'GlobalSettings'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            tuple: Will return tuple of tuples containing the global settings table
        """

        # create table
        Logger.log('>>> Creating new Table: GlobalSettings', Importance.CRIT, transactionID)
        DatabaseHandler.sendQuery(transactionID, 'CREATE TABLE GlobalSettings(configKey CHAR(30),configValue CHAR(30));')

        # set default settings
        """
        DatabaseHandler.sendQuery(transactionID, 'INSERT INTO GlobalSettings '
           +"(configKey, configValue) VALUES ('lotto_max_price', '100.0');")
        DatabaseHandler.sendQuery(transactionID, 'INSERT INTO GlobalSettings '
           +"(configKey, configValue) VALUES ('lotto_min_price', '0.00001');")
        DatabaseHandler.sendQuery(transactionID, 'INSERT INTO GlobalSettings '
           +"(configKey, configValue) VALUES ('lotto_max_duration', '120');")
        DatabaseHandler.sendQuery(transactionID, 'INSERT INTO GlobalSettings '
           +"(configKey, configValue) VALUES ('lotto_min_duration', '60');")
        DatabaseHandler.sendQuery(transactionID, 'INSERT INTO GlobalSettings '
           +"(configKey, configValue) VALUES ('lotto_fee_percent', '0');")
        """

        return DatabaseHandler.getGlobalSettingsTable(transactionID)

    @staticmethod
    def getGlobalSettingsTable(transactionID: uuid):
        """Gets table for bot's global settings called 'GlobalSettings'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            tuple: Will return tuple of tuples containing the global settings table
        """

        results = DatabaseHandler.sendQuery(transactionID, 'SHOW tables like "GlobalSettings";')

        if len(results) == 0:
            DatabaseHandler.createGlobalSettingsTable(transactionID)
            results = DatabaseHandler.sendQuery(transactionID, 'SHOW tables like "GlobalSettings";')
        return results

    @staticmethod
    def getGlobalSettingsTableContents(transactionID: uuid):
        """Gets contents of table for bot's global settings called 'GlobalSettings'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            tuple: Will return tuple of tuples containing the global settings
        """

        DatabaseHandler.getGlobalSettingsTable(transactionID)
        return DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM GlobalSettings;')

    @staticmethod
    def modifyGlobalSettingsTable(transactionID: uuid, key: str, value: str):
        """Modifies Global Settings table to change a given key to a new value.

        Parameters:
            transactionID (uuid): The transactionID for current transaction
            key (str): The key in the table to modify
            value (str): The new value for the key

        Returns:
            tuple: Will return tuple of tuples containing the global settings table
        """

        DatabaseHandler.sendQuery(transactionID, "UPDATE GlobalSettings SET configValue = '"+value+"' WHERE"+" configKey = '"+key+"';")
        return DatabaseHandler.getGlobalSettingsTable(transactionID)

    @staticmethod
    def deleteGlobalSettingsTable(transactionID: uuid):
        """Deletes table for bot's global settings called 'GlobalSettings'.

        Parameters:
            transactionID (uuid): The transactionID for current transaction

        Returns:
            None
        """

        DatabaseHandler.sendQuery(transactionID, 'DROP tables GlobalSettings;')

    """ Functions for handling GuildAdmin tables """
    @staticmethod
    def createGuildAdminsTable(transactionID: uuid, guildID: int):
        """Creates table for specified server's guild admins.

        Args:
            transactionID (uuid): The transactionID for current transaction
            guildID (int): The ID of the guild to create the table for

        Returns:
            tuple: Will return tuple of tuples containing the result if no error was encountered
            str: Will return a string if an error was encountered
        """
        Logger.log('>>> Creating new Table: '+str(guildID)+'GuildAdmins', Importance.WARN, transactionID)
        DatabaseHandler.sendQuery(transactionID, 'CREATE TABLE '+str(guildID)+'GuildAdmins('+'Discord_UID BIGINT(18)'+');')
        return DatabaseHandler.sendQuery(transactionID, 'SHOW tables like "'+str(guildID)+'GuildAdmins";')

    # returns table for specified guild's guild admins
    @staticmethod
    def getGuildAdminsTable(transactionID: uuid, guildID: int):
        return DatabaseHandler.sendQuery(transactionID, 'SHOW tables like "'+str(guildID)+'GuildAdmins";')

    # returns contents for guild's guild admins table
    @staticmethod
    def getGuildAdminsTableContents(transactionID: uuid, guildID: int):
        return DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM '+str(guildID)+'GuildAdmins;')

    # adds new guild admin to table for specified guild's guild admins
    @staticmethod
    def addGuildAdmin(transactionID: uuid, guildID: int, userID: int):
        matchesFoundInDB = DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM '+str(guildID)+'GuildAdmins WHERE Discord_UID = '+str(userID)+';')
        if len(matchesFoundInDB) == 0:
            Logger.log('>>> Adding new GuildAdmin('+str(userID)+') to: '+str(guildID)+'GuildAdmins', Importance.WARN, transactionID)
            DatabaseHandler.sendQuery(transactionID, 'INSERT INTO '+str(guildID)+'GuildAdmins '+'(Discord_UID) VALUES ('+str(userID)+');')
            return True
        Logger.log('>>> Attempted to add pre-existing GuildAdmin('+str(userID)+') to: '+str(guildID)+'GuildAdmins', Importance.INFO, transactionID)
        return False

    # removes guild admin from table for specified guild's guild admins
    @staticmethod
    def removeGuildAdmin(transactionID: uuid, guildID: int, userID: int):
        matchesFoundInDB = DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM '+str(guildID)+'GuildAdmins WHERE Discord_UID = '+str(userID)+';')
        if len(matchesFoundInDB) != 0:
            Logger.log('>>> Removing GuildAdmin('+str(userID)+') from: '+str(guildID)+'GuildAdmins', Importance.WARN, transactionID)
            DatabaseHandler.sendQuery(transactionID, 'DELETE FROM '+str(guildID)+'GuildAdmins '+'WHERE Discord_UID = '+str(userID)+';')
            return True
        return False

    # deletes table for specified guild's guild admins
    @staticmethod
    def deleteGuildAdminsTable(transactionID: uuid, guildID: int):
        DatabaseHandler.sendQuery(transactionID, 'DROP tables '+str(guildID)+'GuildAdmins;')

    """ Functions for handling guildSettings tables"""
    # creates new table for specified guild's settings
    @staticmethod
    def createGuildSettingsTable(transactionID: uuid, guildID: int):
        Logger.log('>>> Creating new Table: '+str(guildID)+'GuildSettings', Importance.WARN, transactionID)
        DatabaseHandler.sendQuery(transactionID, 'CREATE TABLE '+str(guildID)+'GuildSettings('+'configKey CHAR(10),'+'configValue CHAR(10)'+');')

        # set default settings
        DatabaseHandler.sendQuery(transactionID, 'INSERT INTO '+str(guildID)+'GuildSettings '+"(configKey, configValue) VALUES ('prefix', '$');")

        return DatabaseHandler.getGuildSettingsTable(transactionID, guildID)

    # returns table for specified guild's settings
    @staticmethod
    def getGuildSettingsTable(transactionID: uuid, guildID: int):
        return DatabaseHandler.sendQuery(transactionID, 'SHOW tables like "'+str(guildID)+'GuildSettings";')

    # returns contents for specified guild's settings table
    @staticmethod
    def getGuildSettingsTableContents(transactionID: uuid, guildID: int):
        return DatabaseHandler.sendQuery(transactionID, 'SELECT * FROM '+str(guildID)+'GuildSettings;')

    # modifies table for specified guild's settings
    @staticmethod
    def modifyGuildSettingsTable(transactionID: uuid, guildID: int, key: str, value: str):
        DatabaseHandler.sendQuery(transactionID, 'UPDATE '+str(guildID)+"GuildSettings SET configValue = '"+value+"' WHERE"+" configKey = '"+key+"';")
        return DatabaseHandler.getGuildSettingsTable(transactionID, guildID)

    # deletes table for specified guild's settings
    @staticmethod
    def deleteGuildSettingsTable(transactionID: uuid, guildID: int):
        DatabaseHandler.sendQuery(transactionID, 'DROP tables '+str(guildID)+'GuildSettings;')
