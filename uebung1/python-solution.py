#>>> imports <<<
import sys
import os
import bisect
import string

#******* variables *********
filename = "" 
dictionary = {}
chars_to_remove = ''.join(string.punctuation.join('#')) #[',', '!', '?','#', '"','_','.', '-', '@']
postings = []

#******* functions *********

def bi_contains(lst, item):
    """ efficient `item in lst` for sorted lists """
    # if item is larger than the last it's not in the list, but the bisect would 
    # find `len(lst)` as the index to insert, so check that first. Else, if the 
    # item is in the list then it has to be at index bisect_left(lst, item)
    return (item <= lst[-1]) and (lst[bisect.bisect_left(lst, item)] == item)
#end of bi_contains

def get_postings_list(pointer):
	return postings[pointer]

def normalize_term(term):
	# normalize by switching to lowercase and removing ?!,"# [NEWLINE]
	# using translate which takes characters as parameters and removes them more effiecintly than a normal replace.
	# replace is used for [newline] since we need to match a string and translate only accepts characters.
	return term.lower().translate(None, chars_to_remove).replace("[newline]","")
		
def index(filename):
	#loop through lines in the file
	with open(filename, 'r') as input_file:
		for line in input_file:
			current_doc = line.split("\t")
			if len(current_doc) < 5:
				print (line)
				continue #skip tweets where the text is not in the 5th column
			doc_tokens = current_doc[4].split() #5th column is the text, split on white space
			for token in  doc_tokens:
				#normalize by switching to lowercase and removing ?!,"# [NEWLINE]
				term = normalize_term(token)
				docID = long(current_doc[1])
				if (term != "" and term in dictionary):
					# term exists, update postings list
					term_postings_list = get_postings_list(dictionary[term][0])
					if not bi_contains(term_postings_list, docID):
						bisect.insort(term_postings_list, docID) #doc Id = tweet ID						
						dictionary[term][1] += 1 # increase the cached length of the postings list
				else:
					#new term, add to dictionary and create new postings list
					term_postings_list = [docID]
					postings.append(term_postings_list)
					dictionary[term] = [len(postings) - 1, 1] 															
# end index(filename)

def query(term):
	#normalize query term
	term = normalize_term(term)
	if term in dictionary:
		return get_postings_list(dictionary[term][0])

def intersect(posting_list1, posting_list2):
	result = []
	list_iter1 = iter(posting_list1)
	list_iter2 = iter(posting_list2)
	non_empty = len(posting_list1) > 0 and len(posting_list2) > 0
	if(non_empty):
		# get current postings (doc IDs)
		doc_id1 = list_iter1.next()
		doc_id2 = list_iter2.next()
	
	while(non_empty):
		try:			
			#compare doc IDs
			if doc_id1 == doc_id2:
				# match found, add to results
				result.append(doc_id1)
				doc_id1 = list_iter1.next()
				doc_id2 = list_iter2.next()
			elif doc_id1 < doc_id2:
				doc_id1 = list_iter1.next()
			else:
				doc_id2 = list_iter2.next()				
		except StopIteration:
			# one of the lists doesn't have more elements
			break			
	return result
#end of intersect(posting_list1, posting_list2)
	
def bool_query(term1, term2):
	#normalize search terms
	result = posting_list1 = posting_list2 =[]
	term1 = normalize_term(term1)
	term2 = normalize_term(term2)
	print("Showing results for %s, %s:" %(term1, term2))
	if term1 in dictionary:
		posting_list1 = get_postings_list(dictionary[term1][0])	
	if term2 in dictionary:	 
		posting_list2 = get_postings_list(dictionary[term2][0])	
	result = intersect(posting_list1, posting_list2)					
	if len(result) > 0:		
		#fetch documents from file
		with open(filename, 'r') as input_file:
			for line in input_file:
				current_doc = line.split("\t")
				for doc_id in result:
					if doc_id == long(current_doc[1]):
						print(line)
# end of query(term1, term2)					
												
#******* Check parameters to get path from arguments *********
try:
	
	filename = os.path.abspath(sys.argv[1])	
	if not os.path.exists(filename):
		print("invalid file path or name.")
		exit() #file not found, exit program 
		
except Exception as exc:
	filename = ""
	print("An error occurred while reading system parameters\n error details: ", exc)
	exit() #exit program 	 

print "indexing docs from file..." 
#******* Build index *********
index(filename)

#******* Query index *********
bool_query("stuttgart","bahn")
