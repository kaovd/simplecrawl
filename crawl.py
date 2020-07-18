#!/usr/bin/python3

from bs4 import *
from bs4 import Comment
import urllib3
import re
import warnings
import sys
import uuid
import os

identif = str(uuid.uuid4()) #used for output file

## Help dialogue
def help():
	help = '''
Usage: ./crawl.py <url> <args>

-d	Enables debug output
-r(no)	Enables recursion - internal links only - Warning: As dev is lazy, this just recalls the program and iterates through all URLs - be careful - makes a lot of noise. Can be either -r1, -r2 or -r3. Notice: -r2 and -r3 are only useful if there are links to directories. If else the best option is to pick -r1, almost no use cases for -r2,-r3 unless dirs have default docs, r2/r3 not fully tested either. 
-c	Enable common checks - Robots and Sitemap added to url list but no checks on actual existence - Will not do anything without -r1
Example: ./crawl.py localhost -r1

Version: 1.0'''
	return(help)

## Test for arguments
try:
	a = sys.argv[1]
except:
	print("Error - No URL Specified")
	print(help())
	exit()

##-h passed
if sys.argv[1] == "-h":
	print(help())
	exit()


# Debug function - Check if -d is passed and skip if else
def debug(text):
	try:
		if "-d" in sys.argv:
			print("DEBUG: "+text)
	except:
		pass


#Disable Warnings
urllib3.disable_warnings()

# Get Request

http = urllib3.PoolManager()
url = sys.argv[1]
response = http.request('GET', url)
soup = BeautifulSoup(response.data, 'lxml') #Reqs lxml


# Get all URL's

debug("\n===Starting URLs===\n")

found_pages = []
for link in soup.find_all('a'):
	try:

		if "#" in link.get('href')[0]:
			continue
	except:
		debug("css ref checker error") #Gen'd as a result of using [0], need to anticipate if it exists first to not crash
		continue
	if 'mailto' in link.get('href'):
		continue # fix weird bug
	if link.get('href') in found_pages:
		debug("Duplicate found - Skipping")
		continue

	debug(link.get('href')) # Links found
	#ebug(a)
	found_pages.append(link.get('href'))

for link in soup.find_all('script'):
	if link.get('src') in found_pages:
		debug("Duplicate found - Skipping")
		continue

	debug(link.get('src')) # Links found
	found_pages.append(link.get('src'))

# Get all comments

debug("\n===Starting comments===\n")

#Comment Parse function - https://kite.com/python/examples/1719/beautifulsoup-extract-all-comments
found_comments = []

def is_comment(element): 
    return isinstance(element, Comment)

for comment in soup.find_all(text=is_comment):
	debug(comment) #Debug
	found_comments.append(comment)

#Get emails
soupstr = str(soup) #Workaround
found_emails = re.findall("([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", soupstr)

#Add robots and sitemap

url = sys.argv[1]+"/robots.txt"
response = http.request('GET', url)
soup = BeautifulSoup(response.data, 'lxml') #Reqs lxml
soupstr = str(soup)
soupstr = soupstr.strip('/p></body></html>')

url2 = sys.argv[1]+"/sitemap.xml"
response2 = http.request('GET', url2)
soup2 = BeautifulSoup(response2.data, 'lxml') #Reqs lxml
soupstr2 = str(soup2)
soupstr2 = soupstr2.strip('/p></body></html>')
#Really creative variable names

if "-c" in sys.argv:
	for url in re.findall("(\/\w.*)", soupstr):
		debug(url)
		found_pages.append(url[1:]) #Parse robots and remove leading /
	for url in re.findall("(<loc>.*<\/loc>)", soupstr2):
		debug(url)
		url = url.replace('<loc>https://', '') #Parse sitemap and fix sitemap format but lazily
		url = url.replace('<loc>http://', '')
		url = url.replace(sys.argv[1], '') # Take out hostname
		url = url.replace('</loc>', '')
		url = url[1:] #Take out leading /
		found_pages.append(url) #Finally





## Check if we have anything, else die
if found_pages == [None]: #Sometimes this happens, correct it for checking
	found_pages = []
if found_pages == [] and found_comments == [] and found_emails == []:
	print("Found nothing at "+sys.argv[1]+" - dying")
	exit()



# Output
print("=== Pages / Scripts === \n")
print(found_pages)
print("\n=== Comments ===\n")
print(found_comments)
print("\n=== Emails ===\n")
print(found_emails)



## File Writer

safeurl = sys.argv[1].replace('/','_')
writefile = safeurl+"_"+identif

file = open(writefile, "w")
file.write("Crawl Report for: "+sys.argv[1]+"\n\n")
file.write("===Pages===\n")
for page in found_pages:
	file.write(page+"\n")
file.write("===Comments===\n")
for comment in found_comments:
	file.write(comment+"\n")
file.write("===Emails===\n")
for email in found_emails:
	file.write(email+"\n")
file.close()

print("\nSaved to " + writefile)


# Horrible recurse system


if "-r1" in sys.argv:
	base = sys.argv[1]
	for url in found_pages:
		urlfin = base+"/"+url
		os.system("./crawl.py "+urlfin)

if "-r2" in sys.argv:
	base = sys.argv[1]
	for url in found_pages:
		urlfin=base+"/"+url
		debug(urlfin[-4:-3])#.php/3 letters
		debug(urlfin[-3:-2])#.js
		if urlfin[-4:-3] == ".": #Extremely lazy ext detection
			debug("Error - Recursing more than once and not a dir")
			continue
		if urlfin[-3:-2] == ".": #Fix for .js
			debug("Error - Recursing more than once and not a dir")
			continue

		os.system("./crawl.py "+urlfin+" -r1")
	print("If nothing returned, no dirs where present and not crawled, run with -r1 instead")

if "-r3" in sys.argv:
	base = sys.argv[1]
	for url in found_pages:
		urlfin=base+"/"+url
		debug(urlfin[-4:-3])
		debug(urlfin[-3:-2])
		if urlfin[-4:-3] == ".": #Again, lazy ext detection
                        debug("Error - Recursing more than once and not a dir")
                        continue

		if urlfin[-3:-2] == ".": #Fix for .js
			debug("Error - Recursing more than once and not a dir")
			continue

		os.system("./crawl.py "+urlfin+" -r2")
	print("If nothing returned, then no dirs where present and not crawled, run with -r1 instead")


