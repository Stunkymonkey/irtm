#!/usr/bin/env python3
name = ""


def index(filename):
    global name
    name = filename
    global dict
    dict = {}
    global pList
    pList = []
    try:
        global file
        with open(filename, "r") as file:
            docID = 0
            for line in file:
                tweet = line.split()
                for term in tweet:
                    if term in dict:
                        dict[term] = [dict[term][0] + 1, dict[term][1]]
                        position = dict[term][1]
                        pList.insert(position + dict[term][0] - 1, docID)
                        for key, value in dict.copy().items():
                            if (value[1] > position):
                                dict[key] = [value[0], value[1] + 1]
                    else:
                        dict[term] = [1, len(pList)]
                        pList.append(docID)
                docID += 1
                if docID % 1000 == 0:
                    print(docID)
    except FileNotFoundError as e:
        raise SystemExit("Could not open file: " + str(e))
    return dict


def query(term1, term2=""):
    result = ""
    lines = []
    if term1 in dict and not term2:
        list = dict[term1]
        lines = pList[list[1]:list[1] + list[0]]
    elif term2 and term2 in dict:
        list1 = dict[term1]
        lines1 = pList[list1[1]:list1[1] + list1[0]]
        list2 = dict[term2]
        lines2 = pList[list2[1]:list2[1] + list2[0]]
        listiter1 = iter(lines1)
        listiter2 = iter(lines2)
        tmp1 = -1
        tmp2 = -1
        while True:
            try:
                if tmp1 <= tmp2:
                    tmp1 = next(listiter1)
                    print("tmp1: " + str(tmp1))
                else:
                    tmp2 = next(listiter2)
                    print("tmp2: " + str(tmp2))
                if tmp1 == tmp2:
                    lines.append(tmp1)
            except StopIteration:
                break
    try:
        with open(name, "r") as file:
            for i, line in enumerate(file):
                if i in lines:
                    result += str(i) + "\t" + line
    except FileNotFoundError as e:
        raise SystemExit("Could not open file: " + str(e))
    return result


if __name__ == '__main__':
    print("building index...")
    index("tweets")
    print("finished indexing")
    # print(query("which"))
    print()
    print(query("stuttgart", "bahn"))
