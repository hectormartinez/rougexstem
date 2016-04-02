# -*- coding: utf-8 -*-
import sys, os, collections
import ilp, ilp_to_localsolver, ilp_notimelimit

def decode(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, sentence_group_file=None, dependency_file=None, atleast=None, command="glpsol"):
	solver = ilp.IntegerLinearProgram(debug=1, tmp = "tmp_decoder.%d.%s.%s" % (os.getpid(), os.environ["USER"], os.environ["HOSTNAME"]), command=command)
	#solver = ilp_to_localsolver.IntegerLinearProgram(debug=1, tmp = concept_weight_file, time_limit=1)
	concept_id = {}
	concept = 0
	concept_weights = {}
	for line in open(concept_weight_file):
		tokens = line.strip().split()
		weight = float(tokens[1])
		if tokens[0] in concept_id:
			sys.stderr.write('ERROR: duplicate concept \"%s\", line %d in %s\n' % (tokens[0], concept + 1, concept_weight_file))
			sys.exit(1)
		concept_id[tokens[0]] = concept
		concept_weights[concept] = weight
		concept += 1

	index = {}
	sentence_concepts = {}
	sentence = 0
	for line in open(concepts_in_sentence_file):
		tokens = line.strip().split()
		concepts = {}
		for token in tokens:
			concepts[token] = True
		mapped_concepts = {}
		for concept in concepts:
			if concept not in concept_id:
				sys.stderr.write('ERROR: not weight for concept \"%s\", line %d in %s\n' % (concept, sentence + 1, concepts_in_sentence_file))
				sys.exit(1)
			id = concept_id[concept]
			if id not in index: index[id] = []
			index[id].append(sentence)
			mapped_concepts[id] = True
		if len(mapped_concepts) > 0:
			sentence_concepts[sentence] = mapped_concepts
		sentence += 1

	# build objective
	objective = []
	for concept, weight in concept_weights.items():
		if concept not in index: continue # skip unused concepts
		objective.append("%+g c%d" % (weight, concept))
		solver.binary["c%d" % concept] = concept
	solver.objective["score"] = " ".join(objective)

	# sentence => concepts
	for sentence, concepts in sentence_concepts.items():
		solver.binary["s%d" % sentence] = sentence
	#	for concept in concepts:
	#		solver.constraints["sent_%d" % len(solver.constraints)] = "s%d - c%d <= 0" % (sentence, concept)

	# concept => sentence
	for concept in index:
		solver.constraints["index_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in index[concept]]) + " - c%d >= 0" % concept

	if sentence_group_file != None:
		groups = {}
		sentence = 0
		for line in open(sentence_group_file):
			if sentence in sentence_concepts:
				if line != '\n':
					if line not in groups:
						groups[line] = []
					groups[line].append(sentence)
			sentence += 1
		for group in groups:
			solver.constraints["group_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in groups[group]]) + " <= 1"

	if dependency_file != None:
		groups = {}
		sentence = 0
		for line in open(dependency_file):
			if sentence in sentence_concepts:
				if line != '\n':
					for id in line.strip().split():
						id = int(id)
						if "s%d" % id not in solver.binary:
							solver.constraints["depend_%d" % len(solver.constraints)] = "s%d = 0" % (sentence)
						else:
							solver.constraints["depend_%d" % len(solver.constraints)] = "s%d - s%d >= 0" % (id, sentence)
			sentence += 1

	length_constraint = []
	sentence = 0
	for line in open(sentence_length_file):
		if sentence in sentence_concepts:
			length = line.strip()
			length_constraint.append("%s s%d" % (length, sentence))
			solver.objective["score"] += " - %g s%d" % (float(length) / 1000.0, sentence)
		sentence += 1

	solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)

	if atleast != None:
		at_least = []
		sentence = 0
		for line in open(atleast):
			line = line.strip()
			if sentence in sentence_concepts:
				if line == "1":
					at_least.append("s%d" % sentence)
			sentence += 1
		if len(at_least) > 0:
			solver.constraints["at_least_%d" % len(solver.constraints)] = " + ".join(at_least) + " >= 1" # select at least one of those

	sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts), len(index)))

	if len(sentence_concepts) > 0 and len(index) > 0:
		solver.run()
	output = []
	for variable in solver.output:
		if variable.startswith("s") and solver.output[variable] == 1:
			output.append(int(variable[1:]))
	return output

