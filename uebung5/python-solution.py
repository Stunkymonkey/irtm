import numpy as np

filepath = "games-train.csv"

class KMeans:
    debug = False
    reviews = []
    vectors = []
    words = []
    clusters = []
    centroids = []
    closest = []
    classes = set()
    maxVector = []
    solution = []
    data_length = None
    TP = FP = TN = FN = 0
    K = 0
    dim = 0
    def __init__(self, length = None, debug = False):
        self.data_length = length
    def read_data(self, path, length = None):
        """
        Reads data from a file specified by path.
        """
        self.reviews = []
        #print("Read Data")
        data = open(path, 'r')
        lines = data.readlines()
        i = 0
        for line in lines:
            review = line.split('\t')
            self.reviews.append(review)
            if length is not None and i >= length:
                break
            i+= 1
    def determineClasses(self):
        """
        Determines the (actual classes) and sets self.K accordingly (number of clusters)
        """
        reviewIdx = 1 # 1 for good/bad, 0 for games
        self.classes = set()
        for review in self.reviews:
            self.classes.add(review[reviewIdx]) #Classes are "good" and "bad". This works for general Classes, though like for instance games
        self.classes = list(self.classes) #We need some kind of order!
        self.K = len(self.classes)
        self.solution = [[] for _ in range(self.K)]
        self.clusters = [[] for _ in range(self.K)]
        for review in self.reviews:
            if review[3] is not None:
                self.solution[self.classes.index(review[reviewIdx])].append(self.doc2Vec(review[3]))
    def doc2Vec(self, doc):
        """
        Converts a document into a vector
        """
        vector = np.zeros(self.dim)
        docWords = doc.split(' ')
        for word in docWords:
            pos = self.words.index(word)
            vector[pos] += 1
        return vector
    def findReview(self, vec):
        """
        Finds a Review given a vector.
        """
        for review in self.reviews:
            if np.array_equal(self.doc2Vec(review[3]), vec):
                return review
        return None
    def initWords(self):
        """
        This will get all words of all documents and save them to self.words
        """
        #print("InitWords")
        self.words = []
        for review in self.reviews:
            doc = review[3]
            if (doc):
                docWords = doc.split(' ')
                for word in docWords:
                    if not word in self.words:
                        self.words.append(word)
        self.dim = len(self.words)
        #print("Dimension: " + str(self.dim))
    def initVectors(self):
        """
        This will Initialize all vectors accordingly to self.words
        """
        #print("InitVectors")
        self.vectors = []
        for review in self.reviews:
            doc = review[3]
            if (doc):
                self.vectors.append(self.doc2Vec(doc))

    def assign(self):
        """
        assign-phase of K-Means. Every vector finds its closest centroid and is put into the according cluster
        """
        #print("Assign")
        self.clusters = [[] for _ in range(self.K)]
        for vector in self.vectors:
            mindist = None
            argminIdx = None
            i = 0
            for centroid in self.centroids:
                dist = np.linalg.norm(vector - centroid)
                if mindist is None or dist < mindist:
                    mindist = dist
                    argminIdx = i
                i+=1
            self.clusters[argminIdx].append(vector)
    def recompute(self):
        """
        Recompute-phase of K-Means. Every Centroid is set to the average of all its vectors.
        """
        #print("Recompute")
        for i in range(self.K):
            if (len(self.clusters[i]) <= 1):
                self.centroids[i] = self.randomCentroid()
            else:
                self.centroids[i] = sum(self.clusters[i]) / len(self.clusters[i])
    def prepare(self):
        """
        Prepare-phase of K-Means. Every vector is initialized randomly.
        """
        #compute maximum count of each word
        #print("Preprocessing: MaxVector")
        self.centroids = []
        self.maxVector = np.zeros(self.dim)
        for vector in self.vectors:
            for i in range(self.dim):
                self.maxVector[i] = max(self.maxVector[i], vector[i])
        #random centroids
        #print("Preprocessing: RandomCentroid")
        for i in range(self.K):
            self.centroids.append(self.randomCentroid())
    def randomCentroid(self):
        """
        This method requires self.maxVector to be set!
        :return: A random centroid.
        """
        centroid = []
        for i in range(self.dim):
            centroid.append(np.random.randint(self.maxVector[i] + 1))
        return np.array(centroid)
    def evaluate(self):
        """
        This method computes some metrics. It's very slow currently.
        :return: Rand Index Metric
        """
        #print("-----------Evaluation-------------")
        pairs = []
        for idx,item in enumerate(self.vectors):
            for jidx, jitem in enumerate(self.vectors):
                if idx > jidx:
                    pairs.append((item, jitem))
        FP = FN = TP = TN = 0
        progressPoints = [i for i in range(1,len(pairs),len(pairs)//10)]
        i = 0
        #for idx, cluster in enumerate(self.clusters):
        #    print("Length of cluster " + str(idx + 1) + ": " + str(len(cluster)))
        #for idx, aClass in enumerate(self.solution):
        #    print("Length of class " + self.classes[idx] + ": " + str(len(aClass)))
        for pair in pairs:
            #if i in progressPoints:
                #print("Evaluation progress: " + str(i) + " of " + str(len(pairs)) + "...")
            i+=1
            firstClass = secondClass = firstCluster = secondCluster = None

            for grpIdx, grp in enumerate(self.solution):
                if self.numpyIn(pair[0],grp):
                    firstClass = grpIdx
                if self.numpyIn(pair[1],grp):
                    secondClass = grpIdx
            for clusterIdx, cluster in enumerate(self.clusters):
                if self.numpyIn(pair[0],cluster):
                    firstCluster = clusterIdx
                if self.numpyIn(pair[1],cluster):
                    secondCluster = clusterIdx
            if firstClass == secondClass and firstCluster == secondCluster:
                TP += 1
            if firstClass != secondClass and firstCluster == secondCluster:
                FP += 1
            if firstClass == secondClass and firstCluster != secondCluster:
                FN += 1
            if firstClass != secondClass and firstCluster != secondCluster:
                TN += 1
        (self.TP, self.FP, self.FN, self.TN) = (TP, FP, FN, TN)
        #print("TP: " + str(TP))
        #print("FP: " + str(FP))
        #print("FN: " + str(FN))
        #print("TN: " + str(TN))
        RandIndex = float(TP + TN)/(TP + TN + FP + FN)
        assert(RandIndex <= 1)
        print("Rand Index: " + str(RandIndex))
        return RandIndex
    def numpyIn(self, needle, haystack):
        """
        Helper Method: This can be used to find a numpy-array inside a collection of numpy-arrays.
        """
        for elem in haystack:
            if np.array_equal(needle, elem):
                return True
        return False
    def findClosest(self):
        """
        This finds the closest vector to each centroid (We assume that this vector can be found in the cluster of the centroid)
        """
        self.closest = []
        for idx, cluster in enumerate(self.clusters):
            argmin = None
            min = None
            for vector in cluster:
                dist = np.linalg.norm(vector - self.centroids[idx])
                if min is None or dist < min:
                    argmin = vector
            self.closest.append(argmin)

    def main(self, iterations):
        """
        Run full K-Means with initialization and evaluation
        :param iterations: This is the "K"
        :return: Rand Index
        """
        print("######### Calculate with K = " + str(iterations))
        self.read_data(filepath, self.data_length)
        self.initWords()
        self.determineClasses()
        self.initVectors()
        self.prepare()
        for i in range(iterations):
            #print("Iteration: " + str(i+1))
            self.assign()
            self.recompute()
        self.findClosest()
        return self.evaluate()

def main():
    two_ratings = []
    twenty_ratings = []
    for i in range(10):
        k_means = KMeans(100)
        two_ratings.append(k_means.main(2))
        second_means = KMeans(100)
        twenty_ratings.append(second_means.main(20))
        for idx in range(second_means.K):
            print("Closest Document in Cluster " + str(idx) + ":\n" + '\t'.join(second_means.findReview(second_means.closest[idx])))
    print("Average Rand Index for K = 2: " + str(np.average(two_ratings)))
    print("Average Rand Index for K = 20: " + str(np.average(twenty_ratings)))
    
if __name__ == "__main__":
    main()
