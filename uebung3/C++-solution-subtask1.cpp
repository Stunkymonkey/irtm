/*
Copyright 2017 Sebastian Hasler

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

#include <algorithm>
#include <cmath>
#include <codecvt>
#include <fstream>
#include <iostream>
#include <istream>
#include <iterator>
#include <list>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

/**
 * Opens an UTF-8 encoded file as an input stream using wchar_t.
 * @param filepath Path to the file.
 * @return std::wifstream representing the file's content.
 */
std::wifstream OpenFile(const char* filepath) {
  std::wifstream input{filepath};
  if (!input) {
    throw std::runtime_error(std::string{"Failed to open file "} + filepath);
  }
  return input;
}

/** Normalizes a given string for usage in the dictionary of an index. */
void Normalize(std::wstring& str) {
  std::transform(str.begin(), str.end(), str.begin(), ::tolower);
}

/** Class for spelling correction that privide one static method Correct(). */
class SpellingCorrection {
 public:
  /**
   * Corrects a given word if there exists a known english word with a
   * levenshtein distance to the given word of at most 2.
   * @param givenWord The word to correct (in/out-parameter).
   * @return true iff the word has been corrected or was already correctly
   * spelled.
   */
  static bool Correct(std::wstring& givenWord) {
    Normalize(givenWord);
    int32_t minDist = std::numeric_limits<int32_t>::max();
    std::wstring corrected;
    int32_t dist = 0;
    for (int64_t i = 0; i < static_cast<int64_t>(m_words.size()); ++i) {
      const auto& correctWord = m_words[i];
      if (dist < minDist) {
        dist = levenshteinDistance(correctWord, givenWord);
        if (dist < minDist) {
          corrected = correctWord;
          minDist = dist;
          if (minDist == 0) break;
        }
      }
      dist -= m_distancesToNext[i];
    }
    if (minDist <= 2) {
      givenWord = corrected;
      return true;
    }
    return false;
  }

 private:
  /** @return Levenshtein distance of s1 and s2. */
  static int32_t levenshteinDistance(const std::wstring& s1,
                                     const std::wstring& s2) {
    const int32_t len1 = static_cast<int32_t>(s1.size()),
                  len2 = static_cast<int32_t>(s2.size());
    std::vector<int32_t> col(len2 + 1), prevCol(len2 + 1);
    for (int32_t i = 0; i < prevCol.size(); i++) {
      prevCol[i] = i;
    }
    for (int32_t i = 0; i < len1; i++) {
      col[0] = i + 1;
      for (int32_t j = 0; j < len2; j++)
        col[j + 1] = std::min({prevCol[1 + j] + 1, col[j] + 1,
                               prevCol[j] + (s1[i] == s2[j] ? 0 : 1)});
      col.swap(prevCol);
    }
    return prevCol[len2];
  }

  /*
   * Reads all lines from a file and normalizes them. If consecutive lines equal
   * after normalization, only one of them is contained in the result.
   * @param filepath Path to the file to read from.
   * @return std::vector of containing the normalized lines ordered as read.
   */
  static std::vector<std::wstring> ReadWordsFromFile(const char* filepath) {
    std::wifstream input_stream{filepath};
    std::vector<std::wstring> result;
    std::wstring line;
    while (std::getline(input_stream, line)) {
      Normalize(line);
      if (result.empty() || result.back() != line) {
        result.emplace_back(std::move(line));
      }
    }
    return result;
  }

  /**
   * For each word in m_words, calculates the levenshtein distance to the
   * succeeding word in the list.
   * @return std::vector with the same size as m_words, containing the
   * calculated distances. The last entry (refering to the last word in m_words)
   * is a 0.
   */
  static std::vector<int32_t> CalcDistancesToNext() {
    std::vector<int32_t> result;
    result.reserve(m_words.size());
    for (int64_t i = 0; i + 1 < static_cast<int64_t>(m_words.size()); ++i) {
      result.emplace_back(levenshteinDistance(m_words[i], m_words[i + 1]));
    }
    result.emplace_back(0);
    return result;
  }

  static std::vector<std::wstring> m_words;
  static std::vector<int32_t> m_distancesToNext;
};

