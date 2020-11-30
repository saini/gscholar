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
from fake_useragent import UserAgent


class Author:

    def __init__(self):
        pass

class Publisher:
    def __init__(self):
        pass


class Crawler:
    def __init__(self, config):
        self.config = config
        self.baseUrl = "https://scholar.google.com"
        self.headers = {"User-Agent": UserAgent().random}
        self.pagesProcessed = 0
        self.totalPages = 0
        self.session = requests.Session()
        self.requestCount =0

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
            nextPage = self.getNextCitedByLink(nextPage)
            if nextPage:
                print("found: ", nextPage)
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
        print ("extracting author affiliation")
        (element, attribute, url, pos) = authorLink
        userLink = self.baseUrl + url
        page = requests.get(userLink)
        tree = html.fromstring(page.content)

    def extract_acm_author_info(self, url):
        print("extracting acm author, ", url)
        page = self.getPage(url)
        tree = html.fromstring(page.content)
        elements = tree.xpath("//div[contains(@class, 'auth-info')]")
        authors = []
        for element in elements:
            try:
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
            except:
                print("Unexpected error:", sys.exc_info()[0])

        return authors

    def extract_ieee_author_info(self, url):
        print("extracting ieee author, ", url)
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
            try:
                a = Author()
                a.Name = author['name']
                a.Affiliation = author['affiliation'][0]
                authorList.append(a)
            except:
                print("Unexpected error:", sys.exc_info()[0])
        return authorList

    def extract_springer_author_info(self, url):
        print("extracting springer author, ", url)
        page = self.getPage(url)
        tree = html.fromstring(page.content)
        authorNames = tree.xpath("//span[contains(@class, 'authors-affiliations__name')]")
        affiliations = tree.xpath("//span[contains(@class, 'affiliation__name')]")
        cities = tree.xpath("//span[contains(@class, 'affiliation__city')]")
        countries = tree.xpath("//span[contains(@class, 'affiliation__country')]")
        authors = []
        index = 0
        for authorName in authorNames:
            try:
                author = Author()
                author.Name = authorName.text
                affiliation = affiliations[index]
                city = cities[index]
                country = countries[index]
                author.Affiliation = affiliation.text+", " + city.text+", "+ country.text
                index = index + 1
                authors.append(author)
            except:
                print("exception while processing ")

        return authors

    def getAllArticleVersionsUrlsOnPage(self, url):
        print("Getting All Article Versions for", url)
        page = self.getPage(url)
        root = html.fromstring(page.content)
        links = []
        anchors = root.xpath(".//a")
        for anchor in anchors:
            link = anchor.get("href")
            if "scholar?cluster" in anchor.get("href"):
                link = self.getScholarPageLink(link)
                links.append(link)

        print("number of article versions found", len(links))
        return links

    def getKnownPublisherUrls(self, urls):
        print("inside getKnownPublisherUrls")
        citedBy = {}
        for url in urls:
            print("Getting known publisher for ", url)
            page = self.getPage(url)
            root = html.fromstring(page.content)
            anchors = root.xpath(".//a")
            for anchor in anchors:
                link = anchor.get("href")
                if "https://dl.acm.org/doi/abs" in link:
                    print("found acm publisher")
                    publisher = Publisher()
                    publisher.Name = "acm"
                    publisher.ArticleUrl = link
                    citedBy[url] = publisher
                    break
                if "https://ieeexplore.ieee.org/" in link:
                    print("found ieee publisher")
                    publisher = Publisher()
                    publisher.Name = "ieee"
                    publisher.ArticleUrl = link
                    citedBy[url] = publisher
                    break
                if "https://link.springer.com" in link:
                    print("found springer publisher")
                    publisher = Publisher()
                    publisher.Name = "springer"
                    publisher.ArticleUrl = link
                    citedBy[url] = publisher
                    break
        return citedBy

    def getPage(self, url):
        sleepFor = random.randint(5,15)
        print("sleeping for ", sleepFor, "seconds")
        time.sleep(sleepFor)
        if self.requestCount % 5 ==0:
            self.headers = {"User-Agent": UserAgent().random}
        response = self.session.get(url, headers=self.headers)
        print("received response with code: ", response.status_code)
        response.raise_for_status()
        self.requestCount += 1
        return response

    def start(self):
        print("creating authors file")
        self.createAuthorsFile("Authors.csv")

        print("Getting base pages from profile link")
        basePages = self.getAllCitedByBaseLinks()
        print("Number of base pages found ", len(basePages))

        print("getting subsequent pages from every base page")
        allSubsequentLinks = []
        for page in basePages:
            newLinks = self.getAllSubsequentPageLinks(page)
            if newLinks:
                print("found more pages: ", len(newLinks))
                allSubsequentLinks = allSubsequentLinks + newLinks

        allPages = basePages + allSubsequentLinks
        self.totalPages = len(allPages)
        print("total pages to scan", len(allPages))
        self.writeAllPagesToFile("AllPages.txt", allPages)

        # extract get all article version urls from pages
        for page in allPages:
            self.writeToStatusFile("status.txt", page)
            self.extractAuthorInfoAndWriteTofile(page)
            self.pagesProcessed += 1
            progress = self.getProgress()
            print("processed ", progress, "%")

    def processAllPages(self):
        self.createAuthorsFile("Authors.csv")
        with open("AllPages.txt") as f:
            lines = [line.rstrip() for line in f]
            self.totalPages = len(lines)
            for page in lines:
                self.writeToStatusFile("status.txt", page)
                self.extractAuthorInfoAndWriteTofile(page)
                self.pagesProcessed += 1
                progress = self.getProgress()
                print("processed ", progress, "%")

    def processAllSubsequentPageLinks(self, page):
        nextPage = page
        while nextPage:
            self.extractAuthorInfoAndWriteTofile(nextPage)
            self.writeToStatusFile("status.txt", nextPage)
            self.pagesProcessed += 1
            nextPage = self.getNextCitedByLink(nextPage)
            if nextPage:
                print("found: ", nextPage)

    def start2(self, pageIndex):
        print("creating authors file")
        self.AuthorsFile = "Authors-{pi}.csv".format(pi=pageIndex)
        self.createAuthorsFile(self.AuthorsFile)
        print("Getting base pages from profile link")
        basePages = self.getAllCitedByBaseLinks()
        print("Number of base pages found ", len(basePages))
        print("getting subsequent pages from every base page")
        count = 0
        for page in basePages:
            if count == pageIndex:
                self.processAllSubsequentPageLinks(page)
                print("processed all child pages of", page)
            count +=1

    def getProgress(self):
        return self.pagesProcessed * 100/self.totalPages

    def extractAuthorInfoAndWriteTofile(self, page):
        links = self.getAllArticleVersionsUrlsOnPage(page)
        citedBy = self.getKnownPublisherUrls(links)
        if citedBy:
            for key, value in citedBy.items():
                if value.Name == "acm":
                    authors = self.extract_acm_author_info(value.ArticleUrl)
                    self.writeAuthorsToFile(self.AuthorsFile, authors)
                if value.Name == "ieee":
                    authors = self.extract_ieee_author_info(value.ArticleUrl)
                    self.writeAuthorsToFile(self.AuthorsFile, authors)
                if value.Name == "springer":
                    authors = self.extract_springer_author_info(value.ArticleUrl)
                    self.writeAuthorsToFile(self.AuthorsFile, authors)

    def writeAllPagesToFile(self, filename, listPages):
        print("writing to file: ", filename)
        with open(filename, 'w', encoding="utf-8") as the_file:
            for page in listPages:
                print(page)
                the_file.write(page+"\n")

    def writeAuthorsToFile(self, filename, authors):
        print("writing authors to file: ", filename)
        with open(filename, 'a', encoding="utf-8") as the_file:
            for author in authors:
                row = author.Name + "|" + author.Affiliation + "\n"
                print(row)
                the_file.write(row)

    def createAuthorsFile(self, filename):
        with open(filename, 'w', encoding="utf-8") as the_file:
            row = "Name" + "|" + "Affiliation" + "\n"
            print(row)
            the_file.write(row)

    def writeToStatusFile(self, filename, page):
        with open(filename, 'a+', encoding="utf-8") as the_file:
            print("Status: processing page", self.pagesProcessed, page)
            the_file.write(page + "\n")

if __name__ == "__main__":
    c = Crawler({})
    #c.start()
    if len(sys.argv) == 2:
        pageIndex = int(sys.argv[1])
        c.start2(pageIndex)
        #c.getAllSubsequentPageLinks("https://scholar.google.com/scholar?oi=bibs&hl=en&cites=8312375644033733127")
        #c.createAuthorsFile("Authors.csv")
        #c.extractAuthorInfoAndWriteTofile("https://scholar.google.com/scholar?oi=bibs&hl=en&cites=5074073977992802576")
        print("finished!")
