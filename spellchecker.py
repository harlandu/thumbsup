"""Spellchecker based on the checker written by peter norvig.
See http://norvig.com/spell-correct.html
"""

import re, collections

import config

def words(text): return re.findall('[a-z]+', text.lower()) 

DICTIONARY = set(words(file(config.SPELLCHECKER_TEXT).read()))

alphabet = 'abcdefghijklmnopqrstuvwxyz'

def edits1(word):
   splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in alphabet if b]
   inserts    = [a + c + b     for a, b in splits for c in alphabet]
   return set(deletes + transposes + replaces + inserts)

def known_edits2(word):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in DICTIONARY)

# Typo helper function
def is_typo(word):
	'''A word is considered a typo whenever it not in the
	dictionary AND another word that is at edit-distance of 2 or
	less is in the dictionary.'''
	if not word in DICTIONARY and known_edits2(word):
		return True
	return False
