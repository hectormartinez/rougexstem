# -*- coding: utf-8 -*-
import re, cPickle, os, sys, gzip
from nltk.corpus import stopwords
import codecs

def notEnoughLower(s):
#	print "SENT", s
	count=0.0
	for c in s:
		if c.islower() or c==' ':
			count+=1.0
	#print count/float(len(s))
	if count/float(len(s))<0.8:
		return True
	return False

def removeParenthIndices(s):
	indices=[]
	openp=0
	closed=True
	for i in xrange(len(s)):
		if s[i]=='(':
			openp=i
			closed=False
		elif s[i]==')':
			indices.append((openp,i))
			closed=True
	if not closed:
		indices.append((openp,len(s)-1))
	if len(indices)==0:
		return s
	line=''
	for pair in indices:
		line=line+s[:pair[0]]+s[pair[1]+1:]
	return line
#	return indices

def save_pickle(data, path):
	o = gzip.open(path, 'wb')
	cPickle.dump(data, o)
	o.close()

def load_pickle(path):
	i = gzip.open(path, 'rb')
	data = cPickle.load(i)
	i.close()
	return data

def flushFile(fh):
   """
   flush file handle fh contents -- force write
   """
   fh.flush()
   os.fsync(fh.fileno())

def fix_unicode(text):
	return unicodedata.normalize('NFKD', text).encode('ascii','ignore')

def die(msg):
	print '\nERROR: %s' %msg
	sys.exit()
	
def remove_tags(text):
	"""
	remove html style tags from some text
	"""
	cleaned = re.sub('<[^>]+>', '', text)
	return re.sub('\s+',' ', cleaned).strip()

def remove_punct(sent):
	"""
	remove any character that is not in [a-z], [A-Z], [0-9], -, or a space
	also strips leading and trailing spaces
	"""
	return re.sub(r'[^a-zA-Z0-9- ]', '', sent).strip()

def is_punct(text):
	"""
	returns true if the text consists solely of non alpha-numeric characters
	"""
	for letter in text.lower():
		if letter in set('abcdefghijklmnopqrstuvwxyz1234567890'): return False
	return True

stopwords = 'au aux avec ce ces dans de des du elle en et eux il je la le leur lui ma mais me même mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous c d j l à m n s t y été étée étées étés étant étante étants étantes suis es est sommes êtes sont serai seras sera serons serez seront serais serait serions seriez seraient étais était étions étiez étaient fus fut fûmes fûtes furent sois soit soyons soyez soient fusse fusses fût fussions fussiez fussent ayant ayante ayantes ayants eu eue eues eus ai as avons avez ont aurai auras aura aurons aurez auront aurais aurait aurions auriez auraient avais avait avions aviez avaient eut eûmes eûtes eurent aie aies ait ayons ayez aient eusse eusses eût eussions eussiez eussent'.split(" ")
#stopwords = 'au aux avec ce ces dans de des du elle en et eux il je la le leur lui ma mais me mes moi mon nos notre'.split(" ")
def remove_stopwords(words):
	if type(words) == type(''):
		return ' '.join([w for w in words.split() if not w in stopwords])
	return [w for w in words if not w in stopwords]

def is_just_stopwords(words):
	if type(words) == type(''): words = words.split()
	for word in words:
		if word not in stopwords:
			return False
	return True

def get_files(path, pattern):
	"""
	Recursively find all files rooted in <path> that match the regexp <pattern>
	"""
	L = []
	
	# base case: path is just a file
	if (re.match(pattern, os.path.basename(path)) != None) and os.path.isfile(path):
		L.append(path)
		return L

	# general case
	if not os.path.isdir(path):
		return L

	contents = os.listdir(path)
	for item in contents:
		item = path + item
		if (re.search(pattern, os.path.basename(item)) != None) and os.path.isfile(item):
			L.append(item)
		elif os.path.isdir(path):
			L.extend(get_files(item + '/', pattern))

	return L

def get_ngrams(sent, n=2, bounds=False, as_string=False):
	"""
	Given a sentence (as a string or a list of words), return all ngrams
	of order n in a list of tuples [(w1, w2), (w2, w3), ... ]
	bounds=True includes <start> and <end> tags in the ngram list
	"""

	ngrams = []
	words=sent.split()
	if n==1:
		return words

	if bounds:
		words = ['<start>'] + words + ['<end>']

	N = len(words)
	for i in range(n-1, N):
		ngram = words[i-n+1:i+1]
		if as_string: ngrams.append('_'.join(ngram))
		else: ngrams.append(tuple(ngram))
	return ngrams

def get_su4(sent, as_string=False):
	words=get_ngrams(sent, 1, False, True)
	skipgrams = []

	N = len(words)
	for i in xrange(0, N):
		for j in xrange(i+1,min(i+5,N)):
			ngram = [words[i],words[j]]
			if as_string: skipgrams.append('_'.join(ngram))
			else: skipgrams.append(tuple(ngram))
	skipgrams.extend(words)
	return skipgrams

