import sys, os, os.path, tempfile, re, collections, shutil
rg = 'perl /home/alonso/tool/ROUGE-1.5.5/ROUGE_externalstemmer-1.5.5.pl'


def create_config_duc(model_dir, peer_dir, exper_dir):
	 models = [item for item in os.listdir(model_dir) if ("sum_" in item and item.endswith("sent.tok")) ]
	 print models
	 peers = os.listdir(peer_dir)
	 config_file = exper_dir+"config.xml"
	 config = open(config_file, 'w')
	 config.write('<ROUGE_EVAL version=\"1.5.5\">\n')
	 count=0
	 for peer in peers:
		peer2=peer
		if '.' in peer:
			peer2=peer[:peer.find('.')]
			if '_' in peer2:
				peer2=peer2[:peer2.find('_')]
		#print peer2
		count+=1
		config.write('<EVAL ID=\"'+str(count)+'\">\n')
		config.write('<PEER-ROOT>\n')
		config.write(peer_dir + '\n')
		config.write('</PEER-ROOT>\n')
		config.write('<MODEL-ROOT>\n')
		config.write(model_dir + '\n')
		config.write('</MODEL-ROOT>\n')
		config.write('<INPUT-FORMAT TYPE=\"SPL\">\n')
		config.write('</INPUT-FORMAT>\n')
		config.write('<PEERS>\n')
		config.write('<P ID=\"1\">%s</P>\n' %peer)
		config.write('</PEERS>\n')
		config.write('<MODELS>\n')
		modelnames=[item for item in  models if peer2 in item]
		#print modelnames
		for model in modelnames:
			config.write('<M ID=\"'+model[-6:-5]+'\">'+model+'</M>\n' )
		config.write('</MODELS>\n')
		config.write('</EVAL>\n')
	 config.write('</ROUGE_EVAL>\n')
	 config.close()
	 return config_file

def create_config(model_dir, peer_dir, exper_dir):
	 models = [item for item in os.listdir(model_dir) if (item.endswith("sent.tok")) ]
	 #print models
	 peers = os.listdir(peer_dir)
	 config_file = exper_dir+"config.xml"
	 config = open(config_file, 'w')
	 config.write('<ROUGE_EVAL version=\"1.5.5\">\n')
	 count=0
	 for peer in peers:
		peer2=peer
		if '.' in peer:
			peer2=peer[:peer.find('.')]
			if '_' in peer2:
				peer2=peer2[:peer2.find('_')]
		#print peer2
		count+=1
		config.write('<EVAL ID=\"'+str(count)+'\">\n')
		config.write('<PEER-ROOT>\n')
		config.write(peer_dir + '\n')
		config.write('</PEER-ROOT>\n')
		config.write('<MODEL-ROOT>\n')
		config.write(model_dir + '\n')
		config.write('</MODEL-ROOT>\n')
		config.write('<INPUT-FORMAT TYPE=\"SPL\">\n')
		config.write('</INPUT-FORMAT>\n')
		config.write('<PEERS>\n')
		config.write('<P ID=\"1\">%s</P>\n' %peer)
		config.write('</PEERS>\n')
		config.write('<MODELS>\n')
		modelnames=[item for item in  models if peer2 in item]
		#print modelnames
		for model in modelnames:
			config.write('<M ID=\"'+model[-6:-5]+'\">'+model+'</M>\n' )
		config.write('</MODELS>\n')
		config.write('</EVAL>\n')
	 config.write('</ROUGE_EVAL>\n')
	 config.close()
	 return config_file
	 
def run_rouge_bytes(config_file, length, outputdir):
	print "evaluating...", config_file, outputdir+"score.txt"
	rg='perl /home/natschluter/eval_software/ROUGE-1.5.5/ROUGE-1.5.5.pl'

	os.system(rg+"  -e /home/alonso/tool/ROUGE-1.5.5/data -n 4 -2 4 -u -m -x -c 95 -r 1000 -f A -t 0 -b 665 -a "+config_file+" > "+outputdir+"_score.txt" )
	
def run_rouge(config_file, length, outputdir):
	print "evaluating...", config_file, outputdir+"score.txt"

	os.system(rg+"  -e /home/alonso/tool/ROUGE-1.5.5/data -n 4 -2 4 -u -m -x -c 95 -r 1000 -f A -t 0 -l "+length+" -a "+config_file+" > "+outputdir+"_score.txt" )
	
def evaluate_length():
	print len(sys.argv)
	if len(sys.argv) < 7 or len(sys.argv) > 7:
		sys.stderr.write('USAGE: %s <sys_prefix1> <peer_dir2> <length3> <scorefoldername4> <modelfiles5> <dtype6>\n' %sys.argv[0])
		sys.exit(1)
	
	modelfiles=sys.argv[5]

	if sys.argv[6]=='duc04':
		config_file = create_config_duc(modelfiles, sys.argv[2], sys.argv[4]+"/"+sys.argv[1]+"_")
	else:
		config_file = create_config(modelfiles, sys.argv[2], sys.argv[4]+"/"+sys.argv[1]+"_")
	run_rouge(config_file, sys.argv[3], sys.argv[4]+"/"+sys.argv[1]+"_")	

def evaluate_bytes():
	print len(sys.argv)
	if len(sys.argv) < 7 or len(sys.argv) > 7:
		sys.stderr.write('USAGE: %s <sys_prefix1> <peer_dir2> <length3> <scorefoldername4> <modelfiles5> <dtype6>\n' %sys.argv[0])
		sys.exit(1)
	
	modelfiles=sys.argv[5]

	if sys.argv[6]=='duc04':
		config_file = create_config_duc(modelfiles, sys.argv[2], sys.argv[4]+"/"+sys.argv[1]+"_")
	else:
		config_file = create_config(modelfiles, sys.argv[2], sys.argv[4]+"/"+sys.argv[1]+"_")
	run_rouge_bytes(config_file, sys.argv[3], sys.argv[4]+"/"+sys.argv[1]+"_")	

		
if __name__ == '__main__':
#	evaluate_duc_bytes_Chance()
	evaluate_length()
