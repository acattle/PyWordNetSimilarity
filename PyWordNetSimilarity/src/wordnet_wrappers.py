'''
    Created on Nov 23, 2017
    
    :author: Andrew Cattle <acattle@connect.ust.hk>
    
    Wrappers for nltk.corpus.wordnet functions to ensure proper format for
    difflib.SequenceMatcher
'''

#Avoiding using list.extend() and instead using += results in a slight speed increase
#Same is not true for list.append()
#Similarly, casting uuids to int seems to speed things up a small amount too

from uuid import uuid4
from functools import lru_cache


######################### Caching function wrappers ##########################

_cache_size = None #Max size of LRU cache. None means no limit

@lru_cache(maxsize=_cache_size)
def _get_lemmas(synset):
    """
    Wrapper function for caching NLTK's Synset.lemma()
    """
    return synset.lemmas()

@lru_cache(maxsize=_cache_size)
def _get_lemma_names(synset):
    """
    Method for getting list of lemma names.
    
    Note that this method does not insert UUIDs between lemma names because
    the UUIDs would be cached, leading to false matches.
    """
    return [l.name().lower() for l in _get_lemmas(synset)]

@lru_cache(maxsize=_cache_size)
def _get_also_sees(synset):
    """
    Wrapper method for caching NLTK's Synset.also_sees() and
    Lemma.also_sees()
    """
    return synset.also_sees()

@lru_cache(maxsize=_cache_size)
def _get_hypernyms(synset):
    """
    Wrapper method for caching NLTK's Synset.hypernyms() and
    Synset.instance_hypernyms()
    """
    return synset.hypernyms() + synset.instance_hypernyms()

@lru_cache(maxsize=_cache_size)
def _get_hyponyms(synset):
    """
    Wrapper method for caching NLTK's Synset.hyponyms()
    """
    return synset.hyponyms() + synset.instance_hyponyms()

@lru_cache(maxsize=_cache_size)
def _get_holonyms(synset):
    """
    Wrapper method for caching NLTK's Synset.member_holonyms(),
    Synset.part_holonyms(), and Synset.substance_holonyms()
    """
    return synset.member_holonyms() + synset.part_holonyms() + synset.substance_holonyms()

@lru_cache(maxsize=_cache_size)
def _get_meronyms(synset):
    """
    Wrapper method for caching NLTK's Synset.member_meronyms(),
    Synset.part_meronyms(), and Synset.substance_meronyms()
    """
    return synset.member_meronyms() + synset.part_meronyms() + synset.substance_meronyms()

@lru_cache(maxsize=_cache_size)
def _get_attributes(synset):
    """
    Wrapper method for caching NLTK's Synset.attributes()
    """
    return synset.attributes()

@lru_cache(maxsize=_cache_size)
def _get_similar_tos(synset):
    """
    Wrapper method for caching NLTK's Synset.similar_tos()
    """
    return synset.attributes()

@lru_cache(maxsize=_cache_size)
def _get_pertainyms(synset):
    """
    Wrapper method for caching NLTK's Lemma.pertainyms()
    """
    return [pertainym.synset() for lemma in _get_lemmas(synset) for pertainym in lemma.pertainyms()]





######################### WordNet Functions #############################

def concat_definitions(synsets):
    '''
        Takes a list of synsets and combines their definitions into a single
        list suitable for passing to difflib.SequenceMatcher
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets definitions as a list of individual words
        :rtype: list(str)
    '''
    
    definition_words=[]
    
    for i, synset in enumerate(synsets):        
        #unless this is the first definition, insert a unique separator between definitions
        #since definitions are in an arbitrary order, we want to prevent matching across definition boundaries
        if i > 0:
            definition_words.append(int(uuid4()))
        
        definition = synset.definition().lower()
        definition_words += definition.split()
    
    return definition_words
        
def concat_examples(synsets):
    '''
        Takes a list of synsets and combines their examples into a single list
        suitable for passing to difflib.SequenceMatcher
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets examples as a list of individual words
        :rtype: list(str)
    '''
    
    example_words=[]
    
    for i, synset in enumerate(synsets):
        for j, example in enumerate(synset.examples()):
            example = example.lower()
        
            #unless this is the first example, insert a unique separator between definitions
            #since examples are in an arbitrary order, we want to prevent matching across example boundaries
            if (i+j) > 0:
                example_words.append(int(uuid4()))
            
            example_words += example.split()
    
    return example_words

def concat_lemmas(synsets):
    '''
        Takes a list of synsets and combines their lemmas into a single list
        suitable for passing to difflib.SequenceMatcher
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets lemmas as a list of individual words
        :rtype: list(str)
    '''
    
    lemmas=[]
    
    for i, synset in enumerate(synsets):
        for j, lemma_name in enumerate(_get_lemma_names(synset)):
        
            #unless this is the first lemma, insert a unique separator between definitions
            #since lemmas are in an arbitrary order, we want to prevent matching multiple lemmas at a time
            if (i+j) > 0:
                lemmas.append(int(uuid4()))
            
            #splitting the lemma names by "_" helps when matching lemmas against examples or definitions
            lemmas += lemma_name.split("_")
    
    return lemmas

