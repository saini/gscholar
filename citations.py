import logging
import sys
import time
from lxml import html
import requests
import json
import logging
import sys
import time
import random


class Author:

    def __init__(self):
        pass


class Crawler:
    def __init__(self, config):
        self.config = config
        self.baseUrl = "https://scholar.google.com"
        self.headers = {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36"}

    def crawl(self):
        page = requests.get('https://scholar.google.com/scholar?oi=bibs&hl=en&cites=1629517509046821994')
        tree = html.fromstring(page.content)
        links = list(tree.iterlinks())
        authorLinks = []
        for link in links:
            (element, attribute, url, pos) = link
            if "citations?user=" in url:
                print(element, attribute, url, pos)
                print(element.text)
                authorLinks.append(link)

        return authorLinks

    def getAllCitedByBaseLinks(self):
        userProfileUrl = "https://scholar.google.com/citations?user=YMymR_wAAAAJ&hl=en"
        page = self.getPage(userProfileUrl)
        tree = html.fromstring(page.content)
        elements = tree.xpath("//td[contains(@class, 'gsc_a_c')]")
        links = []
        for element in elements:
            anchors = element.xpath(".//a")
            for anchor in anchors:
                if (anchor.text):
                    link = self.getScholarPageLink(anchor.get("href"))
                    #print(anchor.text, link)
                    links.append(link)
        return links

    def getAllSubsequentPageLinks(self, basePageUrl):
        newPages = []
        nextPage = basePageUrl
        while nextPage:
            time.sleep(2)
            nextPage = self.getNextCitedByLink(nextPage)
            newPages.append(nextPage)

        return newPages

    def getNextCitedByLink(self, pageUrl):
        page = self.getPage(pageUrl)
        tree = html.fromstring(page.content)
        #element = tree.xpath("//div[@id = 'gs_n']")
        anchors = tree.xpath(".//a")
        for anchor in anchors:
            bs = anchor.xpath(".//b")
            link = anchor.get("href")
            if "scholar?start" in anchor.get("href"):
                for b in bs:
                    if b.text == "Next":
                        link = self.getScholarPageLink(link)
                        return link

    def getScholarPageLink(self, inputLink):
        if (inputLink.startswith("https://scholar")):
            return inputLink
        return self.baseUrl + inputLink

    def extractAuthorAffiliation(self, authorLink):
        (element, attribute, url, pos) = authorLink
        userLink = self.baseUrl + url
        page = requests.get(userLink)
        tree = html.fromstring(page.content)

    def extract_acm_author_info(self, url):
        page = self.getPage(url)
        tree = html.fromstring(page.content)
        elements = tree.xpath("//div[contains(@class, 'auth-info')]")
        authors = []
        for element in elements:
            spans = element.xpath(".//span")
            author = Author()
            for span in spans:
                anchors = span.xpath(".//a")

                for anchor in anchors:
                    #print(anchor.text)
                    author.Name = anchor.text.strip()
                if len(span.text.strip()) > 0:
                    #print(span.text.strip())
                    author.Affiliation = span.text.strip()
                    authors.append(author)

        return authors

    def extract_ieee_author_info(self, url):
        url = url + "/authors#authors"
        page = self.getPage(url)
        endString = ';\n\n\n\n\txplGlobal.document.snippet="true"'
        startString = 'document.metadata='
        content = page.content.decode("utf-8")
        startMetadataIndex = content.find(startString) + len(startString)
        endMetadataIndex = content.find(endString)
        metadata = content[startMetadataIndex:endMetadataIndex]
        metadict = json.loads(metadata)
        authors = metadict["authors"]
        authorList = []
        for author in authors:
            a = Author()
            a.Name = author['name']
            a.Affiliation = author['affiliation'][0]
            authorList.append(a)
        return authorList

    def extract_springer_author_info(self, url):
        page = self.getPage(url)
        tree = html.fromstring(page.content)
        authorNames = tree.xpath("//span[contains(@class, 'authors-affiliations__name')]")
        affiliations = tree.xpath("//span[contains(@class, 'affiliation__name')]")
        cities = tree.xpath("//span[contains(@class, 'affiliation__city')]")
        countries = tree.xpath("//span[contains(@class, 'affiliation__country')]")
        authors = []
        index = 0
        for authorName in authorNames:
            author = Author()
            author.Name = authorName.text
            affiliation = affiliations[index]
            city = cities[index]
            country = countries[index]
            author.Affiliation = affiliation.text+", " + city.text+", "+ country.text
            index = index + 1
            authors.append(author)

        return authors

    def getPage(self, url):
        sleepFor = random.randint(2,7)
        time.sleep(sleepFor)
        page = requests.get(url, headers=self.headers)
        return page

if __name__ == "__main__":
    c = Crawler({})
    #c.testProxy()
    #sys.exit()
    basePages = c.getAllCitedByBaseLinks()
    allSubsequentLinks = []
    for page in basePages:
        newLinks = c.getAllSubsequentPageLinks(page)
        if newLinks:
            print ("found more pages: ", len(newLinks))
            allSubsequentLinks = allSubsequentLinks + newLinks

    allPages = basePages+allSubsequentLinks

    print ("************************************")
    for page in allPages:
        print (page)
   # for author in authors:
   #     print(author.Name, author.Affiliation)
    print ("total pages to scan", len(allPages))
    print("finished!")
