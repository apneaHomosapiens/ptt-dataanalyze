from bs4 import BeautifulSoup
from time import sleep
from random import randint
import json
import requests
import logging
import re

logging.basicConfig(filename='runtime.log', level=logging.DEBUG, 
	format='%(asctime)s:%(levelname)s:%(message)s')

#====LAST TIME
with open(f'LASTTIME.txt','r', encoding='utf8') as f:
	LASTTIME = f.readline() #LASTTIME keeps most recent article time
	logging.info(LASTTIME)

#====BELOW GET MAX page number====
source = requests.get('https://www.ptt.cc/bbs/AllTogether/index.html').text
soup = BeautifulSoup(source, 'lxml')

paging = soup.find_all('a', class_='btn wide')

# print(paging[0]['href'], paging[1]['href'])

maxPage = re.findall('\d+', paging[1]['href'])

intPage = int(maxPage[0])
#====ABOVE GET MAX page number====

#=====SOME constants here=====
# logging.info(f'max page is: {intPage}')
prevPage = True #==set False when reach LASTTIME
index = intPage + 1 #==page counter as while loop goes page by page
reachCnt = 0 #==increases when reaching LASTTIME, set prevPage to False
thisrunLATEST = LASTTIME #==keeping the most recent article time. write to LASTTIME when this execution finishes
lstofDictVal = []
# logging.info(f'SET prevPage = TRUE')
#=====SOME constants here=====

#====BELOW Get Board index with history====
# for index in range(intPage+2, 500, -1):
while prevPage:
	logging.info(f'START getting article list and header info from page {index}')

	try:
		source = requests.get(f'https://www.ptt.cc/bbs/AllTogether/index{index}.html').text
		soup = BeautifulSoup(source, 'lxml')
	except Exception as e:
		logging.exception(f'Something wrong when getting index{index}.html. Give up for now. {e}')

	arrLink = []

	for indexArticle in soup.find_all('div', class_='r-ent'):
		try:
			artTitle = indexArticle.find('div', class_='title').a.text

			artLink = indexArticle.find('div', class_='title').a['href']
			# artfLink = f'https://www.ptt.cc{artLink}'
			artDate = artLink.split('.')[1]

			artAuthor = indexArticle.find('div', class_='author').text

			logging.info(f'RETRIEVE article header info OK {artLink}')
		except Exception as e:
			artTitle = indexArticle.find('div', class_='title').text
			artLink = None
			artDate = None
			artAuthor = None
			logging.exception(f'RETRIEVE article header info NOK {e}, indexArticle is {indexArticle.prettify()}')

		if artDate and int(artDate) > int(LASTTIME):

			arrLink.append(artLink) if artLink and '[公告]' not in artTitle else arrLink

			lstofDictVal.append({'artLink':artLink,'artAuthor':artAuthor,'artTitle':artTitle,'artDate':artDate,'getContent':'N'})
			prevPage = True
			thisrunLATEST = artDate if int(artDate) > int(thisrunLATEST) else thisrunLATEST

			logging.info(f'artAuthor:{artAuthor}, artDate: {artDate}, prevPage: {prevPage}, thisrunLATEST: {thisrunLATEST}')
		
		elif artDate and int(artDate) < int(LASTTIME) and '[公告]' in artTitle:
			logging.info(f'This is announcement, pass')
			prevPage = True
		
		elif artDate and int(artDate) < int(LASTTIME):
			reachCnt = reachCnt+1
			logging.info(f'else clause reachCnt: {reachCnt}')

	if reachCnt > 0:
		prevPage = False

	logging.info(f'FINISH getting article list from page {index}')
	logging.info(f'{arrLink} and article count = {len(arrLink)}')
	index = index - 1
	sleep(randint(1,4))

#====STOP going further when prevPage is False

#====dump all header dictionary to json
with open(f'runtimeresult.json','w', encoding='utf8') as f:
	json.dump(dict(items=lstofDictVal), f, ensure_ascii=False)
