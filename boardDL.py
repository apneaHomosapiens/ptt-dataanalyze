from bs4 import BeautifulSoup
from time import time, sleep
from random import randint
from multiprocessing import Pool
import json
import requests
import logging
import re

def getLasttime(boardname):
	#====GET LAST TIME
	with open(f'LASTTIME_{boardname}.txt','r', encoding='utf8') as f:
		return f.readline() #LASTTIME keeps most recent article time
	#====GET LAST TIME

def getMaxPage(boardname):
	#====BELOW GET MAX page number====
	source = requests.get(f'https://www.ptt.cc/bbs/{boardname}/index.html').text
	soup = BeautifulSoup(source, 'lxml')

	paging = soup.find_all('a', class_='btn wide')

	maxPage = re.findall('\d+', paging[1]['href'])

	return int(maxPage[0])

def getBoardIndex(boardname, intPage, LASTTIME):
	'''sss'''
	#=====SOME constants here=====
	prevPage = True #==set False when reach LASTTIME
	index = intPage + 1 #==page counter as while loop goes page by page
	reachCnt = 0 #==increases when reaching LASTTIME, set prevPage to False
	thisrunLATEST = LASTTIME #==keeping the most recent article time. write to LASTTIME when this execution finishes
	lstofDictVal = []
	#=====SOME constants here=====

	#====BELOW Get Board index with history====
	while prevPage:
		root_logger.info(f'START getting article list and header info from page {index}')

		try:
			source = requests.get(f'https://www.ptt.cc/bbs/{boardname}/index{index}.html').text
			soup = BeautifulSoup(source, 'lxml')
		except Exception as e:
			root_logger.exception(f'Something wrong when getting index{index}.html. Give up for now. {e}')

		arrLink = []

		for indexArticle in soup.find_all('div', class_='r-ent'):
			try:
				artTitle = indexArticle.find('div', class_='title').a.text

				artLink = indexArticle.find('div', class_='title').a['href']

				artDate = artLink.split('.')[1]

				artAuthor = indexArticle.find('div', class_='author').text

				root_logger.info(f'RETRIEVE article header info OK {artLink}')
			except Exception as e:
				artTitle = indexArticle.find('div', class_='title').text
				artLink = None
				artDate = None
				artAuthor = None
				root_logger.exception(f'RETRIEVE article header info NOK {e}, indexArticle is {indexArticle.prettify()}')

			if artDate and int(artDate) > int(LASTTIME):

				arrLink.append(artLink) if artLink and '[公告]' not in artTitle else arrLink

				lstofDictVal.append({'artLink':artLink,'artAuthor':artAuthor,'artTitle':artTitle,'artDate':artDate,'getContent':'N'})
				prevPage = True
				thisrunLATEST = artDate if int(artDate) > int(thisrunLATEST) else thisrunLATEST

				# root_logger.info(f'artAuthor:{artAuthor}, artDate: {artDate}, prevPage: {prevPage}, thisrunLATEST: {thisrunLATEST}')
			
			elif artDate and int(artDate) < int(LASTTIME) and '[公告]' in artTitle:
				root_logger.info(f'This is announcement, pass')
				prevPage = True
			
			elif artDate and int(artDate) < int(LASTTIME):
				reachCnt = reachCnt+1
				root_logger.info(f'Saved already, skip.')

		if reachCnt > 0:
			prevPage = False

		root_logger.info(f'FINISH getting article list from page {index}')
		root_logger.info(f'{arrLink} and article count = {len(arrLink)}')
		index = index - 1
		sleep(randint(1,4))

	#====STOP going further when prevPage is False
	#====dump all header dictionary to json
	with open(f'runtimeresult_{boardname}.json','w', encoding='utf8') as f:
		json.dump(dict(items=lstofDictVal), f, ensure_ascii=False)
	#====update LASTTIME with thisrunLATEST
	with open(f'LASTTIME_{boardname}.txt','w', encoding='utf8') as f:
		f.write(thisrunLATEST)
	#====ABOVE Get Board index with history====