// Initialize the static members of SpellingCorrection
std::vector<std::wstring> SpellingCorrection::m_words =
    SpellingCorrection::ReadWordsFromFile("english-words");
std::vector<int32_t> SpellingCorrection::m_distancesToNext =
    SpellingCorrection::CalcDistancesToNext();

/**
 * An inverted index containing a document list, a postings list and a
 * dictionary. The dictionary maps normalized terms to a subset of the postings
 * list, which contains the document IDs of the documents where the term occurs.
 */
class Index {
  class DictEntry {
   public:
    std::list<int32_t>::const_iterator begin;
    std::list<int32_t>::const_iterator end;
    int32_t size = 0;
  };

 public:
  /**
   * Default constructor. Constructs an index with no documents and an empty
   * dictionary.
   */
  Index() = default;

  /**
   * Constructor loading the index from a file.
   * @param filepath Path to the file.
   */
  Index(const char* filepath) {
    auto file_stream = OpenFile(filepath);
    ReadTweets(file_stream);
  }

  /**
   * Performs a query using a given term. The term doesn't need to be
   * normalized.
   * @return std::vector containing all document IDs where the term occurs.
   */
  std::vector<int32_t> Query(std::wstring term) {
    SpellingCorrection::Correct(term);
    std::vector<int32_t> result;
    if (auto dict_iter = m_dictionary.find(term);
        dict_iter != m_dictionary.end()) {
      const DictEntry& entry = dict_iter->second;
      for (auto term_iter = entry.begin; term_iter != entry.end; ++term_iter) {
        result.emplace_back(*term_iter);
      }
      Rank(result, {term});  ////////////////////////////////////////// modified
    }
    return result;
  }

  /**
   * Performs a conjunctive query using two given terms.
   * @return std::vector containing all document IDs where both terms occur.
   */
  std::vector<int32_t> Query(std::wstring term1, std::wstring term2) {
    SpellingCorrection::Correct(term1);
    SpellingCorrection::Correct(term2);
    std::vector<int32_t> result;
    auto dict_iter1 = m_dictionary.find(term1),
         dict_iter2 = m_dictionary.find(term2);
    if (dict_iter1 != m_dictionary.end() && dict_iter2 != m_dictionary.end()) {
      const DictEntry& entry1 = dict_iter1->second;
      const DictEntry& entry2 = dict_iter2->second;
      auto plist_iter1 = entry1.begin, plist_iter2 = entry2.begin;
      while (plist_iter1 != entry1.end && plist_iter2 != entry2.end) {
        if (*plist_iter1 == *plist_iter2) {
          result.emplace_back(*plist_iter1);
          ++plist_iter1;
          ++plist_iter2;
        } else if (*plist_iter1 < *plist_iter2) {
          ++plist_iter1;
        } else {
          ++plist_iter2;
        }
      }
      Rank(result, {term1, term2});  ////////////////////////////////// modified
    }
    return result;
  }

  /**
   * @param id The document ID of a document in this index.
   * @return The document with the given ID.
   */
  const std::wstring& Posting(int32_t id) { return m_tweets[id]; }

 private:
  /**
   * Loads entries from a character stream into this index.
   * @param input_stream The character stream to load from.
   */
  void ReadTweets(std::wistream& input_stream) {
    while (std::getline(input_stream, m_tweets.emplace_back())) {
      std::wistringstream line_stream{m_tweets.back()};
      int32_t doc_id = m_tweets.size() - 1;
      for (std::wstring term; line_stream >> term;) {
        Normalize(term);
        if (auto& entry = m_dictionary[std::move(term)]; entry.size == 0) {
          m_postingsList.emplace_front(doc_id);
          entry.begin = m_postingsList.begin();
          entry.end = std::next(entry.begin);
          entry.size = 1;
        } else if (*std::prev(entry.end) != doc_id) {
          m_postingsList.insert(entry.end, doc_id);
          ++entry.size;
        }
      }
    }
  }

  //////////////////////////////////////////////////////////////////////////////
  // MODIFICATION BEGIN
  //////////////////////////////////////////////////////////////////////////////

