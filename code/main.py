from urllib.request import urlopen, Request
from urllib.parse import quote
import re
import html
from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize
import edit_distance
from multiprocessing import Process, Manager

class MemeSearcher:
	
	english_common_words = ['a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
													'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
													'that', 'the', 'to', 'was', 'were', 'will', 'with']
	max_optimal_length = 15
	#from https://nlp.stanford.edu/IR-book/html/htmledition/dropping-common-terms-stop-words-1.html 
	names = None

	def recognize_person(self, query_text):
		self.preprocess(query_text)
		if not self.names:
			data_dict = self.duckduckgo(query_text)
			titles = data_dict['t']
			titles_combined = '. '.join(data_dict['t'])
			names = self.identify_person_names(titles_combined)
			print("Title names are: {}".format(list(names)))

	def identify_person_names(self, s):
		try:
			st = StanfordNERTagger('/Users/behruzcebiyev/Documents/research/meme-misattr/experiments/name-identification/STANFORD/stanford-ner-2018-10-16/classifiers/english.all.3class.distsim.crf.ser.gz')
			tags = st.tag(word_tokenize(s))
			#print(tags)
			if not tags:
				print("RESULT IS FUNNY: {}".format(result))
				return set() 
		
			found = False
			result = set()
			tmp = ""
			for tag in tags:
				if not found:
					if tag[1] == "PERSON":
						found = True
						if tag[0].isalpha():
							tmp = tag[0]
				else:
					if tag[1] == "PERSON":
						if tag[0].isalpha():
							tmp += " " + tag[0]
					else:
						if not self.is_already_there(tmp, result):
							result.add(tmp)
						tmp = ""
						found = False
		
			if tmp:
				substr_flag = False 
				if not self.is_already_there(tmp, result):
					result.add(tmp)
		
			return result
	
		except Exception as e:
			print('sth went wrong in name identification!')
			print(e)
			return set()


	def is_already_there(self, comer, inhabitants):
		inhabitants = list(inhabitants)
		flag1 = False
		for inhabitant in inhabitants:
			inhabitant = inhabitant.lower()
			flag1 = True
			for comer_item in comer.lower().split():
				if comer_item not in inhabitant:
					flag1 = False
					break
	
			if flag1:
				break

		flag2 = False
		for inhabitant in inhabitants:#inhabitants = ['Hillary Clinton', 'Obama'], comer = 'Hillary Rodham Clinton'
			inhabitant = inhabitant.lower()
			flag2 = True
			for word in inhabitant.split():
				if word not in comer.lower():
					flag2 = False
					break

			if flag2:
				break		
				
	
		return flag1 or flag2

	def extract_quote(self, text):
		text = re.sub(r'["]([^ ]*)["]', r'\1', text)#remove quotes enclosing only one word
		matches = re.findall('"([^"]*)"', text)
		if matches:
			return ' '.join(matches)
		else:
			return text

	def preprocess(self, query):
		query = re.sub(r"[^a-zA-Z0-9\"'.,]", " ", query)#Remove junk characters
		quote = self.extract_quote(query)
		if query != quote:#If quote has been successfully extracted
			s1 = self.identify_person_names(query)
			s2 = self.identify_person_names(quote)
			query = self.truncate_extra_space(query.lower())
			self.names = ' '.join(s1 - s2)
			return [self.names + ' ' + ' '.join(quote.split()[:self.max_optimal_length])]
		else:#quote cannot be extracted, so whole string is to be searched

			query = query.replace('?', '.').replace('!', '.')#Converts all stopping punctation marks to period, to be able to separate properly down the road 
			query = re.sub(r'([ ][a-zA-Z])[\.]', r'\1', query)#Remove periods after middle name not to confuse with a sentence
			self.names = ' '.join(self.identify_person_names(query))
			print('-'*50)
			print("Identified names are: {}".format(self.names))
			print('-'*50)

			query = self.truncate_extra_space(query.lower())
			sentences = [sentence for sentence in query.strip().split('. ') if len(sentence.split()) > 1]#Sentences should be more than one word, and should be separated by period-and-space 
			return [self.names + ' ' + sentence for sentence in sentences] 

	def process_search_result(self, search_result):
		'''This function simply unencode, lower search results and 
		remove punctation marks from them'''
		return html.unescape(search_result).lower()
		#return html.unescape(search_result).strip().lower().replace('\\',' ').replace(' xe2 x80 x99', '\'').replace(' x92', '\'').replace(' u2019', '\'')
		


	def download_url(self, url):
		headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
		http_request = Request(url, None, headers)
		response = urlopen(http_request)
		return str(response.read())
		

	def duckduckgo(self, query_string):
		try:
			query_strings = self.preprocess(query_string)
			data_dict = {'a':[], 'c':[], 't':[]}
			for query_string in query_strings: 
				print('-'*50)
				print("Query string is: {}".format(query_string))
				print('-'*50)
	
				search_url = 'https://duckduckgo.com/?q=' + quote(query_string) + '&t=hf&ia=web'
				response1 = self.download_url(search_url)
				url = re.findall(r"/d.js[^']*", response1)[0]
	
				response2= self.download_url("https://duckduckgo.com" + url)
				data = re.findall(r'"[a|c|t]":"[^"]*"', response2)
		
				for item in data:
					splitted_item = item.split('":"')
					key = splitted_item[0][1:]
					value = html.unescape(splitted_item[1][:-1])
					data_dict[key].append(value)
		
				print()
				print()
	
		except Exception as e:
			#data_dict = {}
			print('sth went wrong in retrieving results!')
			print(e)

		return data_dict


	def common_words(self, source, target):
		target_words = target.split()
		source_words = source.split()
		sequence_matcher = edit_distance.SequenceMatcher(source_words, target_words, action_function=edit_distance.highest_match_action)
		arr = sequence_matcher.get_opcodes()
		words_and_indices = []
		indices = []
		words = []
		for val in arr:
			if val[0] == 'equal':
				words_and_indices.append((source_words[val[1]], val[3]))
				indices.append(val[3])
				words.append(source_words[val[1]])

		if indices:
			close_indices, start_index, end_index = self.find_longest_index_sequence(indices)
			if len(close_indices) > 1:
				return [item[0] for item in words_and_indices[start_index:end_index+1]], len(close_indices), close_indices
			else:
				return [], 0, []
	
		return words, sequence_matcher.matches(), indices

	def truncate_extra_space(self, text):
		return re.sub(r"[ ]+", " ", text)

	def analyze_search_result_page(self, search_result_url, query_string, shared_dict):
		'''query_string argument here will have same words (except stop words) 
	 	as the whole text exctracted from OCR, 
		because EDITDISTANCE will handle the rest'''
		try:
			#processed_query_string = self.process_query_string(query_string)
			query_string = self.truncate_extra_space(query_string.lower())
			search_result_html = self.download_url(search_result_url)
			processed_search_result_html = self.process_search_result(search_result_html)
			matches, match_number, indices = self.common_words(query_string, processed_search_result_html) 
			match_ratio = match_number/len(query_string.split())
			contains_word_meme = False
			contains_factcheck_word = False
			if re.search(r"[^a-z]meme[^a-z]", processed_search_result_html):
				contains_word_meme = True

			if processed_search_result_html.find("fact check") != -1:
				contains_factcheck_word = True

			shared_dict[search_result_url] = ((match_ratio, matches, query_string, indices, contains_word_meme, contains_factcheck_word))#remove search_result_html
		except Exception as e:
			print(e)

	def find_longest_index_sequence(self, indices):

		start_index = 0
		end_index = len(indices) - 1
	
		while indices[end_index] - indices[start_index] > 100:
			if (indices[end_index] - indices[end_index-1]) >= (indices[start_index+1] - indices[start_index]):
				end_index -= 1
			else:
				start_index += 1

		return indices[start_index:end_index+1], start_index, end_index

	def main(self, query_string):
		search_results = self.duckduckgo(query_string)
		processes = {}
		if True in [len(item)>0 for item in search_results.values()]:#If any search result has been brought
			num_results = len(search_results['a'])
			manager_dict = Manager().dict()
			for i in range(num_results):
				if search_results['c'][i].find('.pdf') == -1: 
					processes[i] = Process(target=self.analyze_search_result_page, args=(search_results['c'][i], query_string, manager_dict))
					processes[i].start()

			for i in processes:
				process = processes[i]
				process.join(10)
				if process.exitcode is None:
					process.terminate()
		
			for item in sorted(manager_dict.items(), key = lambda pair: pair[1][0], reverse=True):
					try:
						print("{}, {}".format(item[0], str(item[1])[1:-1]))
					except Exception as e:
						print(e)
						continue

		else:
			print('No search results are retrieved!')
		


sm = MemeSearcher()
temp = input()
if re.search(r"[a-zA-Z]", temp):
	sm.recognize_person(temp)
