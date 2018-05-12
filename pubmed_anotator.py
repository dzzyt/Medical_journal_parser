# -*- coding: utf-8 -*-

'''Searches pubmed central for articles/sentences containing a list of terms.
requires
list of article ids PMC numerical format .csv
list key words .csv
Exports articles broken down into sentences, and/or only sentences containing your search terms.'''

import re
'''regular expression'''
import ast, json, copy
import string
import requests
'''http access, api access'''
from collections import defaultdict
from bs4 import BeautifulSoup
''' beautiful soup xml html scraper must be imported from bs4 like this'''
import bs4
import pandas as pd
'''saving and loading csv and other data array tools'''
from stanfordcorenlp import StanfordCoreNLP
############################################################################
'''Load lists/dictionaries'''

'''
Dictionary of Keys terms to target your parse
'''
filename = '.csv'
keys_dict = defaultdict()
df = pd.read_csv(filename)
'''panda csv reading tool'''

'''
Load keys list in panda
'''
for index, row in df.iterrows():
	'''
	first item in keys as root
	'''
	root_term = ' ' + str(row.iat[0]) + ' '
	''' spaces before and after term'''
	for item in row.iteritems():
		'''
		if any item in row found add to root term list
		'''
		if item[1]:
			keys_dict[' ' + str(item[1])+ ' '] = root_term

'''
List of Articles to be Parsed
'''
filename = 'ids_spreadsheet.csv'
#pmc ids
df = pd.read_csv(filename)
id_list = []
for index, row in df.iterrows():
	if index ==0:
		break
	id_list.append(row.iat[0][3:])
#print(id_list)
#########################################################################
'''
Helper Functions
'''
regex = re.compile('[%s]' % re.escape(string.punctuation))
'''identifies if inputString conatins any of the terms loaded in dictionary,
returns a set () of terms from the dictionary found in inputString'''
def has_key(inputString, dictionary):
	result = set()
	for k in dictionary.keys():
		if k.lower() in regex.sub(' ', inputString.lower()):
			try:
				result.add(dictionary[k])
			except Exception:
				result.add(k)
	return result
###########################################################################3
'''stanfordnlp'''
nlp = StanfordCoreNLP(r'location\stanford-corenlp-full-2018-02-27')#, logging_level=logging.DEBUG)
#props={'annotators': 'tokenize,ssplit,pos','pipelineLanguage':'en','outputFormat':'text'}
#requires Lynten Stanford-core NLP See Modified Lynten GIT
##############################################################################3
'''CSV entry'''
def create_spreadsheet_entry(
	article_id,
	token,
	index,
	tag,
	dep
	):
#enters data into csv row format
	result = [[
		article_id,
		token,
		index,
		tag,
		dep
		]]
	return pd.DataFrame(result, columns=list(columns))

def put_values_in_spreadsheet(entry_list, data_frame):
#takes in list of items to be entered as a row in the output CSV/TSV
	data_frame = data_frame.append(
		create_spreadsheet_entry( 
		entry_list[0], 
		entry_list[1],
		entry_list[2],
		entry_list[3],
		entry_list[4]
		),ignore_index=True)
	return data_frame
######################################################################
'''main function'''
data = ''
URL = 'https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:{article_id}&metadataPrefix=pmc'
REPORT_URL = 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{article_id}/'
columns = [
	'Article',
	'Token',
	'index',
	'POS',
	'Dependency@connection'
]
#, 'Paragraph'
data_frame = pd.DataFrame(
	columns=list(columns)
)

def parse_article(article_id, data_frame):
	# Get article XML
	article_xml = requests.get(URL.format(article_id=article_id))
	# Create Soup
	soup = BeautifulSoup(article_xml.content, 'html.parser')
	'''create beautiful soup object'''
	for t in soup.find_all('table'):
		soup.table.decompose()
	for f in soup.find_all('fig'):
		soup.fig.decompose()
	for tw in soup.find_all('table-wrap'):
		soup.find('table-wrap').decompose()
	'''cleans soup'''
	for s in soup.find_all('p'):
		if has_key(str(s),keys_dict):
			parsed = nlp.stnlp(''.join(s.findAll(text=True) ))
			for dic in parsed['sentences']:
				tokes = ''
				pos = ''
				dep = {}
				index = ''	
				s_dep = ''
				no_key = 0
				for item in dic['tokens']:
					tokes = ' '.join([tokes,item['word']])	
					pos = ' '.join([pos,item['pos']])	
					index = ' '.join([index,str(item['index'])])
				if not has_key(tokes,keys_dict):
					no_key +=1
				if no_key==0:
					for item in dic['enhancedPlusPlusDependencies']:
						key = item['dependent']
						value = ''.join([item['dep'],'@',str(item['governor'])])
						dep[key] = value
					for i in range(0,len(dep)):
						key = i+1
						s_dep = ' '.join([s_dep,dep[key]])
					entry = [article_id,tokes,index,pos,s_dep]	
					data_frame = put_values_in_spreadsheet(entry,data_frame)
	return data_frame
############################################################################
'''RUN '''
if __name__ == '__main__':
	tot = 1
	print('Starting')
	for article_id in id_list:
		if tot ==0:
			break
		print(article_id)
		try:
			data_frame = parse_article(article_id, data_frame)
		except Exception as e:
			print(e)
		#return data_frame
		tot -= 1			
	data_frame.to_csv('PMC_script_results.tsv',sep='\t')
nlp.close()

		