def decodelaw(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, depconcepts_in_sentence_file, depconcept_weight_file, depconcepts_weight, sentence_group_file=None, dependency_file=None, atleast=None, command="glpsol"):
	solver = ilp.IntegerLinearProgram(debug=1, tmp = "tmp_decoder.%d.%s.%s" % (os.getpid(), os.environ["USER"], os.environ["HOSTNAME"]), command=command)
	print "weight: ", depconcepts_weight
	alpha=1-float(depconcepts_weight)
	beta=float(depconcepts_weight)
	concept_id = {}
	concept = 0
	concept_weights = {}
	for line in open(concept_weight_file):
		tokens = line.strip().split()
		weight = float(tokens[1])
		if tokens[0] in concept_id:
			sys.stderr.write('ERROR: duplicate concept \"%s\", line %d in %s\n' % (tokens[0], concept + 1, concept_weight_file))
			sys.exit(1)
		concept_id[tokens[0]] = concept
		concept_weights[concept] = weight
		concept += 1
	depconcept_id = {}
	depconcept = 0
	depconcept_weights = {}
	for line in open(depconcept_weight_file):
		tokens = line.strip().split()
		weight = float(tokens[1])
		if tokens[0] in depconcept_id:
			sys.stderr.write('ERROR: duplicate depconcept \"%s\", line %d in %s\n' % (tokens[0], depconcept + 1, depconcept_weight_file))
			sys.exit(1)
		depconcept_id[tokens[0]] = depconcept
		depconcept_weights[depconcept] = weight
		depconcept += 1

	index = {}
	sentence_concepts = {}
	sentence = 0
	for line in open(concepts_in_sentence_file):
		tokens = line.strip().split()
		concepts = {}
		for token in tokens:
			concepts[token] = True
		mapped_concepts = {}
		for concept in concepts:
			if concept not in concept_id:
				sys.stderr.write('ERROR: not weight for concept \"%s\", line %d in %s\n' % (concept, sentence + 1, concepts_in_sentence_file))
				sys.exit(1)
			id = concept_id[concept]
			if id not in index: index[id] = []
			index[id].append(sentence)
			mapped_concepts[id] = True
		if len(mapped_concepts) > 0:
			sentence_concepts[sentence] = mapped_concepts
		sentence += 1
	depindex = {}
	sentence_depconcepts = {}
	sentence = 0
	for line in open(depconcepts_in_sentence_file):
		tokens = line.strip().split()
		depconcepts = {}
		for token in tokens:
			depconcepts[token] = True
		mapped_depconcepts = {}
		for depconcept in depconcepts:
			if depconcept not in depconcept_id:
				sys.stderr.write('ERROR: not weight for depconcept \"%s\", line %d in %s\n' % (depconcept, sentence + 1, depconcepts_in_sentence_file))
				sys.exit(1)
			id = depconcept_id[depconcept]
			if id not in depindex: depindex[id] = []
			depindex[id].append(sentence)
			mapped_depconcepts[id] = True
		if len(mapped_depconcepts) > 0:
			sentence_depconcepts[sentence] = mapped_depconcepts
		sentence += 1

	# build objective
	objective = []
	for concept, weight in concept_weights.items():
		if concept not in index: continue # skip unused concepts
		objective.append("%+g c%d" % (alpha*weight, concept))
		solver.binary["c%d" % concept] = concept
	for depconcept, weight in depconcept_weights.items():
		if depconcept not in depindex: continue # skip unused concepts
		objective.append("%+g k%d" % (beta*weight, depconcept))
		solver.binary["k%d" % depconcept] = depconcept
	solver.objective["score"] = " ".join(objective)

	# sentence => concepts
	for sentence, concepts in sentence_concepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, depconcepts in sentence_depconcepts.items():
		solver.binary["s%d" % sentence] = sentence
	#	for concept in concepts:
	#		solver.constraints["sent_%d" % len(solver.constraints)] = "s%d - c%d <= 0" % (sentence, concept)

	# concept => sentence
	for concept in index:
		solver.constraints["index_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in index[concept]]) + " - c%d >= 0" % concept
	for depconcept in depindex:
		solver.constraints["depindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in depindex[depconcept]]) + " - k%d >= 0" % depconcept

 #   if sentence_group_file != None:
 #	   groups = {}
 #	   sentence = 0
 #	   for line in open(sentence_group_file):
 #		   if sentence in sentence_concepts:
 #			   if line != '\n':
 #				   if line not in groups:
 #					   groups[line] = []
 #				   groups[line].append(sentence)
 #		   sentence += 1
 #	   for group in groups:
 #		   solver.constraints["group_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in groups[group]]) + " <= 1"

 #   if dependency_file != None:
 #	   groups = {}
 #	   sentence = 0
 #	   for line in open(dependency_file):
 #		   if sentence in sentence_concepts:
 #			   if line != '\n':
 #				   for id in line.strip().split():
 #					   id = int(id)
 #					   if "s%d" % id not in solver.binary:
 #						   solver.constraints["depend_%d" % len(solver.constraints)] = "s%d = 0" % (sentence)
 #					   else:
 #						   solver.constraints["depend_%d" % len(solver.constraints)] = "s%d - s%d >= 0" % (id, sentence)
 #		   sentence += 1

	length_constraint = []
	sentence = 0
	for line in open(sentence_length_file):
		if sentence in sentence_concepts:
			length = line.strip()
			length_constraint.append("%s s%d" % (length, sentence))
			solver.objective["score"] += " - %g s%d" % (float(length) / 1000.0, sentence)
		sentence += 1

	solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)

	if atleast != None:
		at_least = []
		sentence = 0
		for line in open(atleast):
			line = line.strip()
			if sentence in sentence_concepts:
				if line == "1":
					at_least.append("s%d" % sentence)
			sentence += 1
		if len(at_least) > 0:
			solver.constraints["at_least_%d" % len(solver.constraints)] = " + ".join(at_least) + " >= 1" # select at least one of those

	sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts)+len(sentence_depconcepts), len(index)+len(depindex)))

	if len(sentence_concepts)+len(sentence_depconcepts) > 0 and len(index)+len(depindex) > 0:
		solver.run()
	output = []
	for variable in solver.output:
		if variable.startswith("s") and solver.output[variable] == 1:
			output.append(int(variable[1:]))
	return output
	
def decodelaw2(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, depconcepts_in_sentence_file, depconcept_weight_file, depconcepts_weight, semconcepts_in_sentence_file, semconcept_weight_file, semconcepts_weight, sentence_group_file=None, dependency_file=None, atleast=None, command="glpsol"):
	solver = ilp.IntegerLinearProgram(debug=1, tmp = "tmp_decoder.%d.%s.%s" % (os.getpid(), os.environ["USER"], os.environ["HOSTNAME"]), command=command)
	print "dep weight: ", depconcepts_weight
	print "sem weight: ", semconcepts_weight
	alpha=1-float(depconcepts_weight)-float(semconcepts_weight)
	beta=float(depconcepts_weight)
	gamma=float(semconcepts_weight)
	concept_id = {}
	concept = 0
	concept_weights = {}
	for line in open(concept_weight_file):
		tokens = line.strip().split()
		weight = float(tokens[1])
		if tokens[0] in concept_id:
			sys.stderr.write('ERROR: duplicate concept \"%s\", line %d in %s\n' % (tokens[0], concept + 1, concept_weight_file))
			sys.exit(1)
		concept_id[tokens[0]] = concept
		concept_weights[concept] = weight
		concept += 1
	depconcept_id = {}
	depconcept = 0
	depconcept_weights = {}
	for line in open(depconcept_weight_file):
		tokens = line.strip().split()
		weight = float(tokens[1])
		if tokens[0] in depconcept_id:
			sys.stderr.write('ERROR: duplicate depconcept \"%s\", line %d in %s\n' % (tokens[0], depconcept + 1, depconcept_weight_file))
			sys.exit(1)
		depconcept_id[tokens[0]] = depconcept
		depconcept_weights[depconcept] = weight
		depconcept += 1
	semconcept_id = {}
	semconcept = 0
	semconcept_weights = {}
	print semconcept_weight_file
	for line in open(semconcept_weight_file):
		tokens = line.strip().split()
