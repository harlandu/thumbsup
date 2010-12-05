import random
import unittest

from review_features import *
from util import anew_scoring

test_review = {}
test_review2 = {}
# review with 6 typos.
test_review['text'] = '''Brand new owner, brand new wine lis, brand
new feeel. GO check it out at http://www.iloveboobs.com ! Have the cheeze appetizer. i forjet what
it's callede. But it was AMAZING! give it a try and I promese you WILL
be BACK. '''

test_review2['text'] = '''I initially purchased the Navigon top of the line unit.  It was cool, but a little sluggish and the buttons did not work as well.  This device is much faster, more intuitive to use and has a great display.  I love it. I even take it with me on walks with my son - put the GPS on the stroller and it tracks my MPH, total time traveled, stopped etc...  It was definitely expensive, but I love it!'''

class FeaturesTests(unittest.TestCase):

    def test_is_typo(self):
        # edit distance 1
        assert is_typo('speling') == True # delete
        assert is_typo('spelilng') == True # swap
        assert is_typo('spellling') == True # insert
        assert is_typo('spellimg') == True # replace
        # edit distance 2
        assert is_typo('speing') == True # delete
        assert is_typo('spelilgn') == True # swap
        assert is_typo('spelllling') == True # insert
        assert is_typo('sbellimg') == True # replace
        # edit distance 3 or more - false
        assert is_typo('spelling') == False    # correct
        assert is_typo('pselilgn') == False # swap
        assert is_typo('spellllling') == False # insert
        assert is_typo('zbellimg') == False # replace

    def test_fill_review_typos(self):
        fill_review_typos(test_review)
        assert test_review['feature_typos'] == 6

    def test_fill_price_range(self):
        # numbers from the data
        price_categories = [(28830, 0.2), (43, 0.5), (2, 0.9), (1, 1.0)]
        for pid, cat in price_categories:
            review = {'product_id':pid}
            fill_price_range(review)
            assert review['feature_price_range'] == cat

    def test_fill_num_urls(self):
        fill_num_urls(test_review)
        assert test_review['num_urls'] == 1
        
    def test_fill_all_caps(self):
        fill_word_count(test_review)
        fill_all_caps_words(test_review)
        assert test_review['feature_all_caps'] == 4.0/test_review['word_count']

    def test_word_count(self):
        fill_word_count(test_review)
        assert test_review['word_count'] == 44

    def test_fill_capitalization_errors(self):
        fill_word_count(test_review)
        fill_capitalization_errors(test_review)
        assert test_review['feature_caps_err'] == 2.0/test_review['word_count']
    
    def test_anew_scoring(self):
        fill_valence_score(test_review)
        fill_arousal_score(test_review)
        fill_dominance_score(test_review)
        # The test review contains only one valence word
        print test_review['feature_valence_score']
        print test_review['feature_arousal_score']
        print test_review['feature_dominance_score']
        assert test_review['feature_valence_score'] > 0.8
        assert test_review['feature_arousal_score'] > 0.87
        assert test_review['feature_dominance_score'] > 0.96

    def test_error_using_word(self):
        fill_writing_errors_using_word(test_review2)

class LoaderTests(unittest.TestCase):

    def test_load_products(self):
        '''Assumes amazon data for now'''
        load_az_products()
        assert AZ_PRODUCTS
        for key in AZ_PRODUCTS.iterkeys():
            assert type(key) == int
            assert type(AZ_PRODUCTS[key]['amazonprice']) == float 

if __name__ == '__main__':
    unittest.main()
