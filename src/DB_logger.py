# Generic-DiscordBot
# author: github/adibarra

# imports
import os
import time
import uuid
import enum
import glob
import traceback
from zipfile import ZipFile
from DB_prefsloader import PreferenceLoader


class Importance(enum.IntEnum):
    """ Enum to keep track of logger message importance """
    CRIT = 0
    WARN = 1
    INFO = 2
    DBUG = 3


class Transaction:
    """ Class to keep all same transactions together """

    logs = []
    transaction_ID = None

    def __init__(self, transaction_ID: uuid):
        self.logs = []
        self.transaction_ID = transaction_ID

    def addMessage(self, message: str):
        self.logs.append(message)

    def getMessages(self):
        return self.logs


class Logger:
    """ Class to handle logging """
    transaction_cache = []

    # log message to logfile
    def log(message: str, importance: int, transactionID: uuid = None, final=False):
        if not PreferenceLoader.logger_enabled:
            return
        else:
            # if logs folder does not exist then create it
            try:
                if not os.path.exists(os.path.dirname(os.path.realpath(__file__))+'/../logs'):
                    original_umask = os.umask(0)
                    os.makedirs(os.path.dirname(os.path.realpath(__file__))+'/../logs')
                    os.umask(original_umask)
            except Exception as e:
                print('There was an error while trying to create the logs directory:')
                print(e)

            # if logfile for today does not exist then create it
            filePath = os.path.dirname(os.path.realpath(__file__))+'/../logs/'+time.strftime('log-%Y-%m-%d')+'.log'
            if not os.path.isfile(filePath):
                try:
                    open(filePath, 'a').close()
                except Exception as e:
                    print('There was an error while trying to create the logfile:')
                    print(e)

            # let transactions bunch up until final or special ones come through
            if importance != None and transactionID != None and importance <= Importance[PreferenceLoader.verbositySetting].value:
                found = False
                for transaction in Logger.transaction_cache:
                    if transaction.transaction_ID == transactionID:
                        transaction.addMessage(time.strftime('%Y-%m-%d %H:%M:%S')+' '+(str(transactionID)[:13]+' ['+Importance(importance).name+'] '+message))
                        found = True
                        break

                if not found:
                    newTransaction = Transaction(transactionID)
                    newTransaction.addMessage(time.strftime('%Y-%m-%d %H:%M:%S')+' '+(str(transactionID)[:13]+' ['+Importance(importance).name+'] '+message))
                    Logger.transaction_cache.append(newTransaction)

            # final transaction for batch has come through, write it to the file
            if final or importance == None or transactionID == None:
                try:
                    to_write = ''
                    with open(filePath, 'a') as (logFile):

                        # if importance or transactionID are None then immediately write to logfile
                        if importance == None or transactionID == None:
                            logFile.write(message+'\n')
                            return

                        # else build to_write str from transaction_cache
                        else:
                            for transaction in Logger.transaction_cache:
                                if transaction.transaction_ID == transactionID:
                                    # get matching transactions and build to_write str
                                    for trans_message in transaction.getMessages():
                                        if importance <= Importance[PreferenceLoader.verbositySetting].value:
                                            to_write += trans_message+'\n'
                                    # remove transaction from cache
                                    Logger.transaction_cache.remove(transaction)
                                    break

                        # write to logfile
                        if to_write != '':
                            logFile.write(to_write+'\n')

                    # if logfile gets too big (10 MB), rename current logfile and later autocreate another
                    if os.stat(filePath).st_size > 1e+7:
                        log_number = 0
                        # iterate through logs for the day and find largest logfile number
                        for name in glob.glob(filePath[:len(filePath)-4]+'*'):
                            if len(name.split('/')[-1].split('.')) > 2:
                                num = int(name.split('/')[-1].split('.')[1])
                                if num > log_number:
                                    log_number = num

                        # rename current log to largest log number +1 then zip and delete original
                        fileName = (filePath[:len(filePath)-4]+'.'+str(log_number+1)+'.log').split('/')[-1]
                        os.rename(filePath, filePath[:len(filePath)-4]+'.'+str(log_number+1)+'.log')
                        with ZipFile(filePath[:len(filePath)-4]+'.'+str(log_number+1)+'.log.zip', 'w') as zip:
                            zip.write(filePath[:len(filePath)-4]+'.'+str(log_number+1)+'.log', fileName)
                        os.remove(filePath[:len(filePath)-4]+'.'+str(log_number+1)+'.log')

                except Exception as e:
                    print('There was an error when reading or writing a file:')
                    print(traceback.format_exc())
