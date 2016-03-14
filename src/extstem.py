import argparse
from nltk.stem.snowball import SnowballStemmer

parser = argparse.ArgumentParser(description="""Wordwise stemmer""")
parser.add_argument('word',)
parser.add_argument('--language', help="language", default='french')
args = parser.parse_args()

stmr = SnowballStemmer(args.language)
print(stmr.stem(args.word))