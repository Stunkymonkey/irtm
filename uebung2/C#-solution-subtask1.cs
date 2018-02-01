using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace MisspelledWords
{
    public class Program
    {
        // Misspelled word + number of occurences of the misspelling
        private static readonly Dictionary<string, int> MisspelledWords = new Dictionary<string, int>();

        // The dictionary containing correct words
        private static HashSet<string> _dictionaryHashset;

        // All distinct words found in the tweets
        private static readonly HashSet<string> TweetWordsSet = new HashSet<string>();

        // Monolith for readability purpouses
        public static void Main(string[] args)
        {
            Console.WriteLine("Welcome to your favourite tweet utility!");
            Console.WriteLine();

            // The dictionary AND the tweets should both be in the same directory in which the .exe file is
            var dictionaryPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, @"dictionary");
            var tweetsPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, @"tweets");

            Console.WriteLine("Parsing dictionary...");
            string[] dictionary = File.ReadAllLines(dictionaryPath);

            Console.WriteLine("Lowercasing all dictionary entries...");
            dictionary = dictionary.Select(s => s.ToLowerInvariant()).ToArray();

            _dictionaryHashset = new HashSet<string>(dictionary);

            Console.WriteLine();

            Console.WriteLine("Parsing tweets...");
            string[] tweetTexts = File.ReadAllLines(tweetsPath).Select(tweet => tweet.Split('\t').Last()).ToArray();

            Console.WriteLine("Removing newline from tweet texts...");
            tweetTexts = tweetTexts.Select(text => Regex.Replace(text, @"\[NEWLINE\]", " ")).ToArray();

            Console.WriteLine("Removing URLs tags from tweet texts...");
            tweetTexts = tweetTexts.Select(text => Regex.Replace(text, @"http[^\s]+", " ")).ToArray();

            Console.WriteLine("Removing hashtags from tweet texts...");
            tweetTexts = tweetTexts.Select(text => Regex.Replace(text, @"#[^\s]+", " ")).ToArray();

            Console.WriteLine("Removing everything non-alphabetic from tweet texts...");
            tweetTexts = tweetTexts.Select(text => new string(text.Where(c => char.IsLetter(c) || char.IsWhiteSpace(c)).ToArray())).ToArray();

            Console.WriteLine("Removing empty values from tweet texts...");
            tweetTexts = tweetTexts.Where(x => !string.IsNullOrEmpty(x)).ToArray();

            Console.WriteLine("Lowercasing all tweet texts...");
            tweetTexts = tweetTexts.Select(text => text.ToLowerInvariant()).ToArray();

            // Extract all words from the tweet texts
            foreach (var text in tweetTexts)
            {
                // Split by whitespace
                text.Split(null).ToList().ForEach(t => TweetWordsSet.Add(t));
            }

            Console.WriteLine();
            Console.WriteLine($"Found {TweetWordsSet.Count} distinct words. Starting spelling check:"); 

            int currentWordCount = 0;
            foreach (var word in TweetWordsSet)
            {
                if (currentWordCount % 10000 == 0)
                {
                    var progressResultLines = MisspelledWords.OrderByDescending(entry => entry.Value).Select(kvp => kvp.Key + " : " + kvp.Value.ToString());

                    Console.WriteLine();
                    Console.WriteLine("Spellchecking results ordered by frequency of appearence.");
                    Console.WriteLine("Misspelled word : Number of occurences.");
                    Console.WriteLine(string.Join(Environment.NewLine, progressResultLines));
                }

                currentWordCount++;
                Console.WriteLine();
                Console.WriteLine($"Spellchecking the word '{word}' ({currentWordCount} out of {TweetWordsSet.Count})");
                SpellcheckWord(word);  
            }

            var resultLines = MisspelledWords.OrderByDescending(entry => entry.Value).Select(kvp => kvp.Key + " : " + kvp.Value.ToString());

            Console.WriteLine();
            Console.WriteLine("Spellchecking results ordered by frequency of appearence.");
            Console.WriteLine("Misspelled word : Number of occurences.");
            Console.WriteLine(string.Join(Environment.NewLine, resultLines));

            Console.ReadLine();
        }

        private static void SpellcheckWord(string candidateWord)
        {
            if (_dictionaryHashset.Contains(candidateWord))
            {
                Console.WriteLine($"The word '{candidateWord}' was found in the dictionary and is thus correct!");
                return;
            }

            int maxEditDistance = 1;

            // Bigger words can have more spelling errors
            if (candidateWord.Length > 4)
                maxEditDistance = 2;

            foreach (var correctWord in _dictionaryHashset)
            {
                int editDistance = ComputeDamerauLevenshteinDistance(candidateWord, correctWord, maxEditDistance);

                if (editDistance >= 0 && editDistance <= maxEditDistance)
                {
                    if (MisspelledWords.ContainsKey(correctWord))
                    {
                        MisspelledWords[correctWord] += 1;
                        Console.WriteLine($"Found the {MisspelledWords[correctWord]} occurence of the misspelled word: {correctWord}.");
                        return;
                    }

                    MisspelledWords.Add(correctWord, 1);
                    Console.WriteLine($"Found a new misspelled word: {correctWord}.");
                    return;
                }
            }
            Console.WriteLine($"Found an unknown word: {candidateWord}");
        }

        #region DamerauLevenshtein

        // Implementation taken from here: https://github.com/wolfgarbe/SymSpell/blob/master/symspell/DamerauLevenshtein/DamerauLevenshtein.cs
        public static int ComputeDamerauLevenshteinDistance(string string1, string string2, int maxDistance)
        {
            if (String.IsNullOrEmpty(string1)) return (string2 ?? "").Length;
            if (String.IsNullOrEmpty(string2)) return string1.Length;

            // if strings of different lengths, ensure shorter string is in string1. This can result in a little
            // faster speed by spending more time spinning just the inner loop during the main processing.
            if (string1.Length > string2.Length)
            {
                var temp = string1; string1 = string2; string2 = temp; // swap string1 and string2
            }
            int sLen = string1.Length; // this is also the minimun length of the two strings
            int tLen = string2.Length;

            // suffix common to both strings can be ignored
            while ((sLen > 0) && (string1[sLen - 1] == string2[tLen - 1])) { sLen--; tLen--; }

            int start = 0;
            if ((string1[0] == string2[0]) || (sLen == 0))
            { // if there'string1 a shared prefix, or all string1 matches string2'string1 suffix
                // prefix common to both strings can be ignored
                while ((start < sLen) && (string1[start] == string2[start])) start++;
                sLen -= start; // length of the part excluding common prefix and suffix
                tLen -= start;

                // if all of shorter string matches prefix and/or suffix of longer string, then
                // edit distance is just the delete of additional characters present in longer string
                if (sLen == 0) return tLen;

                string2 = string2.Substring(start, tLen); // faster than string2[start+j] in inner loop below
            }
            int lenDiff = tLen - sLen;
            if ((maxDistance < 0) || (maxDistance > tLen))
            {
                maxDistance = tLen;
            }
            else if (lenDiff > maxDistance) return -1;

            var v0 = new int[tLen];
            var v2 = new int[tLen]; // stores one level further back (offset by +1 position)
            int j;
            for (j = 0; j < maxDistance; j++) v0[j] = j + 1;
            for (; j < tLen; j++) v0[j] = maxDistance + 1;

            int jStartOffset = maxDistance - (tLen - sLen);
            bool haveMax = maxDistance < tLen;
            int jStart = 0;
            int jEnd = maxDistance;
            char sChar = string1[0];
            int current = 0;
            for (int i = 0; i < sLen; i++)
            {
                char prevsChar = sChar;
                sChar = string1[start + i];
                char tChar = string2[0];
                int left = i;
                current = left + 1;
                int nextTransCost = 0;
                // no need to look beyond window of lower right diagonal - maxDistance cells (lower right diag is i - lenDiff)
                // and the upper left diagonal + maxDistance cells (upper left is i)
                jStart += (i > jStartOffset) ? 1 : 0;
                jEnd += (jEnd < tLen) ? 1 : 0;
                for (j = jStart; j < jEnd; j++)
                {
                    int above = current;
                    int thisTransCost = nextTransCost;
                    nextTransCost = v2[j];
                    v2[j] = current = left; // cost of diagonal (substitution)
                    left = v0[j];    // left now equals current cost (which will be diagonal at next iteration)
                    char prevtChar = tChar;
                    tChar = string2[j];
                    if (sChar != tChar)
                    {
                        if (left < current) current = left;   // insertion
                        if (above < current) current = above; // deletion
                        current++;
                        if ((i != 0) && (j != 0)
                            && (sChar == prevtChar)
                            && (prevsChar == tChar))
                        {
                            thisTransCost++;
                            if (thisTransCost < current) current = thisTransCost; // transposition
                        }
                    }
                    v0[j] = current;
                }
                if (haveMax && (v0[i + lenDiff] > maxDistance)) return -1;
            }
            return (current <= maxDistance) ? current : -1;
        }

        #endregion
    }
}