def get_also_sees(synsets):
    '''
        Takes a list of synsets, finds all their also_sees, and returns them as
        a list of Synsets
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets' also_sees' definitions as a list of individual words
        :rtype: list(nltk.corpus.wordnet.Synset)
    '''
    
    #WordNet::Similarity's "also" is inconsistent
    #It returns the also_sees from breathe.v.01's lemmas
    #but it doesn't return the also_sees from refresh.v.04's
    #For simplicity, we return all also_sees whether they're from synsets or the synsets' lemmas
    
    also_sees=[] #TODO: should I use a set to avoid repeat definitions?
    
    for synset in synsets:
        #add synset-level also_sees
        also_sees += _get_also_sees(synset)
        
        #add lemma-level also_sees
        for lemma in _get_lemmas(synset):
            for also_see in _get_also_sees(lemma):
                also_sees.append(also_see.synset())
    
    return also_sees

def get_hypernyms(synsets):
    '''
        Takes a list of synsets, finds all their hypernnyms, and returns them as
        a list of Synsets
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets' hypernyms' definitions as a list of individual words
        :rtype: list(nltk.corpus.wordnet.Synset)
    '''
    
    hypernyms=[] #TODO: should I use a set to avoid repeat definitions?
    for synset in synsets:
        #Perl library WordNet::Similarity doesn't seem to differentiate hypernyms and instance_hypernyms. Neither should we.
        hypernyms += _get_hypernyms(synset)
    return hypernyms

def get_hyponyms(synsets):
    '''
        Takes a list of synsets, finds all their hyponnyms, and returns them as
        a list of Synsets
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets' hyponyms' definitions as a list of individual words
        :rtype: list(nltk.corpus.wordnet.Synset)
    '''
    
    hyponyms=[] #TODO: should I use a set to avoid repeat definitions?
    for synset in synsets:
        #Perl library WordNet::Similarity doesn't seem to differentiate hyponyms and instance_hyponyms. Neither should we.
        hyponyms += _get_hyponyms(synset)
    return hyponyms

def get_holonyms(synsets):
    '''
        Takes a list of synsets, finds all their holonyms, and returns them as
        a list of Synsets
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets' holonyms' definitions as a list of individual words
        :rtype: list(nltk.corpus.wordnet.Synset)
    '''
    
    holonyms=[] #TODO: should I use a set to avoid repeat definitions?
    #Perl library WordNet::Similarity doesn't seem to differentiate member_holonyms, part_holonyms, and substance_holonyms. Neither should we.
    for synset in synsets:
        #Perl library WordNet::Similarity doesn't seem to differentiate member_holonyms, part_holonyms, and substance_holonyms. Neither should we.
        holonyms += _get_holonyms(synset)
    
    return holonyms

def get_meronyms(synsets):
    '''
        Takes a list of synsets, finds all their meronyms, and returns them as 
        a list of Synsets
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets' meronyms' definitions as a list of individual words
        :rtype: list(nltk.corpus.wordnet.Synset)
    '''
    
    meronyms=[] #TODO: should I use a set to avoid repeat definitions?
    
    for synset in synsets:
        #Perl library WordNet::Similarity doesn't seem to differentiate member_meronyms, part_meronyms, and substance_meronyms. Neither should we.
        meronyms += _get_meronyms(synset)

    return meronyms

def get_attributes(synsets):
    '''
        Takes a list of synsets, finds all their attributes,
        and returns them as a list of Synsets
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets' attributes' definitions as a list of individual words
        :rtype: list(nltk.corpus.wordnet.Synset)
    '''
    
    attributes=[] #TODO: should I use a set to avoid repeat definitions?
    
    for synset in synsets:
        attributes += _get_attributes(synset)
    
    return attributes

def get_similar_tos(synsets):
    '''
        Takes a list of synsets, finds all their similar_tos, and returns them
        as a list of Synsets
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets' similar_tos' definitions as a list of individual words
        :rtype: list(nltk.corpus.wordnet.Synset)
    '''
    
    similar_tos=[] #TODO: should I use a set to avoid repeat definitions?
    
    for synset in synsets:
        similar_tos += _get_similar_tos(synset)
    
    return similar_tos

def get_pertainyms(synsets):
    '''
        Takes a list of synsets, finds all their pertainyms, and returns them
        as a list of Synsets
        
        :param synsets: list of synsets to concatenate
        :type synsets: iterable(nltk.corpus.wordnet.Synset)
        
        :return: all synsets' pertainyms' definitions as a list of individual words
        :rtype: list(nltk.corpus.wordnet.Synset)
    '''
    
    #TODO: hardly.r.02 doesn't return any pertainyms in WQordNet::Similarity despite them being in NLTK
    
    pertainyms=[] #TODO: should I use a set to avoid repeat definitions?
    for synset in synsets:
        pertainyms += _get_pertainyms(synset)
    
    return pertainyms