#		print tokens
		weight = float(tokens[1])
		if tokens[0] in semconcept_id:
			sys.stderr.write('ERROR: duplicate semconcept \"%s\", line %d in %s\n' % (tokens[0], semconcept + 1, semconcept_weight_file))
			sys.exit(1)
		semconcept_id[tokens[0]] = semconcept
		semconcept_weights[semconcept] = weight
		semconcept += 1

	index = {}
	sentence_concepts = {}
	sentence = 0
	for line in open(concepts_in_sentence_file):
		tokens = line.strip().split()
		concepts = {}
		for token in tokens:
			concepts[token] = True
		mapped_concepts = {}
		for concept in concepts:
			if concept not in concept_id:
				sys.stderr.write('ERROR: not weight for concept \"%s\", line %d in %s\n' % (concept, sentence + 1, concepts_in_sentence_file))
				sys.exit(1)
			id = concept_id[concept]
			if id not in index: index[id] = []
			index[id].append(sentence)
			mapped_concepts[id] = True
		if len(mapped_concepts) > 0:
			sentence_concepts[sentence] = mapped_concepts
		sentence += 1
	depindex = {}
	sentence_depconcepts = {}
	sentence = 0
	for line in open(depconcepts_in_sentence_file):
		tokens = line.strip().split()
		depconcepts = {}
		for token in tokens:
			depconcepts[token] = True
		mapped_depconcepts = {}
		for depconcept in depconcepts:
			if depconcept not in depconcept_id:
				sys.stderr.write('ERROR: not weight for depconcept \"%s\", line %d in %s\n' % (depconcept, sentence + 1, depconcepts_in_sentence_file))
				sys.exit(1)
			id = depconcept_id[depconcept]
			if id not in depindex: depindex[id] = []
			depindex[id].append(sentence)
			mapped_depconcepts[id] = True
		if len(mapped_depconcepts) > 0:
			sentence_depconcepts[sentence] = mapped_depconcepts
		sentence += 1
	semindex = {}
	sentence_semconcepts = {}
	sentence = 0
	for line in open(semconcepts_in_sentence_file):
		tokens = line.strip().split()
		semconcepts = {}
		for token in tokens:
			semconcepts[token] = True
		mapped_semconcepts = {}
		for semconcept in semconcepts:
			if semconcept not in semconcept_id:
				sys.stderr.write('ERROR: not weight for semconcept \"%s\", line %d in %s\n' % (semconcept, sentence + 1, semconcepts_in_sentence_file))
				sys.exit(1)
			id = semconcept_id[semconcept]
			if id not in semindex: semindex[id] = []
			semindex[id].append(sentence)
			mapped_semconcepts[id] = True
		if len(mapped_semconcepts) > 0:
			sentence_semconcepts[sentence] = mapped_semconcepts
		sentence += 1

	# build objective
	objective = []
	for concept, weight in concept_weights.items():
		if concept not in index: continue # skip unused concepts
		objective.append("%+g c%d" % (alpha*weight, concept))
		solver.binary["c%d" % concept] = concept
	for depconcept, weight in depconcept_weights.items():
		if depconcept not in depindex: continue # skip unused concepts
		objective.append("%+g k%d" % (beta*weight, depconcept))
		solver.binary["k%d" % depconcept] = depconcept
	for semconcept, weight in semconcept_weights.items():
		if semconcept not in semindex: continue # skip unused concepts
		objective.append("%+g l%d" % (gamma*weight, semconcept))
		solver.binary["l%d" % semconcept] = semconcept
	solver.objective["score"] = " ".join(objective)

	# sentence => concepts
	for sentence, concepts in sentence_concepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, depconcepts in sentence_depconcepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, semconcepts in sentence_semconcepts.items():
		solver.binary["s%d" % sentence] = sentence

	# concept => sentence
	for concept in index:
		solver.constraints["index_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in index[concept]]) + " - c%d >= 0" % concept
	for depconcept in depindex:
		solver.constraints["depindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in depindex[depconcept]]) + " - k%d >= 0" % depconcept
	for semconcept in semindex:
		solver.constraints["semindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in semindex[semconcept]]) + " - l%d >= 0" % semconcept

	length_constraint = []
	sentence = 0
	for line in open(sentence_length_file):
		if sentence in sentence_concepts:
			length = line.strip()
			length_constraint.append("%s s%d" % (length, sentence))
			solver.objective["score"] += " - %g s%d" % (float(length) / 1000.0, sentence)
		sentence += 1

	solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)

	if atleast != None:
		at_least = []
		sentence = 0
		for line in open(atleast):
			line = line.strip()
			if sentence in sentence_concepts:
				if line == "1":
					at_least.append("s%d" % sentence)
			sentence += 1
		if len(at_least) > 0:
			solver.constraints["at_least_%d" % len(solver.constraints)] = " + ".join(at_least) + " >= 1" # select at least one of those

	sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts)+len(sentence_depconcepts)+len(sentence_semconcepts), len(index)+len(depindex)+len(semindex)))

	if len(sentence_concepts)+len(sentence_depconcepts)+len(sentence_semconcepts) > 0 and len(index)+len(depindex)+len(semindex) > 0:
		solver.run()
	output = []
	for variable in solver.output:
		if variable.startswith("s") and solver.output[variable] == 1:
			output.append(int(variable[1:]))
	return output

def decode_simple(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, timelimit=100, command="glpsol"):
	solver = ilp.IntegerLinearProgram(debug=1, tmp = "tmp_decoder.%d.%s.%s" % (os.getpid(), os.environ["USER"], os.environ["HOSTNAME"]), command=command, time_limit=timelimit)
	alpha=1
	concept_id, concept, concept_weights=getConcepts(concept_weight_file, alpha, 'concept')

	index = {};	 sentence_concepts = {};
	index, sentence_concepts=getSentencesWithConcepts(concepts_in_sentence_file, concept_id)
					
	# build objective
	objective = []
	for concept, weight in concept_weights.items():
		if concept not in index: continue # skip unused concepts
		objective.append("%+g c%d" % (alpha*weight, concept))
		solver.binary["c%d" % concept] = concept
	solver.objective["score"] = " ".join(objective)

	# binary sentences
	for sentence, concepts in sentence_concepts.items():
		solver.binary["s%d" % sentence] = sentence

	# concept => sentence (absent from original)
	#DON'T NEED THIS, SINCE THE SYSTEM WILL TRY TO INCLUDE AS MANY CONCEPTS AS POSSIBLE ANYWAYS

	# sentences => concepts
	for concept in index:
		solver.constraints["index_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in index[concept]]) + " - c%d >= 0" % concept

	length_constraint = []
	sentence = 0
	for line in open(sentence_length_file):
		if sentence in sentence_concepts :
			length = line.strip()
			length_constraint.append("%s s%d" % (length, sentence))
#			solver.objective["score"] += " - %g s%d" % (float(length) / 1000.0, sentence)
		sentence += 1

	solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)

	sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts), len(index)))

	if len(sentence_concepts) > 0 and len(index) > 0:
		print "SOLVING"
		solver.run()
		print "SOLVED"
	output = []
	for variable in solver.output:
		if variable.startswith("s") and solver.output[variable] == 1:
			output.append(int(variable[1:]))
	return output

