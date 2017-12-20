'''
Created on Nov 27, 2017

:author: Andrew Cattle <acattle@cse.ust.hk>
'''
from wordnet_wrappers import get_also_sees, get_attributes, concat_examples,\
    concat_definitions, get_hypernyms, get_holonyms, get_meronyms,\
    get_pertainyms, get_similar_tos, concat_lemmas

WORDNET_SIM_FUNC_MAP = {"also" : get_also_sees,
                         "attr" : get_attributes,
                         "example" : concat_examples,
                         "glos" : concat_definitions,
                         "holo" : get_holonyms,
                         "hype" : get_hypernyms,
                         "hypo" : get_holonyms,
                         "mero" : get_meronyms,
                         "pert" : get_pertainyms,
                         "sim" : get_similar_tos,
                         "syns" : concat_lemmas
                         }

def read_relation_file(file_loc):
    '''
        Utility method for reading WordNet::Similarity relation
        files and using them with this library.
        
        see: http://search.cpan.org/dist/WordNet-Similarity/lib/WordNet/Similarity/extended_lesk.pm#RELATION_FILE_FORMAT
        
        :param file_loc: the location of the relation file to be read
        :type relation_loc: str
        
        :returns: relation chains to be compared
        :rtype: tuple(tuple(func), tuple(func), float)
        
        :raises: ValueError
    '''
    
    with open(file_loc, "r") as relation_file:
        header = relation_file.readline()
        
        if header.strip() != "RelationFile":
            #Wordnet::Similarity requires the first line of any relation file to contain the header "RelationFile": http://search.cpan.org/dist/WordNet-Similarity/lib/WordNet/Similarity/extended_lesk.pm#RELATION_FILE_FORMAT
            raise ValueError("Relation file does is not in WordNet::Similarity format; Missing header.\n{}\n\nPlease see http://search.cpan.org/dist/WordNet-Similarity/lib/WordNet/Similarity/extended_lesk.pm#RELATION_FILE_FORMAT".format(file_loc)) #TODO: is ValueError the appropriate exception?
        
        relations = []
        for line in relation_file:
            line = line.lower() #avoids KeyErrors when looking up functions in WORDNET_SIM_FUNC_MAP
            
            #separate the functions used on synset A from those used on synset B
            try:
                a_func_str, b_func_str = line.split("-")
            except ValueError as e:
                raise ValueError("Relation file does is not in WordNet::Similarity format; line '{}' improperly formatted.\n{}\n\nPlease see http://search.cpan.org/dist/WordNet-Similarity/lib/WordNet/Similarity/extended_lesk.pm#RELATION_FILE_FORMAT\n\n{}".format(line, file_loc, str(e))) #TODO: is ValueError the appropriate exception?
                
            #get optional weight value
            weight = 1
            b_func_str_split = b_func_str.split()
            if len(b_func_str_split) == 2: #if there are exactly 2 arguments
                b_func_str, weight_str = b_func_str_split
                
                try:
                    weight=float(weight_str)
                except ValueError:
                    #weight_str cannot be converted to float
                    raise ValueError("Relation file does is not in WordNet::Similarity format; line '{}' contains invalid weight.\n{}\n\nPlease see http://search.cpan.org/dist/WordNet-Similarity/lib/WordNet/Similarity/extended_lesk.pm#RELATION_FILE_FORMAT".format(line, file_loc)) #TODO: is ValueError the appropriate exception?
            
            #break into individual function names
            a_func_strs = a_func_str.split("(")
            b_func_strs = b_func_str.strip().split("(") #strip to to get rid of trailing '\n'
            
            #remove trailing brackets if necessary
            a_num_brackets = len(a_func_strs)-1 #number of brackets is equal to number of splits
            a_trailing_brackets = ""
            if a_num_brackets > 0:
                a_trailing_brackets = a_func_strs[-1][-a_num_brackets:]
                a_func_strs[-1] = a_func_strs[-1][:-a_num_brackets]
            b_num_brackets = len(b_func_strs)-1
            b_trailing_brackets = ""
            if b_num_brackets > 0:
                b_trailing_brackets = b_func_strs[-1][-b_num_brackets:]
                b_func_strs[-1] = b_func_strs[-1][:-b_num_brackets]
            
            #check that we really did remove only trailing brackets
            if (a_trailing_brackets != ")"*a_num_brackets) or (b_trailing_brackets != ")"*b_num_brackets):
                raise ValueError("Relation file does is not in WordNet::Similarity format; line '{}' does not contain properly formated functions.\n{}\n\nPlease see http://search.cpan.org/dist/WordNet-Similarity/lib/WordNet/Similarity/extended_lesk.pm#RELATION_FILE_FORMAT".format(line, file_loc)) #TODO: is ValueError the appropriate exception
            
            #convert from WordNet::Similarity function names to our functions
            a_funcs = []
            b_funcs = []
            try:
                for a_func in a_func_strs:
                    #push the relevant WordNet Wrapper function into the chain
                    a_funcs.append(WORDNET_SIM_FUNC_MAP[a_func])
                
                for b_func in b_func_strs:
                    #push the relevant WordNet Wrapper function into the chain
                    b_funcs.append(WORDNET_SIM_FUNC_MAP[b_func])
            except KeyError as e:
                raise ValueError("Relation file does is not in WordNet::Similarity format; line '{}' contains an unknown function.\n{}\n\nPlease see http://search.cpan.org/dist/WordNet-Similarity/lib/WordNet/Similarity/extended_lesk.pm#RELATION_FILE_FORMAT\n\n{}".format(line, file_loc, str(e))) #TODO: is ValueError the appropriate exception?
            
            #check if the final function returns a list of synsets
            if a_func_strs[-1].lower() not in ("glos", "example", "syns"):
                #add a "glos" on the end
                a_funcs.append(concat_definitions)
            if b_func_strs[-1].lower() not in ("glos", "example", "syns"):
                b_funcs.append(concat_definitions)
                
            #add to the list of relation comparisons to make
            relations.append((tuple(a_funcs), tuple(b_funcs), weight)) #cast to tuple to make function chains immutable
    
    return tuple(relations)