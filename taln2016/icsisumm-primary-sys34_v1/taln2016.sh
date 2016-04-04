#!/bin/bash 

SCORES=taln2016/scores
ROUGEINST=/home/natschluter/eval_software/ROUGE-1.5.5/ROUGE-1.5.5.pl
export PATH=solver/glpk-4.43/examples/:$PATH
export HOSTNAME=localhost
TIMELIMIT=100

##########################################################DUC04
#DOCSDIR=/coastal/summ_data/DUC2004/duc04/docs/
#REFDIR=/coastal/summ_data/DUC2004/duc04/sums/

DOCSDIR=/home/alonso/proj/rougexstem/Corpus_RPM2_resumes/Corpus_RPM2_documents/test/
REFDIR=/home/alonso/proj/rougexstem/Corpus_RPM2_resumes/Corpus_RPM2_references/test/
DTYPE=duc04
LENGTH=665
echo "INPUTDIR "$INPUTDIR
echo "DTYPE "$DTYPE
echo $LENGTH

OUTPUTDIR=taln2016/duc04_words/test/
if [ ! -d "$OUTPUTDIR" ]; then
mkdir -p $OUTPUTDIR
fi

python -u summarizer/inference_taln2016.py -l $LENGTH -i $DOCSDIR -o $OUTPUTDIR -t $DTYPE --manpath $REFDIR --decoder glpsolve --timelimit $TIMELIMIT --unigrams --lang en
python -u eval_taln.py r1_$DTYPE $OUTPUTDIR'summary/' $LENGTH $SCORES $REFDIR $DTYPE


OUTPUTDIR=taln2016/duc04_bigrams/test/
if [ ! -d "$OUTPUTDIR" ]; then
mkdir -p $OUTPUTDIR
fi

python -u summarizer/inference_taln2016.py -l $LENGTH -i $DOCSDIR -o $OUTPUTDIR -t $DTYPE --manpath $REFDIR --decoder glpsolve --timelimit $TIMELIMIT --bigrams --lang en
python -u eval_taln.py r2_$DTYPE $OUTPUTDIR'summary/' $LENGTH $SCORES $REFDIR $DTYPE

#OUTPUTDIR=taln2016/duc04_fourgrams/test/
#if [ ! -d "$OUTPUTDIR" ]; then
#mkdir -p $OUTPUTDIR
#fi

#python -u summarizer/inference_taln2016.py -b $LENGTH -i $DOCSDIR -o $OUTPUTDIR -t $DTYPE --manpath $REFDIR --decoder glpsolve --timelimit $TIMELIMIT --fourgrams --lang en
#python -u eval_taln.py r4_$DTYPE $OUTPUTDIR'summary/' $LENGTH $SCORES $REFDIR $DTYPE

#OUTPUTDIR=taln2016/duc04_su4/test/
#if [ ! -d "$OUTPUTDIR" ]; then
#mkdir -p $OUTPUTDIR
#fi

#python -u summarizer/inference_taln2016.py -b $LENGTH -i $DOCSDIR -o $OUTPUTDIR -t $DTYPE --manpath $REFDIR --decoder glpsolve --timelimit $TIMELIMIT --su4 --lang en
#python -u eval_taln.py su4_$DTYPE $OUTPUTDIR'summary/' $LENGTH $SCORES $REFDIR $DTYPE