def decodegold(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, timelimit=100, sentence_group_file=None, dependency_file=None, atleast=None, command="glpsol"):
	solver = ilp.IntegerLinearProgram(debug=1, tmp = "tmp_decoder.%d.%s.%s" % (os.getpid(), os.environ["USER"], os.environ["HOSTNAME"]), command=command, time_limit=timelimit)
	concept_id, concept, concept_weight_bounds=getConceptsGold(concept_weight_file)

	index, sentence_concepts = getSentencesWithConceptsGold(concepts_in_sentence_file, concept_id) #concept:[sentences], sentence:[concept:freq pairs]

	# build objective (sum of matches across all references)
	objective = []
	varindex=1 #mik
	var_map={}
	inv_var_map={} #refnum:varindices 
	for concept, weights in concept_weight_bounds.items():
		if concept not in index: 
			continue # skip unused concepts
		for x in xrange(len(weights)):
			objective.append("m"+str(varindex))
			solver.integer["m"+str(varindex)] = varindex
			var_map[varindex]=(concept,x)
			if x not in inv_var_map.keys():
				inv_var_map[x]={}
			inv_var_map[x][concept]=varindex
			varindex+=1
	solver.objective["score"] = " + ".join(objective)

	# binary sentences
	for sentence, concepts in sentence_concepts.items():
		solver.binary["s%d" % sentence] = sentence
		
	# match bounded by document freqs
	for id, sents in index.items():
		constraint=[]
		for sent in sents:
			constraint.append(str(sentence_concepts[sent][id])+' s'+str(sent))
		for ref in inv_var_map.keys():
			solver.constraints['docfreq_%d' % len(solver.constraints)] = " + ".join(constraint)+' - m'+ str(inv_var_map[ref][id])+' >= 0 '

	#match bounded by reference freqs
	for concept, freqs in concept_weight_bounds.items(): #i
		for x in xrange(len(freqs)): #k
			solver.constraints['reffreq_%d' % len(solver.constraints)] = ' m'+ str(inv_var_map[x][concept])+' <= '+str(freqs[x])
			
	length_constraint = []
	sentence = 0
	for line in open(sentence_length_file):
		if sentence in sentence_concepts:
			length = line.strip()
			length_constraint.append("%s s%d" % (length, sentence))
		sentence += 1

	solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)

	sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts), len(index)))
	if len(sentence_concepts) > 0 and len(index) > 0:
		print "SOLVING"
		solver.run()
		print "SOLVED"
	output = []
	for variable in solver.output:
		if variable.startswith("s") and solver.output[variable] == 1:
			output.append(int(variable[1:]))
	return output

def getConceptsGold(concept_weight_file):
	concept_id={}
	concept=0
	concept_weight_bounds={}
	for line in open(concept_weight_file):
		tokens = line.strip().split()
		concept_id[tokens[0]] = concept
		concept_weight_bounds[concept] = [float(item) for item in tokens[2:]]
		concept += 1
	return concept_id, concept, concept_weight_bounds

	
def getConcepts(concept_weight_file, contribution, conceptname):
	concept_id={}
	concept=0
	concept_weights={}
	if contribution>0:
		for line in open(concept_weight_file):
			tokens = line.strip().split()
			weight = float(tokens[1])
			if tokens[0] in concept_id:
				sys.stderr.write('ERROR: duplicate '+conceptname+' \"%s\", line %d in %s\n' % (tokens[0], neconcept + 1, concept_weight_file))
				sys.exit(1)
			concept_id[tokens[0]] = concept
			concept_weights[concept] = weight
			concept += 1
	return concept_id, concept, concept_weights

def getSentencesWithConceptsGold(concepts_in_sentence_file, concept_id):
	index = {};	 sentence_concepts = {};	sentence = 0
	for line in open(concepts_in_sentence_file):
		tokens = line.strip().split()
		concepts = collections.defaultdict(int)
		for token in tokens:
			concepts[token] += 1
		mapped_concepts = collections.defaultdict(int)
		for concept in concepts:
			id = concept_id[concept]
			if id not in index: index[id] = []
			index[id].append(sentence) #concept:[sentences]
			mapped_concepts[id] +=1
		if len(mapped_concepts) > 0:
			sentence_concepts[sentence] = mapped_concepts #sentence:[concept:freq pairs]
		sentence += 1
	return index, sentence_concepts

def getSentencesWithConcepts(concepts_in_sentence_file, concept_id):
	index = {};	 sentence_concepts = {};	sentence = 0
	for line in open(concepts_in_sentence_file):
		tokens = line.strip().split()
		concepts = {}
		for token in tokens:
			concepts[token] =True
		mapped_concepts = {}
		for concept in concepts:
			id = concept_id[concept]
			if id not in index: index[id] = []
			index[id].append(sentence) #concept:[sentences]
			mapped_concepts[id] =True
		if len(mapped_concepts) > 0:
			sentence_concepts[sentence] = mapped_concepts #sentence:[concept:freq pairs]
		sentence += 1
	return index, sentence_concepts
	
