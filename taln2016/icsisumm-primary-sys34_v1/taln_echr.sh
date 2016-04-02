#!/bin/bash 

SCORES=taln2016/scores
ROUGEINST=/home/natschluter/eval_software/ROUGE-1.5.5/ROUGE-1.5.5.pl
export PATH=solver/glpk-4.43/examples/:$PATH
export HOSTNAME=localhost
TIMELIMIT=300

#echr
DOCSDIR=/coastal/summ_data/echr_data_clean/test/text_docs/
REFDIR=/coastal/summ_data/echr_data_clean/test/text_sums/
DTYPE=echr
LENGTH=805

echo "INPUTDIR "$INPUTDIR
echo "DTYPE "$DTYPE
echo $LENGTH

OUTPUTDIR=taln2016/echr_unigrams/test/
if [ ! -d "$OUTPUTDIR" ]; then
mkdir -p $OUTPUTDIR
fi

python -u summarizer_fr/inference_taln2016.py -l $LENGTH -i $DOCSDIR -o $OUTPUTDIR -t $DTYPE --manpath $REFDIR --decoder glpsolve --timelimit $TIMELIMIT --unigrams --lang en
python -u eval_taln.py r1_$DTYPE $OUTPUTDIR'summary/' $LENGTH $SCORES $REFDIR $DTYPE

OUTPUTDIR=taln2016/echr_bigrams/test/
if [ ! -d "$OUTPUTDIR" ]; then
mkdir -p $OUTPUTDIR
fi

python -u summarizer_fr/inference_taln2016.py -l $LENGTH -i $DOCSDIR -o $OUTPUTDIR -t $DTYPE --manpath $REFDIR --decoder glpsolve --timelimit $TIMELIMIT --bigrams --lang en
python -u eval_taln.py r2_$DTYPE $OUTPUTDIR'summary/' $LENGTH $SCORES $REFDIR $DTYPE

OUTPUTDIR=taln2016/echr_fourgrams/test/
if [ ! -d "$OUTPUTDIR" ]; then
mkdir -p $OUTPUTDIR
fi

python -u summarizer_fr/inference_taln2016.py -l $LENGTH -i $DOCSDIR -o $OUTPUTDIR -t $DTYPE --manpath $REFDIR --decoder glpsolve --timelimit $TIMELIMIT --fourgrams --lang en
python -u eval_taln.py r4_$DTYPE $OUTPUTDIR'summary/' $LENGTH $SCORES $REFDIR $DTYPE

OUTPUTDIR=taln2016/echr_su4/test/
if [ ! -d "$OUTPUTDIR" ]; then
mkdir -p $OUTPUTDIR
fi

python -u summarizer_fr/inference_taln2016.py -l $LENGTH -i $DOCSDIR -o $OUTPUTDIR -t $DTYPE --manpath $REFDIR --decoder glpsolve --timelimit $TIMELIMIT --su4 --lang en
python -u eval_taln.py su4_$DTYPE $OUTPUTDIR'summary/' $LENGTH $SCORES $REFDIR $DTYPE

