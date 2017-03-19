# Legacy Obituaries
## LegacyObits.py
### Description
This is an example of a screen scraping program using BeautifulSoup.  This is intended to be ran once a day, and will \
retrieve obituaries from the popular Legacy.com website.

Requirement:  Install BeautifulSoup (pip install bs4)

(I recommend running in a container, or virtualenv.)

$pip install -r requirements.txt
###Usage
```$python LegacyObits.py -recipient=<emails - comma delimted> -smtpserver=smtp.gmail.com:587 -smtpuser=<your gmail> -smtppassword=<your password> -url=http://www.legacy.com/obituaries/<your-newspaper>/browse?dateRange=today```