def decodelaw3(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, depconcepts_in_sentence_file, depconcept_weight_file, depconcepts_weight, semconcepts_in_sentence_file, semconcept_weight_file, semconcepts_weight, psemconcepts_in_sentence_file, psemconcept_weight_file, psemconcepts_weight, ldconcepts_in_sentence_file, ldconcept_weight_file, ldconcepts_weight, neconcepts_in_sentence_file, neconcept_weight_file, neconcepts_weight, timelimit=100, sentence_group_file=None, dependency_file=None, atleast=None, command="glpsol"):
	solver = ilp.IntegerLinearProgram(debug=1, tmp = "tmp_decoder.%d.%s.%s" % (os.getpid(), os.environ["USER"], os.environ["HOSTNAME"]), command=command, time_limit=timelimit)
	alpha=1-float(depconcepts_weight)-float(semconcepts_weight)-float(psemconcepts_weight)-float(ldconcepts_weight)-float(neconcepts_weight)
	beta1=float(depconcepts_weight)
	beta2=float(semconcepts_weight)
	beta3=float(psemconcepts_weight)
	beta4=float(ldconcepts_weight)
	beta5=float(neconcepts_weight)
	concept_id, concept, concept_weights=getConcepts(concept_weight_file, alpha, 'concept')
	depconcept_id, depconcept, depconcept_weights=getConcepts(depconcept_weight_file, beta1, 'depconcept')
	semconcept_id, semconcept, semconcept_weights=getConcepts(semconcept_weight_file, beta2, 'semconcept')
	psemconcept_id, psemconcept, psemconcept_weights=getConcepts(psemconcept_weight_file, beta3, 'psemconcept')
	ldconcept_id, ldconcept, ldconcept_weights=getConcepts(ldconcept_weight_file, beta4, 'ldconcept')
	neconcept_id, neconcept, neconcept_weights=getConcepts(neconcept_weight_file, beta5, 'neconcept')

	index = {};	 sentence_concepts = {};
	if alpha>0:
		index, sentence_concepts=getSentencesWithConcepts(concepts_in_sentence_file, 'concept', concept_id)

	depindex = {};	sentence_depconcepts = {}
	if beta1>0:
		depindex, sentence_depconcepts=getSentencesWithConcepts(depconcepts_in_sentence_file, 'depconcept', depconcept_id)
	semindex = {};	sentence_semconcepts = {}
	if beta2>0:
		semindex, sentence_semconcepts=getSentencesWithConcepts(semconcepts_in_sentence_file, 'semconcept', semconcept_id)
	psemindex = {};	sentence_psemconcepts = {}
	if beta3>0:
		psemindex, sentence_psemconcepts=getSentencesWithConcepts(psemconcepts_in_sentence_file, 'psemconcept', psemconcept_id)
	ldindex = {};	sentence_ldconcepts = {}
	if beta4>0:
		ldindex, sentence_ldconcepts=getSentencesWithConcepts(ldconcepts_in_sentence_file, 'ldconcept', ldconcept_id)
	neindex = {};	sentence_neconcepts = {}
	if beta5>0:
		neindex, sentence_neconcepts=getSentencesWithConcepts(neconcepts_in_sentence_file, 'neconcept', neconcept_id)
					
	# build objective
	objective = []
	if alpha>0:
		for concept, weight in concept_weights.items():
			if concept not in index: continue # skip unused concepts
			objective.append("%+g c%d" % (alpha*weight, concept))
			solver.binary["c%d" % concept] = concept
	if beta1>0:
		for depconcept, weight in depconcept_weights.items():
			if depconcept not in depindex: continue # skip unused concepts
			objective.append("%+g k%d" % (beta1*weight, depconcept))
			solver.binary["k%d" % depconcept] = depconcept
	if beta2>0:
		for semconcept, weight in semconcept_weights.items():
			if semconcept not in semindex: continue # skip unused concepts
			objective.append("%+g l%d" % (beta2*weight, semconcept))
			solver.binary["l%d" % semconcept] = semconcept
	if beta3>0:
		for psemconcept, weight in psemconcept_weights.items():
			if psemconcept not in psemindex: continue # skip unused concepts
			objective.append("%+g j%d" % (beta3*weight, psemconcept))
			solver.binary["j%d" % psemconcept] = psemconcept
	if beta4>0:
		for ldconcept, weight in ldconcept_weights.items():
			if ldconcept not in ldindex: continue # skip unused concepts
			objective.append("%+g h%d" % (beta4*weight, ldconcept))
			solver.binary["h%d" % ldconcept] = ldconcept
	if beta5>0:
		for neconcept, weight in neconcept_weights.items():
			if neconcept not in neindex: continue # skip unused concepts
			objective.append("%+g b%d" % (beta5*weight, neconcept))
			solver.binary["b%d" % neconcept] = neconcept
	solver.objective["score"] = " ".join(objective)

	# binary sentences
	for sentence, concepts in sentence_concepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, depconcepts in sentence_depconcepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, semconcepts in sentence_semconcepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, psemconcepts in sentence_psemconcepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, ldconcepts in sentence_ldconcepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, neconcepts in sentence_neconcepts.items():
		solver.binary["s%d" % sentence] = sentence

	# concept => sentence (absent from original)
	#DON'T NEED THIS, SINCE THE SYSTEM WILL TRY TO INCLUDE AS MANY CONCEPTS AS POSSIBLE ANYWAYS

	# sentences => concepts
	for concept in index:
		solver.constraints["index_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in index[concept]]) + " - c%d >= 0" % concept
	for depconcept in depindex:
		solver.constraints["depindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in depindex[depconcept]]) + " - k%d >= 0" % depconcept
	for semconcept in semindex:
		solver.constraints["semindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in semindex[semconcept]]) + " - l%d >= 0" % semconcept
	for psemconcept in psemindex:
		solver.constraints["psemindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in psemindex[psemconcept]]) + " - j%d >= 0" % semconcept
	for ldconcept in ldindex:
		solver.constraints["ldindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in ldindex[ldconcept]]) + " - h%d >= 0" % ldconcept
	for neconcept in neindex:
		solver.constraints["neindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in neindex[neconcept]]) + " - b%d >= 0" % neconcept

	length_constraint = []
	sentence = 0
	for line in open(sentence_length_file):
		if sentence in sentence_concepts or (sentence in sentence_depconcepts) or (sentence in sentence_semconcepts)or (sentence in sentence_psemconcepts) or (sentence in sentence_ldconcepts)or (sentence in sentence_neconcepts):
			length = line.strip()
			length_constraint.append("%s s%d" % (length, sentence))
#			solver.objective["score"] += " - %g s%d" % (float(length) / 1000.0, sentence)
		sentence += 1

	solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)

	if atleast != None:
		at_least = []
		sentence = 0
		for line in open(atleast):
			line = line.strip()
			if sentence in sentence_concepts or (sentence in sentence_depconcepts) or (sentence in sentence_semconcepts)or (sentence in sentence_psemconcepts) or (sentence in sentence_ldconcepts)or (sentence in sentence_neconcepts):
				if line == "1":
					at_least.append("s%d" % sentence)
			sentence += 1
		if len(at_least) > 0:
			solver.constraints["at_least_%d" % len(solver.constraints)] = " + ".join(at_least) + " >= 1" # select at least one of those

	sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts)+len(sentence_depconcepts)+len(sentence_semconcepts)+len(sentence_psemconcepts)+len(sentence_ldconcepts)+len(sentence_neconcepts), len(index)+len(depindex)+len(semindex)+len(psemindex)+len(ldindex)+len(neindex)))

	if len(sentence_concepts)+len(sentence_depconcepts)+len(sentence_semconcepts)+len(sentence_psemconcepts)+len(sentence_ldconcepts)+len(sentence_neconcepts) > 0 and len(index)+len(depindex)+len(semindex)+len(psemindex)+len(ldindex)+len(neindex) > 0:
		print "SOLVING"
		solver.run()
		print "SOLVED"
	output = []
	for variable in solver.output:
		if variable.startswith("s") and solver.output[variable] == 1:
			output.append(int(variable[1:]))
	return output

def decodelaw_struct(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, semconcepts_in_sentence_file, semconcept_weight_file, semconcepts_weight, timelimit=100, sentence_group_file=None, dependency_file=None, atleast=None, section_file=None, relaxed=True, by_article=False, prop2=False, articlesdir=None, id=None, factbudget=229, lawbudget=576, command="glpsol"):
	extrainfo=""
	if by_article:
		extrainfo=extrainfo+'_art'
	if prop2:
		extrainfo=extrainfo+'_p2'
	if relaxed:
		extrainfo=extrainfo+'_r'
	solver = ilp.IntegerLinearProgram(debug=1, tmp = "tmp_decoder.%d.%s.%s.%s" % (os.getpid(), extrainfo,os.environ["USER"], os.environ["HOSTNAME"]), command=command, time_limit=timelimit)
	alpha=1-float(semconcepts_weight)
	beta=float(semconcepts_weight)
	concept_id, concept, concept_weights=getConcepts(concept_weight_file, alpha, 'concept')
	semconcept_id, semconcept, semconcept_weights=getConcepts(semconcept_weight_file, beta, 'semconcept')

	index = {};	 sentence_concepts = {};
	if alpha>0:
		index, sentence_concepts=getSentencesWithConcepts(concepts_in_sentence_file, 'concept', concept_id)

	semindex = {};	sentence_semconcepts = {}
	if beta>0:
		semindex, sentence_semconcepts=getSentencesWithConcepts(semconcepts_in_sentence_file, 'semconcept', semconcept_id)
	#section of sentence
	sectionsindex={};	#(fact,[sentence no. list])
	sentence_sections={}; articles=[]; sectionids={} ; facts_sentence_sections={}; law_sentence_sections={}; art_sentence_sections={}; sentence_articles={}
	if section_file is not None:
		sect=0
		sectionfile=open(section_file,'r')
		sectionlines=sectionfile.readlines()
		sectionfile.close()
		for x in xrange(len(sectionlines)):
			line=sectionlines[x].strip()
			if len(line)>0:
				line=line.split(' ')
				mapped_sections={}
				for l in line: #iterate through concepts
					if l not in sectionsindex.keys():
						sectionsindex[l]=[]
						if 'article' in l:
							articles.append(l)
					sectionsindex[l].append(x)
					mapped_sections[l]=True
					sentence_sections[x]=mapped_sections
					if l=='facts':
						facts_sentence_sections[x]=mapped_sections
					elif l=='law':
						law_sentence_sections[x]=mapped_sections
					else:
						art_sentence_sections[x]=mapped_sections
						sentence_articles[x]=l
						

	# build objective
	objective = []
	if alpha>0:
		for concept, weight in concept_weights.items():
			if concept not in index: continue # skip unused concepts
			objective.append("%+g c%d" % (alpha*weight, concept))
			solver.binary["c%d" % concept] = concept
	if beta>0:
		for semconcept, weight in semconcept_weights.items():
			if semconcept not in semindex: continue # skip unused concepts
			objective.append("%+g l%d" % (beta*weight, semconcept))
			solver.binary["l%d" % semconcept] = semconcept
	solver.objective["score"] = " ".join(objective)

	#binary sentences
	for sentence, concepts in sentence_concepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, semconcepts in sentence_semconcepts.items():
		solver.binary["s%d" % sentence] = sentence

	# concept => sentence (absent from original)
	#DON'T NEED THIS, SINCE THE SYSTEM WILL TRY TO INCLUDE AS MANY CONCEPTS AS POSSIBLE ANYWAYS

	# sentences => concepts
	for concept in index:
		solver.constraints["index_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in index[concept]]) + " - c%d >= 0" % concept
	for semconcept in semindex:
		solver.constraints["semindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in semindex[semconcept]]) + " - l%d >= 0" % semconcept

		
	sentence = 0
	if by_article:
		if prop2:		#calculate proportions
			art_prop={}
			totalsize=0.0
			for art in articles:
				this_art_file = articlesdir+id+'/'+art+'/'
				if beta>0:
					art_prop[art]=os.path.getsize(this_art_file+art+'.sem')
				else:
					art_prop[art]=os.path.getsize(this_art_file+art+'.sent')
				totalsize+=art_prop[art]
			for art in articles:
				art_prop[art]=float(art_prop[art])/float(totalsize)
		if relaxed:
			length_constraint = []
			for line in open(sentence_length_file): #for relaxed budget
				if ((sentence in facts_sentence_sections) or (sentence in art_sentence_sections)) and (sentence in sentence_concepts or (sentence in sentence_semconcepts)):
					length = line.strip()
					length_constraint.append("%s s%d" % (length, sentence))
				else: #make sure sentence is not chosen
					solver.constraints["exclude_%d" % len(solver.constraints)] = "s%d = 0"% sentence 
				sentence += 1
			solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)
		else:
			length_constraint_facts = []
			length_constraint_art = {}
			for line in open(sentence_length_file): #for relaxed budget
				if(sentence in sentence_concepts or (sentence in sentence_semconcepts)):
					if sentence in facts_sentence_sections :
						length = line.strip()
						length_constraint_facts.append("%s s%d" % (length, sentence))
					elif sentence in art_sentence_sections :
						length = line.strip()
						if sentence_articles[sentence] not in length_constraint_art:
							length_constraint_art[sentence_articles[sentence]]=[]
						length_constraint_art[sentence_articles[sentence]].append("%s s%d" % (length, sentence))
					else: # make sure sentence not chosen
						solver.constraints["exclude_%d" % len(solver.constraints)] = "s%d = 0"% sentence 
					
				sentence += 1
			solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint_facts) + " <= " + str(factbudget)
			for art in length_constraint_art.keys():
				if prop2:
					solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint_art[art]) + " <= " + str(float(lawbudget)*art_prop[art]) #prop2
				else:
					solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint_art[art]) + " <= " + str(float(lawbudget)/float(len(length_constraint_art.keys()))) #divide
	else:
		if relaxed:
			length_constraint = []
			for line in open(sentence_length_file): #for relaxed budget
				if sentence in sentence_sections and (sentence in sentence_concepts or (sentence in sentence_semconcepts)):
					length = line.strip()
					length_constraint.append("%s s%d" % (length, sentence))
				else: #make sure sentence is not chosen
					solver.constraints["exclude_%d" % len(solver.constraints)] = "s%d = 0"% sentence 
				sentence += 1
			solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)
		else:
			length_constraint_facts = []
			length_constraint_law = []
			for line in open(sentence_length_file): #for relaxed budget
				if(sentence in sentence_concepts or (sentence in sentence_semconcepts)):
					if sentence in facts_sentence_sections :
						length = line.strip()
						length_constraint_facts.append("%s s%d" % (length, sentence))
					elif sentence in law_sentence_sections :
						length = line.strip()
						length_constraint_law.append("%s s%d" % (length, sentence))
					else: # make sure sentence not chosen
						solver.constraints["exclude_%d" % len(solver.constraints)] = "s%d = 0"% sentence 
					
				sentence += 1
			solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint_facts) + " <= " + str(factbudget)
			solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint_law) + " <= " + str(lawbudget)

	if atleast != None:
		at_least = []
		sentence = 0
		for line in open(atleast):
			line = line.strip()
			if sentence in sentence_concepts or (sentence in sentence_semconcepts):
				if line == "1":
					at_least.append("s%d" % sentence)
			sentence += 1
		if len(at_least) > 0:
			solver.constraints["at_least_%d" % len(solver.constraints)] = " + ".join(at_least) + " >= 1" # select at least one of those

	sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts)+len(sentence_semconcepts), len(index)+len(semindex)))

	if len(sentence_concepts)+len(sentence_semconcepts) > 0 and len(index)+len(semindex) > 0:
		print "SOLVING"
		solver.run()
		print "SOLVED"
	output = []
	for variable in solver.output:
		if variable.startswith("s") and solver.output[variable] == 1:
			output.append(int(variable[1:]))
	return output

