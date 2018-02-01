
#Turn the raw data into lists consist of class and information.
#The information include the title of review and review text.
#The information is saved by tokens in lists
#The title of game is not include
#e.g. ['Class', ['token1', 'token2', ...]]

def data_prep(filename):
    f = open(filename, 'r')
    lines = f.readlines()
    f.close
    data = []
    for line in lines:
        line = line.rstrip()
        line = line.lower()
        cls = line.split("\t")[1]
        tokens = []
        for token in line.split("\t")[2].split(" ") + line.split("\t")[3].split(" "):
            if token != '':
                tokens.append(token)
        data.append([cls, tokens])
    return data

def build_model(train_data):
    global P_gut
    global P_schlecht
    global para_gut
    global para_schlecht
    P_gut = 0
    P_schlecht = 0
    para_gut = {}
    para_schlecht = {}
    
    Vocab = set()
    freq_in_gut = {}
    freq_in_schlecht = {}
    total_doc = 0
    num_gut = 0
    num_schlecht = 0
    for doc in train_data:
        total_doc += 1
        if doc[0] == 'gut':
            num_gut += 1
            for token in doc[1]:
                if token not in freq_in_gut:
                    Vocab.add(token)
                    freq_in_gut[token] = 1
                else:
                    freq_in_gut[token] += 1
                    
        elif doc[0] == 'schlecht':
            num_schlecht += 1
            for token in doc[1]:
                if token not in freq_in_schlecht:
                    Vocab.add(token)
                    freq_in_schlecht[token] = 1
                else:
                    freq_in_schlecht[token] += 1
    
    for token in Vocab:
        para_gut[token] = (freq_in_gut.get(token, 0) + 1) / (sum(freq_in_gut.values()) + len(Vocab))
        para_schlecht[token] = (freq_in_schlecht.get(token, 0) + 1) / (sum(freq_in_gut.values()) + len(Vocab))
        
    P_gut = num_gut/total_doc
    P_schlecht = num_schlecht/total_doc

        
def classification(doc):
    P_gut_doc = P_gut
    P_schlecht_doc = P_schlecht
    
    for token in doc:
        try:
            P_gut_doc = P_gut_doc * para_gut[token]
            P_schlecht_doc = P_schlecht * para_schlecht[token]
        except:
            pass
    if P_gut_doc >= P_schlecht_doc:
        return 'gut'
    else:
        return 'schlecht'


def evaluation(data):
    TP_gut = 0
    FP_gut = 0
    FN_gut = 0
    precision_gut = 0
    recall_gut = 0
    F_gut = 0
    
    TP_schlecht = 0
    FP_schlecht = 0
    FN_schlecht = 0
    precision_schlecht = 0
    recall_schlecht = 0
    F_schlecht = 0
    
    for doc in data:
        TP_gut = TP_gut + ((doc[0]=='gut')and(classification(doc[1])=='gut'))
        FP_gut = FP_gut + ((doc[0]=='schlecht')and(classification(doc[1])=='gut'))
        FN_gut = FN_gut + ((doc[0]=='gut')and(classification(doc[1])=='schlecht'))
        TP_schlecht = TP_schlecht + ((doc[0]=='schlecht')and(classification(doc[1])=='schlecht'))
        FP_schlecht = FP_schlecht + ((doc[0]=='gut')and(classification(doc[1])=='schlecht'))
        FN_schlecht = FN_schlecht + ((doc[0]=='schlecht')and(classification(doc[1])=='gut'))
    
    precision_gut = TP_gut / (TP_gut + FP_gut)
    recall_gut = TP_gut / (TP_gut + FN_gut)
    F_gut = (2*precision_gut*recall_gut) / (precision_gut+recall_gut)
    
    precision_schlecht = TP_schlecht / (TP_schlecht + FP_schlecht)
    recall_schlecht = TP_schlecht / (TP_schlecht + FN_schlecht)
    F_schlecht = (2*precision_schlecht*recall_schlecht) / (precision_schlecht+recall_schlecht) 
    
    print('For class \'gut\':')
    print('TP:', TP_gut)
    print('FP:', FP_gut)
    print('FN:', FN_gut)
    print('Precision,:', precision_gut)
    print('Recall:', recall_gut)
    print('F:', F_gut)
    print('')
    print('For class \'schlecht\':')
    print('TP:', TP_schlecht)
    print('FP:', FP_schlecht)
    print('FN:', FN_schlecht)
    print('Precision,:', precision_schlecht)
    print('Recall:', recall_schlecht)
    print('F:', F_schlecht)
    print('')
    

train_data = data_prep('games-train.csv')
build_model(train_data)
test_data = data_prep('games-test.csv')
evaluation(test_data)


print(sorted(para_gut, key=para_gut.get, reverse=True)[0:100])
print(sorted(para_schlecht, key=para_schlecht.get, reverse=True)[0:100])
