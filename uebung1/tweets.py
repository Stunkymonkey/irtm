#!/usr/bin/env python3
name = ""


def index(filename):
    """
    indexes a given file and saves terms to a posting and non-positional inverted index
    """
    global name
    name = filename
    global dict
    dict = {}
    global pList
    pList = []
    try:
        # open file
        global file
        with open(filename, "r") as file:
            docID = 0
            # iterate over each line in file
            for line in file:
                # make everything lowercase, remove hashtags and slpit them to
                # list of terms
                tweet = line.lower().replace("#", "").split()
                for term in tweet:
                    # if term already in dict:
                    # add it to postinglist; increase the offset in the dict
                    # and move all other pointer to their new list location
                    if term in dict:
                        dict[term] = [dict[term][0] + 1, dict[term][1]]
                        position = dict[term][1]
                        pList.insert(position + dict[term][0] - 1, docID)
                        for key, value in dict.copy().items():
                            if (value[1] > position):
                                dict[key] = [value[0], value[1] + 1]
                    # if not present add it to postinglist and add it to the
                    # dict
                    else:
                        dict[term] = [1, len(pList)]
                        pList.append(docID)
                # count line numbers
                docID += 1
                # this is for displaying a progress while indexing
                if docID % 1000 == 0:
                    print(docID)
    except FileNotFoundError as e:
        raise SystemExit("Could not open file: " + str(e))
    return


def query(term1, term2=""):
    """
    you can query your search terms. If only one term given it only searches
    for one, otherwise they both have to exist in the tweet
    """
    result = ""
    lines = []
    # if only one term given look for it
    if term1 in dict and not term2:
        # get index and offset
        list = dict[term1]
        # create list with index and offset
        lines = pList[list[1]:list[1] + list[0]]
    # if two terms are given look for both
    elif term2 and term2 in dict:
    	# get index and offset
        list1 = dict[term1]
        # create list with index and offset
        lines1 = pList[list1[1]:list1[1] + list1[0]]
        # get index and offset
        list2 = dict[term2]
        # create list with index and offset
        lines2 = pList[list2[1]:list2[1] + list2[0]]
        # init of iterators
        listiter1 = iter(lines1)
        listiter2 = iter(lines2)
        tmp1 = -1
        tmp2 = -1
        # and intersect the lists to see which lines match both terms
        # if the have the same lines, it will be added to 'lines'
        while True:
            try:
                # like discused in the lesson
                if tmp1 <= tmp2:
                    tmp1 = next(listiter1)
                else:
                    tmp2 = next(listiter2)
                if tmp1 == tmp2:
                    lines.append(tmp1)
            except StopIteration:
                break
    try:
        # open file
        with open(name, "r") as file:
            # iterate over the lines and print the lines, which match the terms
            for i, line in enumerate(file):
                if i in lines:
                    result += str(i) + "\t" + line
    except FileNotFoundError as e:
        raise SystemExit("Could not open file: " + str(e))
    return result


if __name__ == '__main__':
    index("tweets")
    print("finished indexing")
    print(query("stuttgart", "bahn"))