def decodelaw4(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, wordconcepts_in_sentence_file, wordconcept_weight_file, timelimit=100, sentence_group_file=None, dependency_file=None, atleast=None, command="glpsol"):
	solver = ilp.IntegerLinearProgram(debug=1, tmp = "tmp_decoder.%d.%s.%s" % (os.getpid(), os.environ["USER"], os.environ["HOSTNAME"]), command=command, time_limit=timelimit)
	alpha=1; beta=0
	concept_id, concept, concept_weights=getConcepts(concept_weight_file, alpha, 'concept')
	wordconcept_id, wordconcept, wordconcept_weights=getConcepts(wordconcept_weight_file, beta, 'wordconcept')

	index = {};	 sentence_concepts = {};
	if alpha>0:
		index, sentence_concepts=getSentencesWithConcepts(concepts_in_sentence_file, 'concept', concept_id)

	wordindex = {};	sentence_wordconcepts = {}
	if beta>0:
		wordindex, sentence_wordconcepts=getSentencesWithConcepts(wordconcepts_in_sentence_file, 'wordconcept', wordconcept_id)

	# build objective
	objective = []
	if alpha>0:
		for concept, weight in concept_weights.items():
			if concept not in index: continue # skip unused concepts
			objective.append("%+g c%d" % (alpha*weight, concept))
			solver.binary["c%d" % concept] = concept
	if beta>0:
		for wordconcept, weight in wordconcept_weights.items():
			if wordconcept not in wordindex: continue # skip unused concepts
			objective.append("%+g k%d" % (beta*weight, wordconcept))
			solver.binary["k%d" % wordconcept] = wordconcept
	solver.objective["score"] = " ".join(objective)

	# sentence => concepts
	for sentence, concepts in sentence_concepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, wordconcepts in sentence_wordconcepts.items():
		solver.binary["s%d" % sentence] = sentence

	# concept => sentence
	for concept in index:
		solver.constraints["index_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in index[concept]]) + " - c%d >= 0" % concept
	for wordconcept in wordindex:
		solver.constraints["wordindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in wordindex[wordconcept]]) + " - k%d >= 0" % wordconcept

	length_constraint = []
	sentence = 0
	for line in open(sentence_length_file):
		if sentence in sentence_concepts or (sentence in sentence_wordconcepts):
			length = line.strip()
			length_constraint.append("%s s%d" % (length, sentence))
		sentence += 1

	solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)

	if atleast != None:
		at_least = []
		sentence = 0
		for line in open(atleast):
			line = line.strip()
			if sentence in sentence_concepts or (sentence in sentence_wordconcepts) :
				if line == "1":
					at_least.append("s%d" % sentence)
			sentence += 1
		if len(at_least) > 0:
			solver.constraints["at_least_%d" % len(solver.constraints)] = " + ".join(at_least) + " >= 1" # select at least one of those

	sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts)+len(sentence_wordconcepts), len(index)+len(wordindex)))

	if len(sentence_concepts)+len(sentence_wordconcepts) > 0 and len(index)+len(wordindex) > 0:
		solver.run()
	output = []
	for variable in solver.output:
		if variable.startswith("s") and solver.output[variable] == 1:
			output.append(int(variable[1:]))
	return output

