#!/usr/bin/env python3
from collections import defaultdict
import math
import sys


occurences = []
tfidf_documents = []
all_terms = set()
all_occurences = defaultdict(set)
idf = defaultdict()

stop_words = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
              'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
              'to', 'was', 'were', 'will', 'with'}


def normalize(term):
    """
    normalize word and remove useless stuff
    """
    return term.lower().\
        replace(":", "").\
        replace(";", "").\
        replace(".", "").\
        replace(",", "").\
        replace("/", "").\
        replace("#", "").\
        replace("!", "").\
        replace("?", "").\
        replace("'", "").\
        replace("\"", "")


def normalize_line(occurence):
    all = sum(occurence.values())
    for term in occurence:
        occurence[term] = occurence[term] / all
    return occurence


def index(filename):
    try:
        current_id = 0
        # open file
        with open(filename, "r") as file:
            # iterate over each line in file
            for line in file:
                tweet = line.split()

                occurence = defaultdict()

                for term in tweet[4:]:
                    # remove clutter
                    term = normalize(term)
                    # check if term is in stop words to save some memory
                    if (not str.isalpha(term) or (term in stop_words)):
                        continue
                    if term in occurence:
                        occurence[term] += 1
                    else:
                        occurence[term] = 1
                    all_occurences[term].add(current_id)
                    all_terms.add(term)
                occurence = normalize_line(occurence)
                occurences.append(occurence)

                current_id += 1
                # this is for displaying a progress while indexing
                if current_id % 10000 == 0:
                    sys.stdout.write("\r{0} %".format(
                        int(current_id / 10000.0)))
                    sys.stdout.flush()
                # if current_id >= 100000:
                #     break
    except FileNotFoundError as e:
        raise SystemExit("Could not open file: " + str(e))
    return


def inverseDocumentFrequency():
    len_all_terms = len(occurences)
    for line in occurences:
        for term in line:
            occ_in_all = len(all_occurences[term])
            if occ_in_all > 0:
                idf[term] = 1.0 + \
                    math.log(float(len_all_terms) / occ_in_all, 10)
            else:
                idf[term] = 1.0


def tfidf():
    for line in occurences:
        doc_tfidf = defaultdict()
        for term, tf in line.items():
            doc_tfidf[term] = tf * idf[term]
        tfidf_documents.append(doc_tfidf)


def cosine_similarity(vector1, vector2):
    """
    return the similarity of two vectors
    """
    dot_product = sum(p * q for p, q in zip(vector1, vector2))
    magnitude = math.sqrt(sum([val**2 for val in vector1])) * \
        math.sqrt(sum([val**2 for val in vector2]))
    if not magnitude:
        return 0
    return dot_product / magnitude


def getLines(filename, lines, sim):
    """
    get lines of multiple lines
    """
    result = ""
    try:
        # open file
        with open(filename, "r") as file:
            # iterate over the lines and print the lines, which match the terms
            tmp = []
            for i, line in enumerate(file):
                if i in lines:
                    tmp.append((i, line))
            for i, line in enumerate(lines):
                for j in tmp:
                    if (line == j[0]):
                        result += str(sim[i]) + "\t" + str(j[0]) + "\t" + j[1]
    except FileNotFoundError as e:
        raise SystemExit("Could not open file: " + str(e))
    return result


def main():
    filename = "tweets"
    index(filename)
    inverseDocumentFrequency()
    tfidf()
    try:
        # asking for more querys
        while True:
            # ask for input
            tfidf_comparisons = []
            search = input('What are you looking for?: ')
            search = search.split()

            occurence = defaultdict()
            for term in search:
                # remove clutter
                term = normalize(term)
                # check if term is in stop words to save some memory
                if not str.isalpha(term) or (term in stop_words):
                    continue
                if term not in all_terms:
                    continue
                if term in occurence:
                    occurence[term] += 1
                else:
                    occurence[term] = 1
            occurence = normalize_line(occurence)
            if len(occurence) == 0:
                continue

            vector = []
            for term, tf in occurence.items():
                vector.append(tf * idf[term])

            for count, doc in enumerate(tfidf_documents):
                make_vector = [0.0] * len(occurence)
                i = 0
                for key, value in occurence.items():
                    if key in doc:
                        make_vector[i] = doc[key]
                    i += 1
                similarity = cosine_similarity(vector, make_vector)
                if similarity > 0:
                    tfidf_comparisons.append((similarity, count))
            lines = []
            sim = []
            for x in sorted(tfidf_comparisons, key=lambda y: float(y[0]), reverse=True)[:100]:
                sim.append(x[0])
                lines.append(x[1])
            print(getLines(filename, lines, sim))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
