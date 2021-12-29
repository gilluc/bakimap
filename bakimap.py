# bakimap.py
# (c) gilles lucato
# backups messages in EML format from a list of folders of an IMAP account to the local directory where the python script is.
# the script creates locally a subdirectory for the account and a subsubdirectory for each IMAP folder where the EML messages will be.
# 'NEW only' mode (recommended) backup only non already backuped messages from IMAP folders (like incremental).
# 'RESET all' mode delete previously backuped message and backup all messages from IMAP folders (like mirror).

import os
import re
import ssl
import hashlib
import datetime
from imapclient import IMAPClient

# params
HOST     = "imap.me.com"
USERNAME = "me@me.com"
PASSWORD = "$$##$$"
FOLDERS  = ["INBOX", "Sent"]        # folder list to backup
BACKUP   = "NEW"   # "NEW" to backup only new messages or "RESET" to backup all messages to match exactly what is in IMAP server

# build path to store emails in folder
def BuildPath(host, user, folder):
    path = './' + host
    if (os.path.isdir(path)==False):
        os.mkdir(path)
    path = './' + host + '/' + user
    if (os.path.isdir(path)==False):
        os.mkdir(path)
    path = './' + host + '/' + user + '/' + folder
    if (os.path.isdir(path)==False):
        os.mkdir(path)
    return path

# remove all previous messages in this folder
def RemoveExistingBackup(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in dirs:
            subdir = os.path.join(root, name)
            RemoveExistingBackup(subdir)
            os.rmdir(subdir)
        for name in files:
            os.remove(os.path.join(root, name))
            
# convert month to number
def ConvertMonth(month):
    if (month == 'Jan'):
        return '01'
    if (month == 'Feb'):
        return '02'
    if (month == 'Mar'):
        return '03'
    if (month == 'Apr'):
        return '04'
    if (month == 'May'):
        return '05'
    if (month == 'Jun'):
        return '06'
    if (month == 'Jul'):
        return '07'
    if (month == 'Aug'):
        return '08'
    if (month == 'Sep'):
        return '09'
    if (month == 'Oct'):
        return '10'
    if (month == 'Nov'):
        return '11'
    if (month == 'Dec'):
        return '12'
    return '99'

# build unique filename for email in a way that an email will have the same name ever and all names will be different (i hope)
def BuildFilename(body):
    #today = datetime.datetime.today()
    #getdate = f"{today:%Y%m%d_%H%M%S}"
    getdate = '20000101_120000'
    posdate = body.find(b'\nDate: ')
    if (posdate >=0):
        enddate = body.find(b'\r', posdate)
        if (enddate < posdate):
            endate = posdate + 32
        zone = body[posdate:enddate]
        match = re.search(r'(\d{2,2}) (\w{3,3}) (\d{4,4}) (\d{2,2}):(\d{2,2}):(\d{2,2})', str(zone))
        if match:
            getdate = match[3] + ConvertMonth(match[2]) + match[1] + '_' + match[4] +match[5] + match[6]
        
    getid = '12345678'
    posid   = body.find(b'\nMessage-ID: ')
    if (posid >=0):
        endid = body.find(b'\r', posid)
        if (endid < posid):
            endid = posid + 128
        zone = body[posid:endid]
        match = re.search(r'<([^>]*)>', str(zone))
        if match:
            getid = str(int(hashlib.sha1(match[1].encode("utf-8")).hexdigest(), 16) % (10 ** 8))
        
    fname = '/' + getdate + '_' + getid + '.eml'
    return fname

# main -------------------------------------------------------------------------

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

for cfolder in FOLDERS:
    with IMAPClient(HOST, ssl_context=ssl_context) as server:
        server.login(USERNAME, PASSWORD)
        backuped = 0
        folderpath = BuildPath(HOST, USERNAME, cfolder)
        if (BACKUP == "RESET"):
            print ('Reset All Mode!')
            RemoveExistingBackup(folderpath)
        else:
            print ('New Only Mode!')
        
        select_info = server.select_folder(cfolder, readonly=True)
        print('%d messages in %s' % (select_info[b'EXISTS'] ,cfolder))

        messages = server.search() # [b'NOT', b'DELETED']
        for uid, message_data in server.fetch(messages, "RFC822").items():
            fil = bytearray();
            fil = message_data[b"RFC822"]

            filename = folderpath + BuildFilename(fil)
            if (BACKUP == "RESET") or (os.path.isfile(filename)==False):
                fout = open(filename, 'wb')
                fout.write(fil)
                fout.close()
                backuped += 1

        server.logout()
        print('%d new messages' % (backuped))