#====update LASTTIME with thisrunLATEST
with open(f'LASTTIME.txt','w', encoding='utf8') as f:
	f.write(thisrunLATEST)
#====ABOVE Get Board index with history====
#====BELOW Get Content====
with open(f'runtimeresult.json') as f:
	runtimejson = json.load(f)

for artData in runtimejson['items']:
	# print(artData['artLink'])
	logging.info(f'''START getting article {artData['artLink']}''')

	try:
		source = requests.get(f'''https://www.ptt.cc{artData['artLink']}''').text
		soup = BeautifulSoup(source, 'lxml')
		artBody = soup.find('div', class_='bbs-screen bbs-content')

	except Exception as e:
		logging.exception(f'''Something wrong when getting {artData['artLink']}. Give up for now. {e}. artBody is {artBody.prettify()}''')
	else:
		#===ugly solution to work around http 5xx response, retry
		if artBody is None:
			logging.debug(f'http returns other than 200. lets retry')
			for i in range(3,0,-1):
				if artBody is not None:
					logging.info(f'retried {i-1} then good to continue')
					break
				else:
					logging.info(f'retry number {i}')
					sleep(10)
					source = requests.get(f'''https://www.ptt.cc{artData['artLink']}''').text
					soup = BeautifulSoup(source, 'lxml')
					artBody = soup.find('div', class_='bbs-screen bbs-content')
		#===ugly solution to work around http 5xx response, retry

		logging.info(f'''article find body OK of article {artData['artLink']}''')

		arrBodyLink = []

		for artBodyLink in artBody.find_all('a'):
			# print(artBodyLink['href'])
			arrBodyLink.append(artBodyLink['href'])

		logging.info(f'''article insideURL OK of article {artData['artLink']}''')

		arrCmt = []

		for artCmt in artBody.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['push']):
			# print(artCmt.prettify())
			try:
				cmtTag = artCmt.find('span', {'class':'push-tag'}).text
				cmtUID = artCmt.find('span', {'class':'push-userid'}).text
				cmtContent = artCmt.find('span', {'class':'push-content'}).text
			except Exception as e:
				cmtTag = None
				cmtUID = None
				cmtContent = None
				logging.exception(f'RETRIEVE article comment info NOK.{e}. artCmt is {artCmt.prettify()}')

			arrCmt.append([cmtTag,cmtUID,cmtContent])

		bodyData = {
			'artBody': artBody.text,
			'artBodyLink': arrBodyLink,
			'artCmt': arrCmt
		}
		logging.info(f'''article cmt OK of article {artData['artLink']}''')
		artData.update(bodyData)
		# print('*****page breaker*****')
		logging.info(f'''FINISH getting article {artData['artLink']}''')

		sleep(randint(1,4))
#====ABOVE Get Content====

logging.info(f'START dumping runtime content into runtimeresult.json')
with open(f'runtimeresult.json', 'w', encoding='utf8') as f:
	json.dump(runtimejson, f, ensure_ascii=False)

logging.info(f'FINISH dumping runtime content into runtimeresult.json')

logging.info(f'START merging runtime with history')

logging.info(f'OPEN history result.json')
with open('result.json') as f:
	history = json.load(f)
logging.info(f'''history has count: {len(history['items'])}''')

logging.info(f'OPEN runtime runtimeresult.json')
with open('runtimeresult.json') as f:
	runtime = json.load(f)
logging.info(f'''runtime has count: {len(runtime['items'])}''')

logging.info(f'APPEND new runtime into history')
for new in runtime['items']:
	# logging.info(new)
	history['items'].append(new)

logging.info(f'''after append history has count: {len(history['items'])}''')

logging.info(f'START dumping new content into result.json')
with open('result.json', 'w', encoding='utf8') as f:
	json.dump(history, f, ensure_ascii=False)
logging.info(f'FINISH dumping new content into result.json')