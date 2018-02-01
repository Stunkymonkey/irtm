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
std::wifstream OpenFile(const char *filepath) {
  std::wifstream input{filepath};
  if (!input) {
    throw std::runtime_error(std::string{"Failed to open file "} + filepath);
  }
  return input;
}

/**
 * Normalizes a given string for usage in the dictionary of an index.
 */
void Normalize(std::wstring &str) {
  std::transform(str.begin(), str.end(), str.begin(), ::tolower);
}

/**
 * An inverted index containing a document list, a postings list and a
 * dictionary. The dictionary maps normalized terms to a subset of the postings
 * list, which contains the document IDs of the documents where the term occurs.
 */
class Index {
 private:
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
  Index(const char *filepath) {
    auto file_stream = OpenFile(filepath);
    ReadTweets(file_stream);
  }

  /**
   * Performs a query using a given term. The term doesn't need to be
   * normalized.
   * @return std::vector containing all document IDs where the term occurs.
   */
  std::vector<int32_t> Query(std::wstring term) {
    Normalize(term);
    std::vector<int32_t> result;
    if (auto dict_iter = m_dictionary.find(term);
        dict_iter != m_dictionary.end()) {
      const DictEntry &entry = dict_iter->second;
      for (auto term_iter = entry.begin; term_iter != entry.end; ++term_iter) {
        result.emplace_back(*term_iter);
      }
    }
    return result;
  }

  /**
   * Performs a conjunctive query using two given terms.
   * @return std::vector containing all document IDs where both terms occur.
   */
  std::vector<int32_t> Query(std::wstring term1, std::wstring term2) {
    Normalize(term1);
    Normalize(term2);
    std::vector<int32_t> result;
    auto dict_iter1 = m_dictionary.find(term1),
         dict_iter2 = m_dictionary.find(term2);
    if (dict_iter1 != m_dictionary.end() && dict_iter2 != m_dictionary.end()) {
      const DictEntry &entry1 = dict_iter1->second;
      const DictEntry &entry2 = dict_iter2->second;
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
    }
    return result;
  }

  /**
   * @param id The document ID of a document in this index.
   * @return The document with the given ID.
   */
  const std::wstring &Posting(int32_t id) { return m_tweets[id]; }

 private:
  /**
   * Loads entries from a character stream into this index.
   * @param input_stream The character stream to load from.
   */
  void ReadTweets(std::wistream &input_stream) {
    while (std::getline(input_stream, m_tweets.emplace_back())) {
      std::wistringstream line_stream{m_tweets.back()};
      int32_t doc_id = m_tweets.size() - 1;
      for (std::wstring term; line_stream >> term;) {
        Normalize(term);
        if (auto &entry = m_dictionary[std::move(term)]; entry.size == 0) {
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

  std::vector<std::wstring> m_tweets;
  std::list<int32_t> m_postingsList;
  std::unordered_map<std::wstring, DictEntry> m_dictionary;
};

/**
 * Constructs an inverted index from a file, performs the query "stuttgart" AND
 * "bahn" on it and prints the result.
 */
int main(int argc, char *argv[]) {
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
    for (int32_t id : idx.Query(L"stuttgart", L"bahn")) {
      output << "ID: " << id << "\tDocument: " << idx.Posting(id) << '\n';
    }
  } catch (const std::runtime_error &err) {
    std::cerr << "ERROR: " << err.what() << '\n';
  }
}