def decodelaw_gurobi(max_length, sentence_length_file, concepts_in_sentence_file, concept_weight_file, depconcepts_in_sentence_file, depconcept_weight_file, depconcepts_weight, semconcepts_in_sentence_file, semconcept_weight_file, semconcepts_weight, psemconcepts_in_sentence_file, psemconcept_weight_file, psemconcepts_weight, ldconcepts_in_sentence_file, ldconcept_weight_file, ldconcepts_weight, neconcepts_in_sentence_file, neconcept_weight_file, neconcepts_weight, timelimit=100, sentence_group_file=None, dependency_file=None, atleast=None, command="gurobi_cl"):
	solver = ilp.IntegerLinearProgram(debug=1, tmp = "tmp_decoder.%d.%s.%s" % (os.getpid(), os.environ["USER"], os.environ["HOSTNAME"]), command=command)
	alpha=1-float(depconcepts_weight)-float(semconcepts_weight)-float(psemconcepts_weight)-float(ldconcepts_weight)-float(neconcepts_weight)
	beta1=float(depconcepts_weight)
	beta2=float(semconcepts_weight)
	beta3=float(psemconcepts_weight)
	beta4=float(ldconcepts_weight)
	beta5=float(neconcepts_weight)
	concept_id, concept, concept_weights=getConcepts(concept_weight_file, alpha, 'concept')
	depconcept_id, depconcept, depconcept_weights=getConcepts(depconcept_weight_file, beta1, 'depconcept')
	semconcept_id, semconcept, semconcept_weights=getConcepts(semconcept_weight_file, beta2, 'semconcept')
	psemconcept_id, psemconcept, psemconcept_weights=getConcepts(psemconcept_weight_file, beta3, 'psemconcept')
	ldconcept_id, ldconcept, ldconcept_weights=getConcepts(ldconcept_weight_file, beta4, 'ldconcept')
	neconcept_id, neconcept, neconcept_weights=getConcepts(neconcept_weight_file, beta5, 'neconcept')

	index = {};	 sentence_concepts = {};
	if alpha>0:
		index, sentence_concepts=getSentencesWithConcepts(concepts_in_sentence_file, 'concept', concept_id)

	depindex = {};	sentence_depconcepts = {}
	if beta1>0:
		depindex, sentence_depconcepts=getSentencesWithConcepts(depconcepts_in_sentence_file, 'depconcept', depconcept_id)
	semindex = {};	sentence_semconcepts = {}
	if beta2>0:
		semindex, sentence_semconcepts=getSentencesWithConcepts(semconcepts_in_sentence_file, 'semconcept', semconcept_id)
	psemindex = {};	sentence_psemconcepts = {}
	if beta3>0:
		psemindex, sentence_psemconcepts=getSentencesWithConcepts(psemconcepts_in_sentence_file, 'psemconcept', psemconcept_id)
	ldindex = {};	sentence_ldconcepts = {}
	if beta4>0:
		ldindex, sentence_ldconcepts=getSentencesWithConcepts(ldconcepts_in_sentence_file, 'ldconcept', ldconcept_id)
	neindex = {};	sentence_neconcepts = {}
	if beta5>0:
		neindex, sentence_neconcepts=getSentencesWithConcepts(neconcepts_in_sentence_file, 'neconcept', neconcept_id)
