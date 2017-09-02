import json
from urllib import request
import argparse
import sqlite3
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import re

conn = sqlite3.connect('obits.db')
c = conn.cursor()

class Obituary(object):
    def __init__(self):
        self.ObitID = None
        self.Name = None
        self.Url = None
        self.ImageUrl = None
        self.ObituaryText = None
        self.sendme = False
    def __str__(self):
        return unicode(self).encode('utf-8')

def ConnectToDB():
    sql = 'create table if not exists obits (id integer)'
    c.execute(sql)

    c.execute(sql)
    conn.commit()

def JustRetrieved(obitID):
    sql = 'insert into obits (id) values (%d)' % obitID
    c.execute(sql)
    conn.commit()

def HasAlreadyRetrieved(obitID):
    returnValue = False
    sql = 'select id from obits where id = ' + str(obitID)
    c.execute(sql)
    data=c.fetchall()
    if len(data) == 0:
        print ('Obit not retrieved yet for: ' + str(obitID))
    else:
        print ('Obit ALREADY retrieved for: ' + str(obitID))
        returnValue = True

    return returnValue

def GenerateHtml(obits):
    returnValue = '<html><table border=1>'
    for obit in obits:
        if obit.ObituaryText is not None and obit.sendme == True:
            returnValue += '<tr><td><img src=' + str(obit.ImageUrl) + '><br/>' + obit.Name + '</td>'
            returnValue += '<td>' + str(obit.ObituaryText) + '</td></tr>'
    returnValue += '</table></html>'
    return returnValue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grabs all the obits")
    parser.add_argument('-url','--url',help='URL', required=True)
    parser.add_argument('-recipient','--recipient',help='Email Recipient', required=True)
    parser.add_argument('-smtpuser','--smtpuser',help='SMTP User', required=False)
    parser.add_argument('-smtppassword','--smtppassword',help='SMTP Password', required=False)
    parser.add_argument('-smtpserver','--smtpserver',help='SMTP Server', required=True)
    ConnectToDB()

    args = vars(parser.parse_args())
    url = args['url']
    print ('Using: ' + url)

    response = request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, 'html.parser')

    #script = soup.find('script', text=re.compile('window\.blog\.data'))
    script = soup.find('script', text=re.compile('window\.__INITIAL_STATE__'))
    json_text = re.search(r'^\s*window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;\s*$',
                          script.string, flags=re.DOTALL | re.MULTILINE).group(1)
    data = json.loads(json_text)
    #assert data['activity']['type'] == 'read'

    obits = []
    for entry in data['BrowseStore']['data']['obituaries']['obituaries']['edges']:
        o = Obituary()
        o.Name = entry['node']['name']['firstName'] + ' ' + entry['node']['name']['lastName']
        o.ObitID = entry['node']['personId']
        o.ImageUrl = entry['node']['photoUrl']
        #throw the candle up
        if o.ImageUrl is None:
            o.ImageUrl = 'http://ak-static.legacy.net/obituaries/images/premiumobit/premiumobit_candle.jpg?v=105.0.0.11909'
        else:
            o.ImageUrl += 'x?w=168&h=168&option=3&v=1562247837631119400'
        o.ObituaryText =  entry['node']['obituaryNoHtml'].replace('\n', ' ')
        o.Url = 'http://www.legacy.com' + entry['node']['links']['obituaryUrl']['path']
        obits.append(o)
    print (len(obits))
    Body = 'There are no obits.'
    anyObits = False
    for obit in obits:
        if not HasAlreadyRetrieved(obit.ObitID):
            anyObits = True
            obit.sendme = True
            JustRetrieved(obit.ObitID)
    if anyObits:
         Body = GenerateHtml(obits)
    Body = Body.encode('ascii','ignore')
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "New Obituaries"
    msg['From'] = 'noreply@example.com'
    recipients = []
    parts = args['recipient'].split(',')
    for recipient in parts:
        recipients = []
        recipients.append(recipient)
        msg['BCC'] = ", ".join(recipients)

    #     # Create the body of the message (a plain-text and an HTML version).
        text = Body.decode('ascii')
        html = Body.decode('ascii')
    #     # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
    #
    #     # Attach parts into message container.
    #     # According to RFC 2046, the last part of a multipart message, in this case
    #     # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)
    #
        smtpserver = smtplib.SMTP(args['smtpserver'],timeout=10)
    #     # Send the message via local SMTP server.
        if args['smtpuser'] != "":
            print('Starting TTLS with user %s' % args['smtpuser'])
            smtpserver.starttls()
            smtpserver.login(args['smtpuser'], args['smtppassword'])
    #     # sendmail function takes 3 arguments: sender's address, recipient's address
    #     # and message to send - here it is sent as one string.
            smtpserver.sendmail('noreply@acudea.com', recipients, msg.as_string())
            smtpserver.quit()
