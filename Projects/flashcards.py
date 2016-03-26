# coding: utf8
import requests
from lxml import html
import re
import csv
import sys

base_url = "http://dictionnaire.reverso.net/anglais-francais/"

#Load the page
def get_content(url):
    response = requests.get(url)
    content = response.text
    return html.fromstring(content)

#Check if there is a definition section on the page
def definition_section(page):
    XPATH_1 = """//*[@id="ctl00_cC_ucResPM_divSource"]"""
    XPATH_2 = """//*[@id="ctl00_cC_ucResEM_divSource"]"""
    return len(page.xpath(XPATH_1)) != 0 or len(page.xpath(XPATH_2)) != 0

#Check if there is a content section on the page
def context_section(page):
    XPATH = """//*[@id="contextSection"]"""
    return len(page.xpath(XPATH)) != 0

#Get the translation
def get_word_details(page):
    #List of xpath
    XPATH_fr1 = """//*[@id="ctl00_cC_ucResPM_lblTranslation"]/text() """
    XPATH_fr2 = """//*[@id="ctl00_cC_ucResEM_lblTranslation"]/text() """

    XPATH_context_eng = """//*[@id="ctxRes"]/table/tr[1]/td[1]/text/text()"""
    XPATH_context_word_eng = """//*[@id="ctxRes"]/table/tr[1]/td[1]/text/span/text()"""
    XPATH_context_fr = """//*[@id="ctxRes"]/table/tr[1]/td[2]/text/text()"""
    XPATH_context_word_fr = """//*[@id="ctxRes"]/table/tr[1]/td[2]/text/span/text()"""

    if definition_section(page):
        try:
            french = page.xpath(XPATH_fr1)[0].encode("utf8")
        except:
            french = page.xpath(XPATH_fr2)[0].encode("utf8")
    else:
        english = "not available"
        french = "not available"

    if context_section(page):
        try:
            context_english = page.xpath(XPATH_context_eng)[0].encode("utf8") + page.xpath(XPATH_context_word_eng)[0].encode("utf8") + page.xpath(XPATH_context_eng)[1].encode("utf8")
            context_french = page.xpath(XPATH_context_fr)[0].encode("utf8") + page.xpath(XPATH_context_word_fr)[0].encode("utf8") + page.xpath(XPATH_context_fr)[1].encode("utf8")
        except:
            context_english = "not available"
            context_french = "not available"
    else:
        context_english = "not available"
        context_french = "not available"

    return french, context_english, context_french

#Build world list from text file
def build_words_list(path):
    words = []
    with open(path) as f:
        for line in f:
            match = re.search(r'([\w\s]+)-([\w\s,]+)', line)
            words.append((match.group(1),match.group(2).replace("\n","")))
    return words

#path = "C:\Users\JC\Desktop\dscamp\dscamp\EC2\ubi400.txt"

#Space in the terminal
def clean():
    print '\n' * 100

#Load everything into a csv file
"""
with open("C:\Users\JC\Desktop\dscamp\dscamp\EC2\ubi400.csv","wb") as f:
    counter = 0
    try:
        c = csv.writer(f)
        c.writerow(["english", "synonym", "french", "context_english", "context_french","known/unknown"])

        for tup in build_words_list(path):
            url = base_url + tup[0]
            english = tup[0].strip()
            synonym = tup[1].strip()
            french = get_word_details(get_content(url))[0].strip()
            context_english = get_word_details(get_content(url))[1].strip()
            context_french = get_word_details(get_content(url))[2].strip()

            c.writerow([english, synonym, french, context_english, context_french,"0"])
            counter = counter + 1
            print counter
    finally:
        f.close()
        print counter
"""

# split file into chuncks
def split_file(path, number_chunks):
    with open(path,"rb") as f1:
        c = csv.reader(f1)
        lines = list(c)
        leap = 0
        chunk_size = round(len(lines)/float(number_chunks),0)
        for i in range(1,number_chunks + 1):
            rows = lines[int(0 + leap) : int(chunk_size + leap)]
            leap = leap + chunk_size
            with open("C:\Users\JC\Desktop\dscamp\dscamp\EC2\ubi400-" + str(i) + ".csv","wb") as f2:
                c = csv.writer(f2)
                c.writerows(rows)
            f2.close()
    f1.close()

#split_file(path,8)

# Go through deck
def browse_deck(path):
    with open(path,"rb") as f:
        c = csv.reader(f)
        lines = list(c)
        length = [x for x in lines if x[5] == "0"]
        length = len(length)
        known, unknown, counter = 0, 0, 1
        for line in lines:
            if line[5] == "0":
                print "{0} over {1}".format(counter, length)
                print '\n'
                print line[0].upper()
                print '\n'
                input = raw_input("Press M to see definition or ENTER to go to next word")
                print '*****'
                if input == "m":
                    print "word: " + line[0].upper()
                    print "syn: " + line[1].upper()
                    print '\n'
                    print ">: " + line[3]
                    print "......."
                    print ">: " + line[4]
                    print '\n'
                    line[5] = "0"
                    unknown += 1
                    input = raw_input("Press ENTER to continue")
                else:
                    line[5] = "1"
                    known += 1
                    pass
                counter += 1
                print '*****'
                clean()
        try:
            score = (known / float(known + unknown))*100
        except:
            score = 100

        print "Score: {0}".format(score)
        f.close()
        with open(path,"wb") as f:
            c = csv.writer(f)
            c.writerows(lines)
        f.close()
    return score

#Practice deck
def learn_deck(deck):
    path = "C:\Users\JC\Desktop\dscamp\dscamp\EC2\\" + deck + ".csv"
    score = 0
    while score != 100:
        score = browse_deck(path)


def main():
    deck = str(sys.argv[1])
    learn_deck(deck)

if __name__ == "__main__":
    main()






















