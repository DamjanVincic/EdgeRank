import csv
import colorama
import networkx as nx
from datetime import datetime
import pickle
from functools import reduce
from tabulate import tabulate
import copy
import parse_files
from entities.status import Status
from entities.comment import Comment
from entities.share import Share
from entities.reaction import Reaction
from entities.trie import Trie

users = set()
friends = {}
statuses = {}
shares = {}
reactions = {}
comments = {}

def calculate_status_weight(status):
    weight = 0
    weight += status.comment_count*1.0 + status.share_count*2.0 + status.like_count*0.5 + status.num_loves*1.0 + status.num_wows*1.5 + status.num_hahas*0.5 * status.num_sads*0.25 + status.num_angrys*0.25
    difference = (datetime.now() - status.publish_time).days
    if difference < 1:
        time_decay = 1
    elif difference < 3:
        time_decay = 5*difference
    else:
        time_decay = 20*difference
    weight /= time_decay
    return weight

def edgerank(status):
    rank = calculate_status_weight(status)
    edge = graph.get_edge_data(name, status.author)
    if edge is not None:
        rank += graph.get_edge_data(name, status.author)['weight']
    rank /= max(1, (datetime.now() - status.publish_time).days)
    return rank

def load_users(path):
    users = set()
    friends = {}
    with open(path, encoding = 'utf-8') as f:
        reader = csv.reader(f)
        data = list(reader)
        for row in data[1:]:
            users.add(row[0])
            users.update(row[2:])
            friends[row[0]] = row[2:]
    return users, friends

def create_graph():
    graph = nx.DiGraph()
    graph.add_nodes_from(users)

    for user in friends:
        for friend in friends[user]:
            graph.add_edge(user, friend, weight = 3.0, friends = True)
            graph.add_edge(friend, user, weight = 3.0, friends = True)

    for share in reduce(lambda x, y: x + y, shares.values()):
        user1 = share.sharer
        user2 = statuses[share.status_id].author
        if graph.get_edge_data(user1, user2) is None:
            graph.add_edge(user1, user2, weight = 2.0 / max(1, (datetime.now() - share.share_time).days), friends = False)
        else:
            graph.get_edge_data(user1, user2)['weight'] += 2.0 / max(1, (datetime.now() - share.share_time).days)
        if user2 in friends[user1] or (graph.get_edge_data(user2, user1) is not None and graph.get_edge_data(user2, user1)['friends']):
            graph.get_edge_data(user1, user2)['friends'] = True
    
    reaction_weights = {"likes": 0.5, "loves": 1.0, "wows": 1.5, "hahas": 0.5, "sads": 0.25, "angrys": 0.75, "special": 0}
    for reaction in reduce(lambda x, y: x + y, reactions.values()):
        user1 = reaction.reactor
        user2 = statuses[reaction.status_id].author

        if graph.get_edge_data(user1, user2) is None:
            graph.add_edge(user1, user2, weight = reaction_weights[reaction.type] / max(1, (datetime.now() - reaction.reaction_time).days), friends = False)
        else:
            graph.get_edge_data(user1, user2)['weight'] += reaction_weights[reaction.type] / max(1, (datetime.now() - reaction.reaction_time).days)
        if user2 in friends[user1] or (graph.get_edge_data(user2, user1) is not None and graph.get_edge_data(user2, user1)['friends']):
            graph.get_edge_data(user1, user2)['friends'] = True

    for comment in reduce(lambda x, y: x + y, comments.values()):
        user1 = comment.author
        user2 = statuses[comment.status_id].author
        if graph.get_edge_data(user1, user2) is None:
            graph.add_edge(user1, user2, weight = 1.0 / max(1, (datetime.now() - comment.publish_time).days), friends = False)
        else:
            graph.get_edge_data(user1, user2)['weight'] += 1.0 / max(1, (datetime.now() - comment.publish_time).days)
        if user2 in friends[user1] or (graph.get_edge_data(user2, user1) is not None and graph.get_edge_data(user2, user1)['friends']):
            graph.get_edge_data(user1, user2)['friends'] = True

    return graph

def add_friend_affinities(graph):
    graph_copy = copy.deepcopy(graph)
    for node in graph.nodes:
        for friend in friends[node]:
            for node2 in graph.neighbors(friend):
                if node2 != node and node2 != friend:
                    if graph_copy.get_edge_data(node, node2) is None:
                        graph_copy.add_edge(node, node2, weight = graph.get_edge_data(friend, node2)['weight']/1000, friends = False)
                    else:
                        graph_copy.get_edge_data(node, node2)['weight'] += graph.get_edge_data(friend, node2)['weight']/1000

            for ff in friends[friend]:
                for node2 in graph.neighbors(ff):
                    if node2 != node and node2 != ff:
                        if graph_copy.get_edge_data(node, node2) is None:
                            graph_copy.add_edge(node, node2, weight = graph.get_edge_data(ff, node2)['weight']/1000, friends = False)
                        else:
                            graph_copy.get_edge_data(node, node2)['weight'] += graph.get_edge_data(ff, node2)['weight']/1000
    return graph_copy

