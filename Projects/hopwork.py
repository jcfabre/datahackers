import requests
from datetime import datetime
from pytz import timezone
import re
import time
from lxml import html
from prettytable import PrettyTable
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

base_url = "https://www.upwork.com"
start_url = "https://www.upwork.com/o/jobs/browse/c/data-science-analytics/"

def parse_body(url):
    response = requests.get(url)
    source = response.text
    return html.fromstring(source)

def get_page_url(number):
    return start_url + "/?page=" + str(number)

def get_article_info(art):
    paristime = timezone('Europe/Paris')
    utctime = timezone('UTC')
    format = "%Y-%m-%d %H:%M:%S"

    try:
        href = base_url + art.xpath("./div/div/header/h2/a/@href")[0]
    except:
        href = '*****'

    try:
        title = art.xpath("./div/div/header/h2/a/text()")[0].strip("\n").strip()
    except:
        title = '*****'

    try:
        description = art.xpath("./div/div/div/div/text()")
    except:
        description = '*****'

    try:
        payment = art.xpath("./div/div/small/strong/text()")[0]
    except:
        payment = '*****'

    try:
        level = art.xpath("./div/div/small/*[@class='js-contractor-tier']/text()")[0].strip("\n").strip()
    except:
        level = '*****'

    try:
        budget = art.xpath("./div/div/small/*[@class='js-budget']/text()")[0].strip("\n").strip() + ' ' + art.xpath("./div/div/small/*[@class='js-budget']/*[@itemprop='baseSalary']/text()")[0].strip("\n").strip()
    except:
        budget = '*****'

    try:
        estimated_time = art.xpath("./div/div/small/*[@class='js-duration']/text()")[0].strip("\n").strip()
    except:
        estimated_time = '*****'

    try:
        posted = art.xpath("./div/div/small/*[@class='js-posted']/time/@datetime")[0]
        re_date = re.search(r'\d{4}-\d{2}-\d{2}', posted).group()
        re_hour = re.search(r'\d{2}:\d{2}:\d{2}', posted).group()
        posted = utctime.localize(datetime.strptime(re_date+' '+re_hour, "%Y-%m-%d %H:%M:%S")).astimezone(paristime).strftime(format)
    except:
        posted = 'Not Available'


    return (title, payment, level, budget, estimated_time, posted, href)


def get_articles(page):
    for elt in page.xpath("//article")[:-1]:
        yield elt

page = parse_body(start_url)

def timediff(d1,d2):
    return (d2 - d1).total_seconds()/float(60)

def get_last_jobs(x):
    t = PrettyTable(['title', 'payment', 'level', 'budget', 'estimated_time', 'posted','href',])
    d1 = datetime.now()
    i = 0
    url = start_url
    while timediff(d1,datetime.now()) <= x * 60:
        page = parse_body(url)
        for elt in get_articles(page):
            t.add_row(list(get_article_info(elt)))
            d1 = datetime.strptime(get_article_info(elt)[-2],"%Y-%m-%d %H:%M:%S")
            if timediff(d1,datetime.now()) > x * 60:
                break
        i = i + 1
        url = get_page_url(i)

    filename = "Jobs "+ datetime.now().strftime("%Y-%m-%d %H-%M-%S") +".txt"
    with open(filename,'w') as f:
        f.write(t.get_string().encode('utf8'))
        f.close()
    return filename


def main():
    fromaddr = "YOUR EMAIL ADDRESS"
    toaddr = "WHERE YOU WANT TO SEND IT TO"
    msg = MIMEMultipart()

    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Jobs from hopwork :)"

    body = "Awesome !"

    msg.attach(MIMEText(body, 'plain'))

    filename = get_last_jobs(6)
    attachment = open("PATH" + get_last_jobs(6), "rb")

    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "YOUR PASSWORD")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

main()