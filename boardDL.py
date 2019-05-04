from bs4 import BeautifulSoup
from time import sleep
from random import randint
import json
import requests
import logging
import re

# 20190504 starting Git

logging.basicConfig(filename='runtime.log', level=logging.DEBUG, 
	format='%(asctime)s:%(levelname)s:%(message)s')

#====BELOW GET MAX page number====
source = requests.get('https://www.ptt.cc/bbs/AllTogether/index.html').text
soup = BeautifulSoup(source, 'lxml')

paging = soup.find_all('a', class_='btn wide')

# print(paging[0]['href'], paging[1]['href'])

maxPage = re.findall('\d+', paging[1]['href'])

intPage = int(maxPage[0])
#====ABOVE GET MAX page number====

#====BELOW Get Board index====
for index in range(intPage+2, 500, -1):
	
	logging.info(f'START getting article list and header info from page {index}')

	try:
		source = requests.get(f'https://www.ptt.cc/bbs/AllTogether/index{index}.html').text
		soup = BeautifulSoup(source, 'lxml')
	except Exception as e:
		logging.exception(f'Something wrong when getting index{index}.html. Give up for now. {e}')

	arrLink = []

	dictAllArt = {}

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

		arrLink.append(artLink) if artLink and artLink not in ['/bbs/AllTogether/M.1276689157.A.9DD.html','/bbs/AllTogether/M.1277610443.A.944.html','/bbs/AllTogether/M.1554201298.A.FD0.html'] else arrLink

		dictAllArt[artLink] = {'artAuthor':artAuthor,'artTitle':artTitle,'artDate':artDate}
		# print(dictAllArt)
	logging.info(f'FINISH getting article list from page {index}')
	#====ABOVE Get Board index====

	#====BELOW Get Content====
	# source = requests.get('https://www.ptt.cc//bbs/AllTogether/M.1556385940.A.E80.html').text
	for artLink in arrLink:
		logging.info(f'START getting article {artLink} of page {index}')

		try:
			source = requests.get(f'https://www.ptt.cc{artLink}').text
			soup = BeautifulSoup(source, 'lxml')
		except Exception as e:
			logging.exception(f'Something wrong when getting {artLink}. Give up for now. {e}')
		else:
			artBody = soup.find('div', class_='bbs-screen bbs-content')

			dictAllArt[artLink]['artBody'] = artBody.text
			logging.info(f'article body OK of article {artLink}')

			arrBodyLink = []

			for artBodyLink in artBody.find_all('a'):
				# print(artBodyLink['href'])
				arrBodyLink.append(artBodyLink['href'])

			dictAllArt[artLink]['artBodyLink'] = arrBodyLink
			logging.info(f'article insideURL OK of article {artLink}')

			arrCmt = []

			# for artCmt in artBody.find_all('div', class_='push'):
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

			dictAllArt[artLink]['artCmt'] = arrCmt
			logging.info(f'article cmt OK of article {artLink}')

			# print('*****page breaker*****')
			logging.info(f'FINISH getting article {artLink} of page {index}')

			sleep(randint(3,6))
	#====ABOVE Get Content====

	logging.info(f'START dumping content of page {index} into JSON')
	with open(f'index{index}.json','w', encoding='utf8') as f:
		json.dump(dictAllArt, f, indent=2, ensure_ascii=False)

	logging.info(f'FINISH dumping content of page {index} into JSON')