def getArticleMP(link):
#	for link in runtimejson['items']:

	root_logger.info(f'''START getting article {link['artLink']}''')

	try:
		source = requests.get(f'''https://www.ptt.cc{link['artLink']}''').text
		soup = BeautifulSoup(source, 'lxml')
		artBody = soup.find('div', class_='bbs-screen bbs-content')

	except Exception as e:
		root_logger.exception(f'''Something wrong when getting {link['artLink']}. Give up for now. {e}. artBody is {artBody.prettify()}''')
	else:
		#===ugly solution to work around http 5xx response, retry
		if artBody is None:
			root_logger.debug(f'http returns other than 200. lets retry')
			for i in range(3,0,-1):
				if artBody is not None:
					root_logger.info(f'retried {i-1} then good to continue')
					break
				else:
					root_logger.info(f'retry number {i}')
					sleep(10)
					source = requests.get(f'''https://www.ptt.cc{link['artLink']}''').text
					soup = BeautifulSoup(source, 'lxml')
					artBody = soup.find('div', class_='bbs-screen bbs-content')
		#===ugly solution to work around http 5xx response, retry

		# root_logger.info(f'''article find body OK of article {link['artLink']}''')

		arrBodyLink = []

		for artBodyLink in artBody.find_all('a'):

			arrBodyLink.append(artBodyLink['href'])

		# root_logger.info(f'''article insideURL OK of article {link['artLink']}''')

		arrCmt = []

		for artCmt in artBody.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['push']):

			try:
				cmtTag = artCmt.find('span', {'class':'push-tag'}).text
				cmtUID = artCmt.find('span', {'class':'push-userid'}).text
				cmtContent = artCmt.find('span', {'class':'push-content'}).text
			except Exception as e:
				cmtTag = None
				cmtUID = None
				cmtContent = None
				root_logger.exception(f'RETRIEVE article comment info NOK.{e}. artCmt is {artCmt.prettify()}')

			arrCmt.append([cmtTag,cmtUID,cmtContent])

		bodyData = {
			'artBody': artBody.text,
			'artBodyLink': arrBodyLink,
			'artCmt': arrCmt
		}
		# root_logger.info(f'''article cmt OK of article {link['artLink']}''')
		link.update(bodyData)

		root_logger.info(f'''FINISH getting article {link['artLink']}''')

		sleep(randint(3,6))
#====ABOVE Get Content====

def getBoardContent(boardname):
	'''ggg'''
	#====BELOW Get Content====
	with open(f'runtimeresult_{boardname}.json','r', encoding='utf8') as f:
		runtimejson = json.load(f)

	#===== get article with MP
	p = Pool(processes=4)
	result = p.map(getArticleMP, runtimejson['items'])
	p.close()
	p.join()
	#===== get article with MP

	root_logger.info(f'START dumping runtime content into runtimeresult_{boardname}.json')
	with open(f'runtimeresult_{boardname}.json', 'w', encoding='utf8') as f:
		json.dump(runtimejson, f, ensure_ascii=False)
	root_logger.info(f'FINISH dumping runtime content into runtimeresult_{boardname}json')

def mergeResult(boardname):
	'''eee'''
	root_logger.info(f'START merging runtime with history')

	root_logger.info(f'OPEN history result_{boardname}.json')
	with open(f'result_{boardname}.json','r', encoding='utf8') as f:
		history = json.load(f)
	root_logger.info(f'''history has count: {len(history['items'])}''')

	root_logger.info(f'OPEN runtime runtimeresult_{boardname}.json')
	with open(f'runtimeresult_{boardname}.json','r', encoding='utf8') as f:
		runtime = json.load(f)
	root_logger.info(f'''runtime has count: {len(runtime['items'])}''')

	root_logger.info(f'APPEND new runtime into history')
	for new in runtime['items']:
		history['items'].append(new)

	root_logger.info(f'''after append history has count: {len(history['items'])}''')

	root_logger.info(f'START dumping new content into result_{boardname}.json')
	with open(f'result_{boardname}.json', 'w', encoding='utf8') as f:
		json.dump(history, f, ensure_ascii=False)
	root_logger.info(f'FINISH dumping new content into result_{boardname}.json')

def foo():	
	#====BOARDNAME LIST
	lstBoardName = ['Stock','WomenTalk','AllTogether','Boy-Girl','marriage']
	# 'AllTogether','Boy-Girl','WomenTalk','marriage'
	#====BOARDNAME LIST

	# for each board in lstBoardName:
	# 	1) get LASTTIME
	# 	2) get MAX page
	# 	3) get board index, save to runtimeresult.json
	# 	4) open runtimeresult.json, get content of those link
	#	5) merge runtime reuslt with history

	for bname in lstBoardName:
		# 	1) get LASTTIME
		LASTTIME = getLasttime(bname)
		root_logger.info(LASTTIME)

		# 	2) get MAX page
		intPage = getMaxPage(bname)

		# 	3) get board index, save to runtimeresult.json
		getBoardIndex(bname, intPage, LASTTIME)
		
		#=== Timing, see the improvement of multiprocessing
		# 	4) open runtimeresult.json, get content of those link
		s_time = time()
		getBoardContent(bname)
		e_time = time() - s_time
		root_logger.info(f'Took {e_time} to get {bname}')
		#=== Timing, see the improvement of multiprocessing

		#	5) merge runtime reuslt with history
		mergeResult(bname)

if __name__ == "__main__":
	#====SETUP LOGGER
	root_logger = logging.getLogger(__name__)
	root_logger.setLevel(logging.DEBUG)
	handler = logging.FileHandler('runtime.log', mode='a', encoding='utf-8')
	formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
	handler.setFormatter(formatter)
	root_logger.addHandler(handler)
	#====SETUP LOGGER
	foo()