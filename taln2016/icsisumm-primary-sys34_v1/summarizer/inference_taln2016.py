import sys, os, util, re, collections, shutil, math
import prob_util, decoder2, decoder_localsolver

class Sentence:
	def __init__(self, bytes, id, order, orig, doc, tok=None, par=None, unresolved=False, lang='en'):
		self.id = id
		self.order = order
		self.orig = orig
		self.tok = tok
		if lang=='en':
			self.tok2 = util.porter_stem_sent(util.tokenize(fix_text(self.orig)))
		elif lang=='fr':
			#FOR HECTOR (you will do something in the util.py file for this)
			print 'This part is for you, Hector...'
			sys.exit(0)
		else:
			print 'Unsupported language...'
			sys.exit(0)
#		print "TOK2", len(self.tok2)
		self.doc = doc
		self.new_par = (par == '1')
		if bytes >- 1:
			self.length = len(self.orig) #for bytes
		else:
			self.length = len(self.orig.split())
		self.unresolved = unresolved
#		print self.orig

	def __str__(self):
		return self.orig

def load_sents(bytes, filename): 
	if not filename.endswith('sent.tok'):
		filename=filename+'.sent.tok'
	print filename
	orig_fh = open(filename)
	tok_fh = open(filename)
	length = len(tok_fh.read().replace('\n', ' ').split())
	tok_fh.seek(0,0)
	doc_fh = open(filename) #changed to .par from .doc for echr documents
	par_fh = open(filename)
	
	sents = []
	count = 0
	order = 0
	prev_doc = ''
	while True:
		[doc, orig, tok, parse, par] = map(str.strip, [doc_fh.readline(), orig_fh.readline(), tok_fh.readline(), "", par_fh.readline()])

		if not (doc or orig or tok): break
		if doc != prev_doc: order = 0
		sents.append(Sentence(bytes, count, order, orig, doc, tok, par))
		count += 1
		order += 1
		prev_doc = doc

	sys.stderr.write('topic [%s]: got [%d] sentences\n' %(id, count))
	return (length, sents)


def fix_text(text):
	"""
	prepare text for ngram concept extraction
	"""
	t = text
	t = util.remove_punct(t)
	t = re.sub('\s+', ' ', t)
	return t.lower()

def create_ilp_output(sents, concepts, path):
	## output concepts in each sentence and lengths
#	print "create ilp output", len(sents), len(concepts), path
	sentence_concepts_file = path + '.sent.tok.concepts'
	length_file = path + '.sent.tok.lengths'
	orig_file = path + '.sent.tok.orig'
	sent_fh = open(sentence_concepts_file, 'w')
	length_fh = open(length_file, 'w')
	orig_fh = open(orig_file, 'w')
	for sent in sents:
		sent_fh.write(' '.join(list(sent.concepts)) + '\n')
		length_fh.write('%d\n' %sent.length)
		orig_fh.write('%s\n' %sent.orig)
	length_fh.close()
	sent_fh.close()
	orig_fh.close()
	
	## output concept weights, now with reference counts beside
	concept_weights_file = path + '.concepts'
	concept_fh = open(concept_weights_file, 'w')
	for concept, value in concepts.items():
		concept_fh.write('%s %1.7f\n' %(concept.encode('utf8'), value))
	concept_fh.close()
		
	return sentence_concepts_file, concept_weights_file, length_file, orig_file

def make_concepts(id, path, sents, R1=True, R2=False, R4=False, SU4=False):
	all_concepts = collections.defaultdict(int)
	
	print "******************make_concepts", id
	for sent in sents:
		## store this sentence's concepts
		sent.concepts = set()
		if R1:
			concepts = set(util.get_ngrams(sent.tok2, 1, bounds=False, as_string=True))
		elif R2:
			concepts = set(util.get_ngrams(sent.tok2, 2, bounds=False, as_string=True))
		elif R4:
			concepts = set(util.get_ngrams(sent.tok2, 4, bounds=False, as_string=True))
		elif SU4:
			concepts = set(util.get_su4(sent.tok2, as_string=True))

		for concept in concepts:
			all_concepts[concept]+=1
		sent.concepts = concepts
	return create_ilp_output(sents, all_concepts, path+id)

def get_topic_ids(path): #just returns file names as ids
	ids=None
	ids = map(str.strip, os.popen('ls %s*.sent.tok' %path).readlines()) #HECTOR, HERE ARE THE FILE EXTENSIONS HARD CODED
	ids = [f.split('.')[0] for f in map(os.path.basename, ids)]
	return ids

def make_summary(data_path, docfilename, out_path, summ_path, length, options):
	index=docfilename.find('_')+1
	id=docfilename[index:]
	(ln, sents) = load_sents(options.bytes, data_path+docfilename)
	if True:
		sentence_concepts_file, concept_weights_file, length_file, orig_file= make_concepts(id, out_path[:out_path.rfind('/')+1], sents, options.unigrams, options.bigrams, options.fourgrams, options.su4)
		
		summ_sent_nums = decoder2.decode_simple(length, length_file, sentence_concepts_file, concept_weights_file, options.timelimit)
		
		summary = [sents[i] for i in summ_sent_nums]

		## order sentences
#		summary = order(summary)
	summary_fh = open(summ_path + id, 'w')
	print "WRITING TO :", summ_path+id
	for sent in summary:
		summary_fh.write('%s\n' %sent)

from optparse import OptionParser
def get_options(parser=None):
	usage = 'usage: %prog [options]'
	if parser == None:
		parser = OptionParser(usage=usage)
		
	parser.add_option('--lang', dest='lang', type='str', help='either en or fr')

	parser.add_option('-t', '--task', dest='task', type='str', help='tasks: duc04, echr, wiki')
	parser.add_option('--manpath', dest='manpath', type='str', help='manual summary path')
	parser.add_option('-l', '--length', dest='length', help='maximum number of words in output summaries', type='float', default=-1)
	parser.add_option('-b', '--bytes', dest='bytes', help='maximum number of bytes in output summaries', type='float', default=-1)
	parser.add_option('-i', '--input-path', dest='inputpath', type='str', help='path of input files')
	parser.add_option('-o', '--output-path', dest='outpath', type='str', help='path to store output')
	parser.add_option('--decoder', dest='decoder', type='str', default="glpsolve", help='ILP decoder (glpsolve or localsolver)')
	parser.add_option('--oldconcepts', dest='oldconcepts', type='str', default="", help='do not generate new concepts, use the ones already in the directory')
	parser.add_option('--timelimit' ,dest='timelimit', type='float', help='timelimit', default=100)
	parser.add_option('--fourgrams', dest='fourgrams', action="store_true", default=False, help='optimising w.r.t. R4')
	parser.add_option('--su4', dest='su4', action="store_true", default=False, help='optimising w.r.t. SU4')
	parser.add_option('--bigrams', dest='bigrams', action="store_true", default=False, help='optimising w.r.t. R2')
	parser.add_option('--unigrams', dest='unigrams', action="store_true", default=False, help='optimising w.r.t. R1')
	
	(options, args)=parser.parse_args()
	if options.length*options.bytes>0:
		print 'Must choose either length or bytes budget but not both'
		sys.exit(0)
	return (options,args)
	
if __name__ == '__main__':
	
	(options, args) = get_options()
	
	## get doc ids to match with summaries
	ids = get_topic_ids(options.inputpath) # list of filenames (basenames)

	os.popen('mkdir -p %s' %options.outpath + 'summary/')
	for id in ids:
		make_summary(options.inputpath, id, options.outpath, options.outpath + 'summary/', max(options.length,options.bytes), options)
		
