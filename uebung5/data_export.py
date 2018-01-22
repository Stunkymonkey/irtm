#!/usr/bin/env python3
import csv
import random
import math
from collections import defaultdict

stop_words = {"aber", "alle", "allem", "allen", "aller", "alles", "als", "also", "am", "an", "ander", "andere",
              "anderem", "anderen", "anderer", "anderes", "anderm", "andern", "anders", "auch", "auf", "aus", "bei",
              "bin", "bis", "bist", "da", "damit", "dann", "das", "dass", "dasselbe", "dazu", "daß", "dein", "deine",
              "deinem", "deinen", "deiner", "deines", "dem", "demselben", "den", "denn", "denselben", "der", "derer",
              "derselbe", "derselben", "des", "desselben", "dessen", "dich", "die", "dies", "diese", "dieselbe",
              "dieselben", "diesem", "diesen", "dieser", "dieses", "dir", "doch", "dort", "du", "durch", "ein", "eine",
              "einem", "einen", "einer", "eines", "einig", "einige", "einigem", "einigen", "einiger", "einiges",
              "einmal", "er", "es", "etwas", "euch", "euer", "eure", "eurem", "euren", "eurer", "eures", "für", "gegen",
              "gewesen", "hab", "habe", "haben", "hat", "hatte", "hatten", "hier", "hin", "hinter", "ich", "ihm", "ihn",
              "ihnen", "ihr", "ihre", "ihrem", "ihren", "ihrer", "ihres", "im", "in", "indem", "ins", "ist",
              "jede", "jedem", "jeden", "jeder", "jedes", "jene", "jenem", "jenen", "jener", "jenes", "jetzt", "kann",
              "kein", "keine", "keinem", "keinen", "keiner", "keines", "können", "könnte", "machen", "man", "mal",
              "manche", "manchem", "manchen", "mancher", "manches", "mein", "meine", "meinem", "meinen", "meiner",
              "meines", "mich", "mir", "mit", "muss", "musste", "nach", "nicht", "nichts", "noch", "nun", "nur", "ob",
              "oder", "ohne", "sehr", "sein", "seine", "seinem", "seinen", "seiner", "seines", "selbst", "sich", "sie",
              "sind", "so", "solche", "solchem", "solchen", "solcher", "solches", "soll", "sollte", "sondern", "sonst",
              "um", "und", "uns", "unser", "unsere", "unserem", "unseren", "unserer", "unseres", "unter", "viel", "vom",
              "von", "vor", "war", "waren", "warst", "was", "weg", "weil", "weiter", "welche", "welchem", "welchen",
              "welcher", "welches", "wenn", "werde", "werden", "wie", "wieder", "will", "wir", "wird", "wirst", "wo",
              "wollen", "wollte", "während", "würde", "würden", "zu", "zum", "zur", "zwar", "zwischen", "über"}
init_prob = 0.5

feature_classification = defaultdict()
amount_good = 0
amount_bad = 0


def load_csv(filename):
    data = csv.reader(open(filename, "r"), delimiter='\t')
    result = list()
    count = 0
    for i in data:
        tmp1 = []
        for word in i[2].split(" "):
            norm = normalize(word)
            if 0 < len(norm) <= 20 and norm not in stop_words:
                tmp1.append(norm)
        tmp2 = []
        for word in i[3].split(" "):
            norm = normalize(word)
            if 0 < len(norm) <= 20 and norm not in stop_words:
                tmp2.append(norm)

        result.append([i[0], i[1], tmp1, tmp2])
    return result


def write_csv(filename, rows):
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)


def normalize(term):
    """
    normalize word and remove useless stuff
    """
    return term.lower(). \
        replace(":", ""). \
        replace(";", ""). \
        replace(".", ""). \
        replace(",", ""). \
        replace("/", ""). \
        replace("#", ""). \
        replace("!", ""). \
        replace("?", ""). \
        replace("(", ""). \
        replace(")", ""). \
        replace("'", ""). \
        replace("\"", "")


def learn(data):
    global amount_good
    global amount_bad
    for line in data:
        if line[1] == "gut":
            amount_good += 1
            add_line(line, True)
        else:
            amount_bad += 1
            add_line(line, False)


def add_line(line, is_good):
    words = line[2] + line[3]
    for word in words:
        if word == "":
            continue
        if word not in feature_classification:
            feature_classification[word] = [0, 0]
        feature_classification[word][is_good] += 1


def weighted_prob(word, is_good):
    count = 0
    f_count = 0.5
    if word in feature_classification:
        count = sum(feature_classification[word])
        f_count = feature_classification[word][is_good]
    if is_good:
        fprob = float(f_count) / float(amount_good)
    else:
        fprob = float(f_count) / float(amount_bad)
    return (init_prob + count * fprob) / (1 + count)


def prob(words, is_good):
    result = 1.0
    for word in words:
        word = normalize(word)
        if word == "":
            continue
        result *= weighted_prob(word, is_good)
    return result
    if is_good:
        result *= (float(amount_good) / float(amount_good + amount_bad))
    else:
        result *= (float(amount_bad) / float(amount_good + amount_bad))
    return result


def get_class(line):
    good = prob(line[2] + line[3], True)
    bad = prob(line[2] + line[3], False)
    return [good, bad]


def main():
    data = load_csv("games-train.csv")
    learn(data)
    tmp = [["V1", "V2"]]
    for line in data:
        v = get_class(line)
        tmp.append([float(len(line[2] + line[3])), v[0] - v[1]])
    write_csv("data.csv", tmp)


if __name__ == '__main__':
    main()
