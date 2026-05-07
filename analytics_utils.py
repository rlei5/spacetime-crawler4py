from bs4 import BeautifulSoup
from collections import Counter
from typing import Dict, Tuple, List


# default table was used from https://www.ranks.nl/stopwords
STOP_WORDS = ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
              "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
              "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
              "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
              "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
              "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
              "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more",
              "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
              "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd",
              "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their",
              "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
              "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we",
              "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
              "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
              "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"]

word_freq = {}
longest_page_url = ''
max_number_of_words = 0
seen_hashes = []

def _hash_word(word):
    # basic polynomial rolling hash: each character's position is weighted by powers of 31
    # 31 is a small prime that distributes bits well across 64 positions
    # ord() converts each character to its ASCII value
    # % (2**64) keeps the result within 64 bits
    h = 0
    for char in word:
        h = (h * 31 + ord(char)) % (2**64)
    return h

def get_simhash(tokens):
    weights = Counter(tokens)
    v = [0] * 64
    for word, weight in weights.items():
        word_hash = _hash_word(word)
        for i in range(64):
            if (word_hash >> i) & 1:
                v[i] += weight
            else:
                v[i] -= weight
    fingerprint = 0
    for i in range(64):
        if v[i] > 0:
            fingerprint |= (1 << i)
    return fingerprint

def is_near_duplicate(tokens, threshold=3):
    new_hash = get_simhash(tokens)
    for h in seen_hashes:
        if bin(new_hash ^ h).count('1') <= threshold:
            return True
    seen_hashes.append(new_hash)
    return False

def get_report_data() -> Tuple[Dict, Tuple[str, int]]:
    return find_top_fifty_words(), (longest_page_url, max_number_of_words)

def process_text(url, tokens) -> None:
    global word_freq
    global longest_page_url
    global max_number_of_words

    # longest page check
    if len(tokens) > max_number_of_words:
        max_number_of_words = len(tokens)
        longest_page_url = url

    # add to word frequencies
    page_word_frequencies = Counter(computeWordFrequencies(tokens))
    word_freq = Counter(word_freq) + page_word_frequencies

# note that each token is a word, so it's possible that the most common words might be single characters that are separated by apostrophes
def find_top_fifty_words() -> dict:
    sorted_items = sorted(word_freq.items(), key=lambda item: item[1], reverse=True)
    return dict(sorted_items[:50])

def computeWordFrequencies(tokens_list: List[str]) -> dict:
    tokens_dict = {}

    for token in tokens_list:
        if token in tokens_dict:
            tokens_dict[token] += 1
        else:
            tokens_dict[token] = 1

    return tokens_dict

# note that get_text() strips HTML tags
def tokenize(soup) -> List[str]:
    tokens = []
    output = soup.get_text()

    token = ''
    for line in output.splitlines():
        lower_case_line = line.lower()

        for char in lower_case_line:
            if is_valid(char):
                token += char
            else:
                if token != '' and len(token) > 1 and not is_stop_word(token): # dont get single letters
                    tokens.append(token)
                token = ''

        # if the line ends on a token
        if token != '' and len(token) > 1 and not is_stop_word(token):
            tokens.append(token)
        token = ''
    return tokens
def is_valid(char) -> bool:
    return ('a' <= char <= 'z') or ('0' <= char <= '9')

def is_stop_word(token) -> bool :
    return token in STOP_WORDS