def get_ngrams_sects(sections, sent, n=2, bounds=False, as_string=False):
	"""
	Given a sentence (as a string or a list of words), return all ngrams
	of order n in a list of tuples [(w1, w2), (w2, w3), ... ]
	bounds=True includes <start> and <end> tags in the ngram list
	"""

	ngrams = []
	words=sent.split()

	if bounds:
		words = ['<start>'] + words + ['<end>']

	N = len(words)
	for i in range(n-1, N):
		ngram = words[i-n+1:i+1]
		if as_string: ngrams.append('_'.join(ngram))
		else: ngrams.append(tuple(ngram))
	sect_ngrams=[]
	for sect in sections:
		for ngram in ngrams:
			sect_ngrams.append(sect+'#'+ngram)
	return sect_ngrams

def get_deppairs(sent, as_string=False):
	"""
	"""
	if not as_string:
		return sent
	pairs=[]
	for pair in sent:
		if '_'.join(pair) not in pairs:
			pairs.append('_'.join(pair))
	return pairs

def get_skip_bigrams(sent, k=2, bounds=False):
	"""
	get bigrams with up to k words in between
	otherwise similar to get_ngrams
	duplicates removed
	"""

	sb = set()

	if type(sent) == type(''): words = sent.split()
	elif type(sent) == type([]): words = sent
	else:
		sys.stderr.write('unrecognized input type [%s]\n' %type(sent))
		return sb

	if bounds:
		words = ['<start>'] + words + ['<end>']

	N = len(words)
	width = min(k+2, N)
	for i in range(width, N+1):
		for j in range(i-width, i):
			for k in range(j+1, i):
				g = (words[j], words[k])
				sb.add(g)
	return list(sb)

import nltk
stemmer = nltk.stem.porter.PorterStemmer()
def porter_stem(word):
	return stemmer.stem(word)

def porter_stem_sent(s):
	return ' '.join([porter_stem(w) for w in s.split()])

def porter_stem_sentdep(pairs):
	for pair in pairs:
		pair[0]=porter_stem(pair[0].decode('utf8'))
		pair[1]=porter_stem(pair[1].decode('utf8'))
	return pairs

def porter_stem_psem(pairs_string):
	if len(pairs_string)==0:
		return []
	pairs=pairs_string.split('|')
	newpairs=[]
	for pair in pairs:
#		print pair
		if pair.find(',')>-1:
			pair=pair.split(',')
			temp=""
			for word in pair[1].split():
				temp=temp+'_'+porter_stem(word.decode('utf8'))
			newpairs.append((pair[0].decode('utf8'),temp[1:]))
	return newpairs

def contract_stopwords(triples_string):
	if len(triples_string.strip())==0:
		return []
	tout=""
	triples_lines=triples_string.strip().split('|')
	pairs=[]
	for line in triples_lines:
#		print "line:**",line
		t=line[line.find('(')+1:line.find(')')]
		tdata=t.split(',')
		if len(tdata)==2:
			tdata[0]=tdata[0].strip()
			tdata[1]=tdata[1].strip()
			pairs.append(tdata)
	#collapsing here
	for pair1 in pairs:
		toadd=[]
		toremove=[]
		curr_word=pair1[1][:pair1[1].find('-')]
		if curr_word in stopwords:
			for pair2 in pairs:
				if pair2[0]==pair1[1]:
					toadd.append([pair1[0], pair2[1]])
					toremove.append(pair2)
			toremove.append(pair1)
		for x in toremove:
			if x in pairs:
				pairs.remove(x)
		for x in toadd:
			pairs.append(x)
	for pair in pairs:
		pair[0]=pair[0][:pair[0].find('-')]
		pair[1]=pair[1][:pair[1].find('-')]
	return pairs

def labeled_contract_stopwords(triples_string):
	if len(triples_string.strip())==0:
		return []
	tout=""
	triples_lines=triples_string.strip().split('|')
	triples=[]
	for line in triples_lines:
		rel=line[:line.find('(')]
		t=line[line.find('(')+1:line.find(')')]
		tdata=t.split(',')
		if len(tdata)==2:
			tdata[0]=tdata[0].strip()
			tdata[1]=tdata[1].strip()
			tdata.append(rel)
			triples.append(tdata)
	#collapsing here
	for pair1 in triples:
		toadd=[]
		toremove=[]
		curr_word=pair1[1][:pair1[1].find('-')]
		if curr_word in stopwords:
			for pair2 in triples:
				if pair2[0]==pair1[1]:
					toadd.append([pair1[0], pair2[1], pair1[2]])
					toremove.append(pair2)
			toremove.append(pair1)
		for x in toremove:
			if x in triples:
				triples.remove(x)
		for x in toadd:
			triples.append(x)
	for pair in triples:
		pair[0]=pair[0][:pair[0].find('-')]
		pair[1]=pair[1][:pair[1].find('-')]
	return triples

def tokenize(text):
	#return ' '.join(nltk.tokenize.punkt.PunktWordTokenizer(text))
	return ' '.join(nltk.tokenize.wordpunct_tokenize(text))
	#return ' '.join(nltk.tokenize.punkt.punkt_word_tokenize(text))