#	print neindex
#	print nesentence_concepts

	# build objective
	objective = []
	if alpha>0:
		for concept, weight in concept_weights.items():
			if concept not in index: continue # skip unused concepts
			objective.append("%+g c%d" % (alpha*weight, concept))
			solver.binary["c%d" % concept] = concept
	if beta1>0:
		for depconcept, weight in depconcept_weights.items():
			if depconcept not in depindex: continue # skip unused concepts
			objective.append("%+g k%d" % (beta1*weight, depconcept))
			solver.binary["k%d" % depconcept] = depconcept
	if beta2>0:
		for semconcept, weight in semconcept_weights.items():
			if semconcept not in semindex: continue # skip unused concepts
			objective.append("%+g l%d" % (beta2*weight, semconcept))
			solver.binary["l%d" % semconcept] = semconcept
	if beta3>0:
		for psemconcept, weight in psemconcept_weights.items():
			if psemconcept not in psemindex: continue # skip unused concepts
			objective.append("%+g j%d" % (beta3*weight, psemconcept))
			solver.binary["j%d" % psemconcept] = psemconcept
	if beta4>0:
		for ldconcept, weight in ldconcept_weights.items():
			if ldconcept not in ldindex: continue # skip unused concepts
			objective.append("%+g h%d" % (beta4*weight, ldconcept))
			solver.binary["h%d" % ldconcept] = ldconcept
	if beta5>0:
		for neconcept, weight in neconcept_weights.items():
			if neconcept not in neindex: continue # skip unused concepts
			objective.append("%+g b%d" % (beta5*weight, neconcept))
			solver.binary["b%d" % neconcept] = neconcept
	solver.objective["score"] = " ".join(objective)[1:]

	# sentence => concepts
	for sentence, concepts in sentence_concepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, depconcepts in sentence_depconcepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, semconcepts in sentence_semconcepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, psemconcepts in sentence_psemconcepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, ldconcepts in sentence_ldconcepts.items():
		solver.binary["s%d" % sentence] = sentence
	for sentence, neconcepts in sentence_neconcepts.items():
		solver.binary["s%d" % sentence] = sentence

	# concept => sentence
	for concept in index:
		solver.constraints["index_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in index[concept]]) + " - c%d >= 0" % concept
	for depconcept in depindex:
		solver.constraints["depindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in depindex[depconcept]]) + " - k%d >= 0" % depconcept
	for semconcept in semindex:
		solver.constraints["semindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in semindex[semconcept]]) + " - l%d >= 0" % semconcept
	for psemconcept in psemindex:
		solver.constraints["psemindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in psemindex[psemconcept]]) + " - j%d >= 0" % semconcept
	for ldconcept in ldindex:
		solver.constraints["ldindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in ldindex[ldconcept]]) + " - h%d >= 0" % ldconcept
	for neconcept in neindex:
		solver.constraints["neindex_%d" % len(solver.constraints)] = " + ".join(["s%d" % x for x in neindex[neconcept]]) + " - b%d >= 0" % neconcept

	length_constraint = []
	sentence = 0
	for line in open(sentence_length_file):
		if sentence in sentence_concepts or (sentence in sentence_depconcepts) or (sentence in sentence_semconcepts)or (sentence in sentence_psemconcepts) or (sentence in sentence_ldconcepts)or (sentence in sentence_neconcepts):
			length = line.strip()
			length_constraint.append("%s s%d" % (length, sentence))
#			solver.objective["score"] += " - %g s%d" % (float(length) / 1000.0, sentence)
		sentence += 1

	solver.constraints["length_%d" % len(solver.constraints)] = " + ".join(length_constraint) + " <= " + str(max_length)

	if atleast != None:
		at_least = []
		sentence = 0
		for line in open(atleast):
			line = line.strip()
			if sentence in sentence_concepts or (sentence in sentence_depconcepts) or (sentence in sentence_semconcepts)or (sentence in sentence_psemconcepts) or (sentence in sentence_ldconcepts)or (sentence in sentence_neconcepts):
				if line == "1":
					at_least.append("s%d" % sentence)
			sentence += 1
		if len(at_least) > 0:
			solver.constraints["at_least_%d" % len(solver.constraints)] = " + ".join(at_least) + " >= 1" # select at least one of those

	sys.stderr.write("ilp: %d sentences, %d concepts\n" % (len(sentence_concepts)+len(sentence_depconcepts)+len(sentence_semconcepts)+len(sentence_psemconcepts)+len(sentence_ldconcepts)+len(sentence_neconcepts), len(index)+len(depindex)+len(semindex)+len(psemindex)+len(ldindex)+len(neindex)))

	if len(sentence_concepts)+len(sentence_depconcepts)+len(sentence_semconcepts)+len(sentence_psemconcepts)+len(sentence_ldconcepts)+len(sentence_neconcepts) > 0 and len(index)+len(depindex)+len(semindex)+len(psemindex)+len(ldindex)+len(neindex) > 0:
		solver.run_gurobi()
	output = []
	for variable in solver.output:
		if variable.startswith("s") and solver.output[variable] == 1:
			output.append(int(variable[1:]))
	return output

	
if __name__ == '__main__':
	if len(sys.argv) < 5 or len(sys.argv) > 8:
		sys.stderr.write('USAGE: %s <length_constraint> <sentence_lengths> <concepts_in_sentences> <concept_weights> [sentence_groups] [dependencies] [atleast]\n')
		sys.exit(1)
	sentence_groups = None
	dependencies = None
	atleast = None
	if len(sys.argv) > 5:
		sentence_groups = sys.argv[5]
	if len(sys.argv) > 6:
		dependencies = sys.argv[6]
	if len(sys.argv) > 7:
		atleast = sys.argv[7]
	output = decode(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sentence_groups, dependencies, atleast)
	for value in output:
		print value
	