  /**
   * Calculates a tf matching score per 1+log(tf). The score is 0 if the term
   * doesn't occur.
   * @param id ID of the document to count the occurences of the
   * term in.
   * @param term The term to count the occurences of.
   * @return The calculated tf matching score.
   */
  double TfMatchingScore(int32_t id, const std::wstring& term) {
    int32_t tf = 0;
    std::wistringstream doc_stream{m_tweets[id]};
    for (std::wstring other_term; doc_stream >> other_term;) {
      Normalize(other_term);
      if (other_term == term) ++tf;
    }
    if (tf == 0) return 0;
    return 1 + std::log(static_cast<double>(tf));
  }

  /**
   * Calculates an inverse document frequency weight per log(N/df) where N is
   * the total number of tweets.
   * @param term The term to count the number of documents it occurs in.
   * @return The caulculated idf-weight weight.
   * @throws std::logic_error if the term doesn't occur in the dictionary.
   */
  double IdfWeight(const std::wstring& term) {
    auto dict_iter = m_dictionary.find(term);
    if (dict_iter == m_dictionary.end())
      throw std::logic_error("Term doesn't occur in the dictionary.");
    const DictEntry& entry = dict_iter->second;
    auto df = std::distance(entry.begin, entry.end);
    auto N = m_tweets.size();
    return std::log(static_cast<double>(N) / df);
  }

  /**
   * Calculates a tf-idf weight.
   * @param id ID of a document in this dictionary.
   * @param term A term to calculate the weight of, with respect to the
   * given document.
   * @return The calculated tf-idf weight.
   */
  double TfIdfWeight(int32_t id, const std::wstring& term) {
    return TfMatchingScore(id, term) * IdfWeight(term);
  }

  /**
   * Calculates the tf-idf weights for multiple documents and multiple terms.
   * @param ids std::vector of the document IDs to consider.
   * @param terms std::vector of the terms to consider.
   * @return std::unordered_map where the keys are the given document IDs and
   * the values are the sum of the tf-idf weights of the given terms with
   * respect to the document identified by the key.
   * @throws std::logic_error if any of the terms doesn't occur in the
   * dictionary.
   */
  std::unordered_map<int32_t, double> TfIdfWeights(
      const std::vector<int32_t>& ids, const std::vector<std::wstring>& terms) {
    std::unordered_map<int32_t, double> result;
    for (int32_t doc : ids) {
      double& weight = result[doc];
      for (const std::wstring& term : terms) {
        weight += TfIdfWeight(doc, term);
      }
    }
    return result;
  }

  /**
   * Ranks (i.e. sorts) a collection of documents based tf-idf-weights of
   * given terms. If multiple terms are provided, the sum of the tf-idf-weights
   * is taken to rank the documents.
   * @param ids IDs of the documents to rank.
   * @param terms The terms to calculate the tf-idf-weights of.
   * @throws std::logic_error if any of the terms doesn't occur in the
   */
  void Rank(std::vector<int32_t>& ids, const std::vector<std::wstring>& terms) {
    auto weights = TfIdfWeights(ids, terms);
    auto comp = [&weights](int32_t lhs, int32_t rhs) {
      return weights[lhs] > weights[rhs];
    };
    std::sort(ids.begin(), ids.end(), comp);
  }

  //////////////////////////////////////////////////////////////////////////////
  // MODIFICATION END
  //////////////////////////////////////////////////////////////////////////////

  std::vector<std::wstring> m_tweets;
  std::list<int32_t> m_postingsList;
  std::unordered_map<std::wstring, DictEntry> m_dictionary;
};

/**
 * Constructs an inverted index from a file, performs the query "stuttgart" AND
 * "bahn" on it and prints the result.
 */
int main(int argc, char* argv[]) {
  std::locale::global({std::locale{}, new std::codecvt_utf8<wchar_t>});
  try {
    Index idx;
    switch (argc) {
      case 0:
      case 1:
        idx = Index{"tweets"};
        break;
      case 2:
        idx = Index{argv[1]};
        break;
      default:
        throw std::runtime_error("Too many command line arguments.");
    }
    std::wofstream output{"output.txt"};
    output << L'\uFEFF';  // utf-8 byte order mark
    for (int32_t id : idx.Query(L"The", L"true")) {
      output << "ID: " << id << "\tDocument: " << idx.Posting(id) << '\n';
    }
  } catch (const std::runtime_error& err) {
    std::cerr << "ERROR: " << err.what() << '\n';
  }
}
