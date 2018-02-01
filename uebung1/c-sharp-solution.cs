using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Exercise1 {

    class InvertedIndex {

        static Dictionary<string, EntryData> invertedDictionary;
        static Dictionary<ulong, string> tweetDictionary;
        //static bool debug = false;

        static void Main(string[] args) {
            GetFile();

            while (true) {
                Console.WriteLine("\nSearch term: ");
                string term = Console.ReadLine();
                Query(term);
                Console.WriteLine("\nSearch term A: ");
                string termA = Console.ReadLine();
                Console.WriteLine("\nSearch term B: ");
                string termB = Console.ReadLine();
                Query(termA, termB);
                Console.ReadLine();
            }
        }

        private static void Query(string termA, string termB) {
            if (invertedDictionary.TryGetValue(termA, out EntryData entryA)) {
                if (invertedDictionary.TryGetValue(termB, out EntryData entryB)) {

                    Console.WriteLine("\nquerying . . . \n");

                    int indexA = 0;
                    int indexB = 0;

                    List<ulong> postingsA = entryA.postingsListRef.Value;
                    List<ulong> postingsB = entryB.postingsListRef.Value;

                    string result = "";
                    bool matchFound = false;

                    while (indexA < postingsA.Count || indexB < postingsB.Count) {

                        if (postingsA[indexA] == postingsB[indexB]) {

                            matchFound = true;

                            if (tweetDictionary.TryGetValue(postingsA[indexA], out string text)) {

                                result += "--------------------------------------------" + "\nTweetID: " + postingsA[indexA].ToString() + "\nText: " + text + "\n";

                            } else {
                                result += "--------------------------------------------" + "\nTweetID: " + postingsA[indexA].ToString() + "\n";
                            }

                            if ((indexA + 1) < postingsA.Count) {
                                indexA += 1;
                            }
                            else {
                                break;
                            }
                        }

                        else if (postingsA[indexA] < postingsB[indexB]) {
                            if ((indexA + 1) < postingsA.Count) {
                                indexA += 1;
                            }
                            else {
                                break;
                            }
                        }

                        else {
                            if ((indexB + 1) < postingsB.Count) {
                                indexB += 1;
                            }
                            else {
                                break;
                            }
                        }
                    }

                    if (matchFound) {
                        Console.WriteLine("Result: \n" + result + "--------------------------------------------");
                    }
                    else {
                        Console.WriteLine("No match was found. \n");
                    }

                }
                else {
                    Console.WriteLine("Search term B was not found.");
                }
            }
            else {
                Console.WriteLine("Search term A was not found.");
            }
        }

        static void Query(string term) {
            if (invertedDictionary.TryGetValue(term, out EntryData entry)) {
                Console.WriteLine("\nSize: " + entry.size);
                List<ulong> postings = entry.postingsListRef.Value;
                foreach (ulong id in postings) {
                    if (tweetDictionary.TryGetValue(id, out string text)) {
                        Console.WriteLine("--------------------------------------------" + "\nTweetID: " + id + "\nText: " + text);
                    }
                    else {
                        Console.WriteLine("--------------------------------------------" + "\nTweetID: " + id);
                    }
                }

            }
            else {
                Console.WriteLine("Search term was not found.");
            }
            Console.WriteLine("--------------------------------------------");
        }

        static void GetFile() {
            Console.WriteLine("Path of the file:");
            string filename = Console.ReadLine();
            Index(filename);
        }

        static void Index(string filename) {
            Console.WriteLine("Indexing . . . ");
            Console.WriteLine();
            System.IO.StreamReader file = new System.IO.StreamReader(@"E:\Studium\Master\Text Mining\tweets");
            tweetDictionary = new Dictionary<ulong, string>();
            invertedDictionary = new Dictionary<string, EntryData>();

            //string line;
            //while ((line = file.ReadLine()) != null) {
            //    InsertDocument(line);
            //}

            for (int i = 0; i < 1000000; i++) {
                InsertDocument(file.ReadLine());
            }

            file.Close();
        }

        static void InsertDocument(string line) {
            string[] entries = line.Split('\t');
            string[] text = entries[entries.Length - 1].Split(null);

            tweetDictionary.Add(ulong.Parse(entries[1]), entries[entries.Length - 1]);

            List<string> terms = new List<string>();                        // list of terms in the given document (words in tweet text)
            foreach (string term in text) {
                if (invertedDictionary.TryGetValue(term, out EntryData entry)) {    // check if term is already in the dictionary
                    if (!terms.Contains(term)) {                            // check if this term was already inserted from this document
                        entry.size += 1;
                        //dictionary[term].size += 1;
                        entry.postingsListRef.Value.Add(ulong.Parse(entries[1]));
                        entry.postingsListRef.Value.Sort();
                        terms.Add(term);
                    }
                }
                else {                                                      // in case this is a new term create new entry in the dictionary
                    List<ulong> postingsList = new List<ulong>();
                    postingsList.Add(ulong.Parse(entries[1]));
                    var refPostings = new Ref<List<ulong>>(() => postingsList, x => { postingsList = x; });
                    invertedDictionary.Add(term, new EntryData(1, refPostings));
                }
            }

        }

    }

    public class EntryData {

        public int size;
        public Ref<List<ulong>> postingsListRef;

        public EntryData(int size, Ref<List<ulong>> postingsListRef) {
            this.size = size;
            this.postingsListRef = postingsListRef;
        }

    }

    // Delegate class since C# does not allow storing references to variables
    public class Ref<T> {
        private Func<T> getter;
        private Action<T> setter;
        public Ref(Func<T> getter, Action<T> setter) {
            this.getter = getter;
            this.setter = setter;
        }
        public T Value
        {
            get { return getter(); }
            set { setter(value); }
        }
    }



}
