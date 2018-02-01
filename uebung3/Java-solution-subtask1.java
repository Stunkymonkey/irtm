package inforet;

import java.io.*;
import java.util.*;

public class Ranker {

    // maps a term to a profile that contains its postings, tf and idf scores
    private HashMap<String, Profile> termToProfile;
    // number of documents in the corpus
    private int corpusCardinality;

    private Ranker() {
        termToProfile = new HashMap<>();
        corpusCardinality = 0;
    }

    /**
     * for all observed terms in the corpus, it creates a postings list; computes the tf map and an idf score
     * @param corpus  a file with all documents to index
     * @param smoothIDF whether to use smooth Idf metric (true) or normal Idf (false)
     */
    public Ranker(File corpus, boolean smoothIDF) {
        this();
        build(corpus, smoothIDF);
    }

    // create postings lists; store term frequencies; then store IDF vals
    private void build(File corpus, boolean smoothIDF) {

        int n=0; // counter for number of documents
        try (BufferedReader r = new BufferedReader(new FileReader(corpus))) {
            String line;
            while ((line=r.readLine())!=null) {
                String[] lineSplit = line.split("\\t");
                if (lineSplit.length != 5) continue; // skip if num cols is less than expected

                long docID = Long.parseLong(lineSplit[1]); // doc ID is at 2nd col
                String content = lineSplit[4]; // content is at 5th col
                content = content.replaceAll("\\p{Punct}", "").toLowerCase().trim(); // delete punctuation & lowercase
                if (content.isEmpty()) continue; // skip tweets with empty content
                n++;

                String[] terms = content.split(" ");
                for (String term : terms) {
                    // add current docID to the postings of current term
                    Profile p = (termToProfile.containsKey(term)) ? termToProfile.get(term) : new Profile();
                    p.addDoc(docID);
                    termToProfile.put(term, p);
                }
            }

        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }

        corpusCardinality = n; // store total number of docs in the indexed dir

        // set the idf for each term using the corpus cardinality
        termToProfile.forEach((k, v) -> {
            // smooth Idf scores to avoid 0 when term appears in all docs
            if (smoothIDF) v.setSmoothIdfwithN(corpusCardinality);
            else v.setIdfwithN(corpusCardinality); // default: normal idf

            v.rescaleTFs(); // use log scale for tf instead of absolute freq
        });

        // normalize tf values by vector length of document vectors to have unit vectors
        normalizeTfsToUnitVecs();
    }

    // converts a vector of tf scores to a unit vector
    private void normalizeTfsToUnitVecs() {
        // step 0: create an accumulator for each doc
        Map<Long, Double> accumulatorMap = new HashMap<>(corpusCardinality);

        // step 1: sum the squares of all the values in the vector of each doc
        for (Profile profile : termToProfile.values())
            profile.postings.forEach((docId, tf) -> {
            double score = accumulatorMap.containsKey(docId) ?
                    accumulatorMap.get(docId) + (tf * tf) : (tf * tf); // sum of squares
            accumulatorMap.put(docId, score);
            });

        // step 2: take the square root to determine vector lengths
        accumulatorMap.keySet().forEach(docID -> accumulatorMap.put(docID, Math.sqrt(accumulatorMap.get(docID))));

        // step 3: divide each val by the corresponding vector length and store this normalized score
        for (Profile profile : termToProfile.values()) {
            LinkedHashMap<Long, Double> newPostings = new LinkedHashMap<>();
            profile.postings.forEach((docID, oldTf) -> {
                double denom = accumulatorMap.get(docID); // denominator is vector length
                double newVal = oldTf / denom; // divide old tf val by vec length to normalize
                newPostings.put(docID, newVal); // store the new tf val
            });
            profile.postings = newPostings;
        }
    }

    /**
     * Tf-Idf score for a doc wrt to the given one-term query
     * @param query a one-term query
     * @param docID id of the doc to score
     * @return score = norm_tf(term,doc) * idf(term) if term occurs in doc; else 0
     */
    private double score(String query, long docID) {
        if (!termToProfile.get(query).postings.containsKey(docID)) return 0;
        double docTf = termToProfile.get(query).postings.get(docID);
        double idf = termToProfile.get(query).idf;
        return docTf * idf;
    }

    /**
     * boolean OR query operator
     * returns the union of all docIDs from the postings of all query terms
     * i.e. docs(q_1) U .... U docs(q_n); null pointers and OOV terms are ignored
     * @param queryTerms
     * @return all documents that contain at least 1 of the query terms
     */
    private Set<Long> potentialDocs(String... queryTerms) {
        Set<Long> docs = new HashSet<>();
        for (String term : queryTerms) {
            if (term != null) {
                term =term.replaceAll("\\p{Punct}", "").toLowerCase().trim();
                if (term.isEmpty() || !termToProfile.containsKey(term)) continue;
                docs.addAll(termToProfile.get(term).postings.keySet());
            }
        }
        return docs;
    }

