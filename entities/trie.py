import copy
from colorama import Fore, Style
import string

class TrieNode(object):
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.statuses = {}

class Trie(object):
    def __init__(self, statuses):
        self.root = TrieNode()

        for status in statuses:
            for word in status.message.split():
                self.insert_word(self.strip_word(word).lower(), status)


    def insert_word(self, word, status):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        if status.id not in node.statuses:
            node.statuses[status.id] = [1, status]
        else:
            node.statuses[status.id][0] += 1 # number of appearances
        node.is_end_of_word = True

    def search_word(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return {}
            node = node.children[char]
        return node.statuses if node.is_end_of_word else {}
    
    def strip_word(self, word):
        word = word.strip()
        additional_chars = string.punctuation + '“”‘’:'
        word = word.translate(str.maketrans('', '', additional_chars))
        word = word.replace("'", "").replace('"', '')
        return word
    
    def search_query(self, query):
        results = {}
        for idx, word in enumerate(query.split(), start = 1):
            word = self.strip_word(word).lower()
            if word:
                filtered_statuses = self.search_word(word)
                for status_id in filtered_statuses:
                    if status_id not in results:
                        results[status_id] = copy.deepcopy(filtered_statuses[status_id])
                    else:
                        results[status_id][0] += filtered_statuses[status_id][0]
                        if idx == len(query.split()):
                            results[status_id][0] += 10
                    
                    results[status_id][1].message = self.highlight_text(word, results[status_id][1].message)
        return results.values()
    
    def search_exact_query(self, query):
        results = []
        filtered_statuses = self.search_word(self.strip_word(query.split()[0]))
        for status_id in filtered_statuses:
            if query in ' '.join([self.strip_word(word).lower() for word in filtered_statuses[status_id][1].message.split()]):
                results.append(filtered_statuses[status_id][1])
        return results
    
    def search_prefix(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        return self.get_words_from_prefix(node, prefix)

    def get_words_from_prefix(self, node, prefix):
        words = []
        if node.is_end_of_word:
            words.append(prefix)
        for char, child in node.children.items():
            words.extend(self.get_words_from_prefix(child, prefix + char))
        return words
    
    def highlight_text(self, word, text):
        indexes = [i for i in range(len(text)) if text.lower().startswith(word, i)]
        offset = 0
        for index in indexes:
            index += offset
            text = f"{text[:index]}{Fore.RED}{text[index:index+len(word)]}{Style.RESET_ALL}{text[index+len(word):]}"
            offset += len(Fore.RED) + len(Style.RESET_ALL)
        return text
