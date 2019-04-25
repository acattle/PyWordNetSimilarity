'''
    Created on Sep 19, 2017
    
    :author: Andrew Cattle <acattle@connect.ust.hk>
    
    This module implements the Extended Lesk algorithm described in [1].
    
    This code is heavily based on  similarity/lesk.pm module from the Perl
    WordNet::Similarity library created by Ted Pedersen, Siddharth Patwardhan,
    Satanjeev Banerjee, and Jason Michelizzi.
    
    
    [1]    Banerjee, S., & Pedersen, T. (2002, February). An adapted Lesk
    algorithm for word sense disambiguation using WordNet. In International
    Conference on Intelligent Text Processing and Computational Linguistics
    (pp. 136-145). Springer, Berlin, Heidelberg.
'''

from __future__ import print_function #for Python 2.7 compatibility
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords as sw
from wordnet_similarity_dat_reader import read_relation_file
from uuid import uuid4
import difflib
import re

space_pat = re.compile(" ")

class ExtendedLesk:
    
    def __init__(self, relations_loc, stopwords=None):
        """
            Initialize the Extended Lesk algorithm
            
            :param relations_loc: the location of a WordNet::Similarity relations file
            :type relations_loc: str
            :param stopwords: set of stopwords to be excluded from beginning/end of overlaps. If None, NLTK English stopwords are used.
            :type stopwords: list(str)
            :param cache: whether results should be cached
            :type cache: bool
        """
        #TODO: make relations optional
        self.relations = read_relation_file(relations_loc)
        if stopwords == None:
            self.stopwords = set(sw.words("english"))
        else:
            self.stopwords = set(stopwords) #casting to set improves membership checking performance
    
    def _getLeadingStopwordCount(self, text):
        """
            Compute the number of leading stopwords
            
            :param text: the text to check for leading stopwords as a list of tokens
            :type text: list(str)
            
            :return: the number of stopwords at the beginning of text
            :rtype: int
        """
        
        stopword_count = 0
        for token in text:
            if token in self.stopwords:
                #stopword found. Add it to the count.
                stopword_count = stopword_count + 1
            else:
                #first non-stopword reached. Stop checking.
                break
        
        return stopword_count
    
    def _lengthWithoutStopwords(self, matched_text):
        """
            Computes the match length excluding leading and/or trailing
            stopwords
            
            :param matched_text: the overlapping text as a list of tokens
            :type matched_text: list(str)
            
            :return: the match length excluding leading and trailing stopwords
            :rtype: int
        """
        
        match_length = len(matched_text)
        
        #remove leading stopwords from length
        match_length = match_length - self._getLeadingStopwordCount(matched_text)
        
        #only continue is we haven't already seen every token
        if match_length > 0:
            #remove trailing stopwords from length
            match_length = match_length - self._getLeadingStopwordCount(reversed(matched_text))
        
        return match_length
    
    def getTextOverlapScore(self, text_a, text_b):
        """
            Computes the overlap score between two texts represented as lists of
            tokens.
            
            :param text_a: the first text as a list of tokens
            :type text_a: list(str)
            :param text_b: the second text as lists of tokens
            :type text_b: list(str)
            
            :return: A relatedness score which is greater-than or equal-to 0
            :rtype: int
        """
        #TODO: Omit stopwords? Shorter docs mean faster comparisons
        text_a = list(text_a) #to avoid accidentally editing the list in place
        text_b = list(text_b)
        
        sm = difflib.SequenceMatcher(None, text_a, text_b, autojunk=False)
        
        score = 0
        match_found = True
        while match_found:
            a_start, b_start, length = sm.find_longest_match(0, len(text_a), 0, len(text_b))
            
            if length > 0:
                #Remove leading/trailing stopwords as per Extended Lesk algorithm
                length_without_stopwords = self._lengthWithoutStopwords(text_a[a_start:a_start+length])
                
                #match score = (match length)^2 as per Extended Lesk algorithm
                score = score + length_without_stopwords**2
                
                #replace the match in both text_a and text_b with unique separators to prevent matching across this boundary again
                text_a[a_start:a_start+length] = [int(uuid4())] #casting uuid to int causes a slight speedup
                text_b[b_start:b_start+length] = [int(uuid4())]
                #replacing a slice with an iterable is more efficient than using list concatenation
                #https://stackoverflow.com/questions/12088089/python-list-concatenation-efficiency
                
                #update the sequence matcher
                sm = difflib.SequenceMatcher(None, text_a, text_b, autojunk=False)
                #Previously we used sm.set_seqs() but this caused an issue with the more efficient list alteration
                #where SequenceMatcher's cache wasn't updating
            else:
                #match length 0. No more matches
                match_found = False  
        
        return score
    
    def getSynsetRelatedness(self, synsets_a, synsets_b):
        """
            Compute the Extended Lesk relatedness between two groups of synsets
            
            :param synsets_a: the first group of synsets to be considered
            :type synsets_a: list(nltk.cropus.wordnet.Synset)
            :param synsets_b: the second group of synsets to be considered
            :type synsets_b: list(nltk.cropus.wordnet.Synset)
            
            :return: Extended Lesk relatedness score
            :rtype: flaot
        """
        relatedness_score = 0
        
        for a_funcs, b_funcs, weight in self.relations:
            text_a = synsets_a            
            #apply the relevant functions to the first group of synsets
            for a_func in a_funcs:
                text_a = a_func(text_a)
            
            text_b = synsets_b
            #apply the relevant functions to the second group of synsets
            for b_func in b_funcs:
                text_b = b_func(text_b)
                
            #get the overlap between text_a and text_b and update the relatedness score accordingly
            overlap_score = self.getTextOverlapScore(text_a, text_b)
            relatedness_score = relatedness_score + overlap_score*weight
        
        return relatedness_score
    
    def getWordRelatedness(self, word_a, word_b):
        """
            Compute the Extended Lesk relatedness between two ambiguous words
            
            :param synsets_a: the first word
            :type synsets_a: str
            :param synsets_b: the second word
            :type synsets_b: str
            
            :return: Extended Lesk relatedness score
            :rtype: flaot
        """
        
        synsets_a = wn.synsets(space_pat.sub("_", word_a))
        synsets_b = wn.synsets(space_pat.sub("_", word_b))
        
        return self.getSynsetRelatedness(synsets_a, synsets_b)
            
        
if __name__ == '__main__':
    import pickle
    import timeit

    relations_file = "lesk-relation.dat"
    
    with open("d:/git/HumourDetection/HumourDetection/src/word_associations/features/usf/word_pairs.pkl", "rb") as wp_file:
        wp = pickle.load(wp_file, encoding="latin1")
    wn.ensure_loaded()
    print ("starting")
#     el = ExtendedLesk(relations_file)
#     print(timeit.timeit("[el.getWordRelatedness(a, b) for a,b in wp[:10]]", "from __main__ import wp,el"))
    el = ExtendedLesk(relations_file, cache=False)
    print(el.getWordRelatedness("car", "bus"))
#     print(timeit.timeit("[el.getWordRelatedness(a, b) for a,b in wp[:10]]", "from __main__ import wp,el", number=100))
    print(timeit.timeit("el.getWordRelatedness('car','bus')", "from __main__ import wp,el", number=1000))
    
#     for a,b in wp[:100]:
#         print("{}-{}: {}".format(a,b,el.getWordRelatedness(a, b)))