def format_status(status):
    status_data = [
        ["Message", f"{status.message[:160]}{colorama.Style.RESET_ALL}..."],
        ["Author", status.author],
        ["Publish Time", status.publish_time],
        ["Reactions", status.reaction_count],
        ["Comments", status.comment_count],
        ["Shares", status.share_count]
    ]
    table = tabulate(status_data, headers=["", "New Post"], tablefmt="fancy_grid")
    return table

def print_status(status):
    print(f"Message: {status.message}\nAuthor: {status.author}\nPublish Time: {status.publish_time}\nReactions: {status.reaction_count}\nComments: {status.comment_count}\nShares: {status.share_count}\n\n------\n")

if __name__ == "__main__":
    colorama.init()

    users, friends = load_users("dataset/friends.csv")

    for row in parse_files.load_statuses("dataset/original_statuses.csv"):
        status = Status(row[0], row[1], row[2], row[3], datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S"), row[5], int(row[6]), int(row[7]), int(row[8]), int(row[9]), int(row[10]), int(row[11]), int(row[12]), int(row[13]), int(row[14]))
        statuses[status.id] = status
    for row in parse_files.load_statuses("dataset/test_statuses.csv"):
        status = Status(row[0], row[1], row[2], row[3], datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S"), row[5], int(row[6]), int(row[7]), int(row[8]), int(row[9]), int(row[10]), int(row[11]), int(row[12]), int(row[13]), int(row[14]))
        statuses[status.id] = status
    

    for row in parse_files.load_shares("dataset/original_shares.csv"):
        share = Share(row[0], row[1], datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"))
        if share.sharer not in shares:
            shares[share.sharer] = [share]
        else:
            shares[share.sharer].append(share)
    for row in parse_files.load_shares("dataset/test_shares.csv"):
        share = Share(row[0], row[1], datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"))
        if share.sharer not in shares:
            shares[share.sharer] = [share]
        else:
            shares[share.sharer].append(share)


    for row in parse_files.load_reactions("dataset/original_reactions.csv"):
        reaction = Reaction(row[0], row[1], row[2], datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S"))
        if reaction.reactor not in reactions:
            reactions[reaction.reactor] = [reaction]
        else:
            reactions[reaction.reactor].append(reaction)
    for row in parse_files.load_reactions("dataset/test_reactions.csv"):
        reaction = Reaction(row[0], row[1], row[2], datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S"))
        if reaction.reactor not in reactions:
            reactions[reaction.reactor] = [reaction]
        else:
            reactions[reaction.reactor].append(reaction)


    for row in parse_files.load_comments("dataset/original_comments.csv"):
        comment = Comment(row[0], row[1], row[2], row[3], row[4], datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S"), int(row[6]), int(row[7]))
        if comment.author not in comments:
            comments[comment.author] = [comment]
        else:
            comments[comment.author].append(comment)
    for row in parse_files.load_comments("dataset/test_comments.csv"):
        comment = Comment(row[0], row[1], row[2], row[3], row[4], datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S"), int(row[6]), int(row[7]))
        if comment.author not in comments:
            comments[comment.author] = [comment]
        else:
            comments[comment.author].append(comment)


    graph = create_graph()
    trie = Trie(statuses.values())

    with open("pickles/test/user_graph.pickle", "wb") as f:
        pickle.dump(graph, f)
    
    data = {"users": users, "friends": friends, "statuses": statuses, "shares": shares, "reactions": reaction, "comments": comments}
    with open("pickles/test/entities.pickle", "wb") as f:
        pickle.dump(data, f)

    with open("pickles/test/trie.pickle", "wb") as f:
        pickle.dump(trie, f)

    
    name = input("Enter a user's name: ").title()
    while name not in users:
        print("User with that name doesnt exist.")
        name = input("Enter a user's name: ").title()

    while True:
        print("[1] Get recommended statuses\n[2] Search\n[3] Log Out")
        try:
            choice = int(input("> "))
            if choice == 1:
                recommended_statuses = sorted(statuses.values(), key = edgerank, reverse = True)
                for status in recommended_statuses[:10]:
                    print_status(status)
            elif choice == 2:
                query = input("Enter search: ").lower()
                if query[-1] == '*':
                    print(", ".join(trie.search_prefix(query[:-1])))
                elif query[0] == '"' and query[-1] == '"':
                    results = trie.search_exact_query(query[1:-1].lower())
                    results.sort(key = edgerank, reverse = True)
                    for result in results[:10]:
                        print_status(result)
                else:
                    results = list(trie.search_query(query))
                    results.sort(key = lambda result: result[0] + edgerank(result[1]), reverse = True)
                    results = list(map(lambda x: x[1], results))
                    for result in results[:10]:
                        print_status(result)
            elif choice == 3:
                break
            else:
                raise Exception
        except:
            pass
