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
    
    def search_query(self, query, results = {}):
        for word in query.split():
            word = self.strip_word(word)
            if word:
                filtered_statuses = self.search_word(word)
                for status_id in filtered_statuses:
                    if status_id not in results:
                        results[status_id] = filtered_statuses[status_id]
                    else:
                        results[status_id][0] += filtered_statuses[status_id][0]
        return results.values()
    
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