    /**
     * score each of the given documents based on similarity to all the given query terms
     * @param docIDs     a list of doc ids to score and rank by score
     * @param queryTerms query terms
     * @return an ordered set of documents by their computed score
     */
    public TreeSet<ScoredDoc> score(Collection<Long> docIDs, String... queryTerms) {
        // create a map of <queryTerm, tf>; and store tf on log scale
        LinkedHashMap<String, Double> qMap = new LinkedHashMap<>(queryTerms.length);
        for (int i = 0; i < queryTerms.length; i++) {
            if (queryTerms[i] != null) {
                String t = queryTerms[i].replaceAll("\\p{Punct}", "").toLowerCase().trim();
                if (t.isEmpty() || !termToProfile.containsKey(t)) continue;
                qMap.put(t, qMap.containsKey(t) ? qMap.get(t) + 1 : 1);
            }
        }

        qMap.keySet().forEach(k -> qMap.put(k, 1 + Math.log10(qMap.get(k)))); // re-scale on log

        // create an ordered set to store the result in descending order
        TreeSet<ScoredDoc> res = new TreeSet<>(Collections.reverseOrder());

        // iterate through documents; compute score; store in the result set
        for (Long docID : docIDs) {
            double score = 0;
            for (Map.Entry<String, Double> entry : qMap.entrySet())
                //score = tf(term, query) * idf(term) * tf(term, cur_doc)
                score += entry.getValue() * score(entry.getKey(), docID);

            res.add(new ScoredDoc(docID, score));
        }
        return res;
    }

    /**
     * first: retrieves all docs that contain at least 1 of the query terms
     * second: orders them by tf-idf similarity to the query (descending order)
     *
     * @param queryTerms
     * @return set of relevant docs, ranked by similarity to the query
     */
    public TreeSet<ScoredDoc> query(String... queryTerms) {
        Collection<Long> potentialDocs = potentialDocs(queryTerms);
        return score(potentialDocs, queryTerms);
    }

    /**
     * Private class to represent the profile of a term
     * stores its inverted index, tf and idf vals
     */
    class Profile {
        double idf;
        LinkedHashMap<Long, Double> postings; // <docID, tf> pairs; tf can be on log scale

        Profile() {
            idf = -1; // dummy val as long as idf not yet determined
            postings = new LinkedHashMap<>();
        }

        void addDoc(long docID) { // add doc ID to the postings (if doesn't exist) or update its freq
            postings.put(docID, postings.containsKey(docID) ? postings.get(docID) + 1 : 1);
        }

        void setIdfwithN(double n) {
            idf = Math.log10(n / postings.size());
        }

        void setSmoothIdfwithN(double n) {
            idf = Math.log10(1 + (n / postings.size()));
        }

        // store tf on log scale instead of absolute values
        void rescaleTFs() {
            // add 1 to avoid 0 when tf=1
            postings.keySet().forEach(i -> postings.put(i, 1 + Math.log10(postings.get(i))));
        }
    }

    /**
     * Inner class representing a scored document
     * stores only a doc id together with its score (wrt to a query)
     */
    public class ScoredDoc implements Comparable<ScoredDoc> {

        long docID;
        double score;

        public ScoredDoc(long id, double s) {
            docID = id;
            score = s;
        }

        @Override
        public int compareTo(ScoredDoc d2) {
            return Double.compare(this.score, d2.score);
        }
    }

    // fetch all documents in the given file whose ID is contained in the docsIDList
    private static Map<Long, String> fetchDocumentsByID(String filepath, List<Long> docIDsList) {
        Map<Long, String> fetchedDocs = new HashMap<>(docIDsList.size());

        try (BufferedReader r = new BufferedReader(new FileReader(filepath))) {
            String line;
            while ((line=r.readLine())!=null) {
                String[] lineSplit = line.split("\\t");
                if (lineSplit.length != 5) continue;
                // doc ID is at 2nd col, content at 5th col
                long docID = Long.parseLong(lineSplit[1]);
                if (docIDsList.contains(docID))
                    fetchedDocs.put(docID, lineSplit[4]);
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }

        return fetchedDocs;
    }

    // from a list of ranked documents, print the top k results (docID, score, content)
    public static void printTopK(String filename, TreeSet<ScoredDoc> query, int k) {
        List<Long> list = new ArrayList<>(k);
        List<ScoredDoc> listDocID = new ArrayList<>(k);

        Iterator<ScoredDoc> iter = query.iterator();
        int i=0;
        while (iter.hasNext() && i<k) {
            ScoredDoc d = iter.next();
            list.add(d.docID);
            listDocID.add(d);
            i++;
        }
        Map<Long, String> documents = fetchDocumentsByID(filename, list);

        for (int j = 0; j < listDocID.size(); j++) {
            ScoredDoc cur = listDocID.get(j);
            System.out.println(cur.docID + " :: " + cur.score + " # ");
            System.out.println(documents.get(cur.docID));
        }

        System.out.println();
    }

    public static void main(String[] args) {

        Long start = System.currentTimeMillis();

        String filename = "res/twitter/tweets.txt";
        Ranker ranker = new Ranker(new File(filename), true); // create a ranker instance; use smooth IDF
        System.out.println("Building the ranker took: "+ (System.currentTimeMillis()-start)/1000 +" seconds.\n");

        TreeSet<ScoredDoc> query1 = ranker.query("stuttgart", "bahn");
        System.out.println("Query 1: stuttgart bahn");
        Ranker.printTopK(filename, query1, 10);

        TreeSet<ScoredDoc> query2 = ranker.query("popular", "political", "party");
        System.out.println("Query 2: popular political party");
        Ranker.printTopK(filename, query2, 10);

        TreeSet<ScoredDoc> query3 = ranker.query("running", "small", "business");
        System.out.println("Query 3: running small business");
        Ranker.printTopK(filename, query3, 10);
    }
}