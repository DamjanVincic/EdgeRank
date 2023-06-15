import csv
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

def calculate_user_affinity(user1, user2):
    affinity = 0

    if user2 in statuses:
        for status in statuses[user2]:
            status_affinity = 0
            if status.id in shares:
                for share in shares[status.id]:
                    if share.sharer == user1:
                        status_affinity += 2.0
            
            if status.id in reactions:
                for reaction in reactions[status.id]:
                    if reaction.reactor == user1:
                        reaction_time_decay = max(1, (datetime.now() - reaction.reaction_time).days)
                        if reaction.type == "likes":
                            status_affinity += 0.5 / reaction_time_decay
                        elif reaction.type == "loves":
                            status_affinity += 1.0 / reaction_time_decay
                        elif reaction.type == "wows":
                            status_affinity += 1.5 / reaction_time_decay
                        elif reaction.type =="hahas":
                            status_affinity += 0.5 / reaction_time_decay
                        elif reaction.type == "sads":
                            status_affinity += 0.25 / reaction_time_decay
                        elif reaction.type == "angrys":
                            status_affinity += 0.75 / reaction_time_decay

            if status.id in comments:
                for comment in comments[status.id]:
                    if comment.author == user1:
                        status_affinity += 1.0 / max(1, (datetime.now() - comment.publish_time).days)
            
            affinity += status_affinity

    return affinity

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

def create_graph(data):
    graph = nx.DiGraph()
    graph.add_nodes_from(data)
    for user1 in data:
        for user2 in data:
            if user1 != user2:
                weight = calculate_user_affinity(user1, user2)
                if weight != 0:
                    if user2 in friends[user1] or (graph.get_edge_data(user2, user1) is not None and graph.get_edge_data(user2, user1)['friends']):
                        graph.add_edge(user1, user2, weight = weight, friends = True)
                    else:
                        graph.add_edge(user1, user2, weight = weight, friends = False)
    return graph

def add_friend_affinities(graph):
    graph_copy = copy.deepcopy(graph)
    for node in graph.nodes:
        for neighbor in graph.neighbors(node):
            if graph.get_edge_data(node, neighbor)['friends']:
                for node2 in graph.neighbors(neighbor):
                    if node2 != node and node2 != neighbor:
                        if graph_copy.get_edge_data(node, node2) is None:
                            graph_copy.add_edge(node, node2, weight = graph.get_edge_data(neighbor, node2)['weight']/1000)
                        else:
                            graph_copy.get_edge_data(node, node2)['weight'] += graph.get_edge_data(neighbor, node2)['weight']/1000
            
            for ff in graph.neighbors(neighbor):
                if graph.get_edge_data(neighbor, ff)['friends']:
                    for node2 in graph.neighbors(ff):
                        if node2 != node and node2 != ff and node2 != neighbor:
                            if graph_copy.get_edge_data(node, node2) is None:
                                graph_copy.add_edge(node, node2, weight = graph.get_edge_data(ff, node2)['weight']/10000)
                            else:
                                graph_copy.get_edge_data(node, node2)['weight'] += graph.get_edge_data(ff, node2)['weight']/10000
    return graph_copy

def format_status(status):
    status_data = [
        ["Message", f"{status.message[:160]}..."],
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
    # users, friends = load_users("dataset/friends.csv")

    # for row in parse_files.load_statuses("dataset/original_statuses.csv"):
    #     status = Status(row[0], row[1], row[2], row[3], datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S"), row[5], int(row[6]), int(row[7]), int(row[8]), int(row[9]), int(row[10]), int(row[11]), int(row[12]), int(row[13]), int(row[14]))
    #     if status.author not in statuses:
    #         statuses[status.author] = [status]
    #     else:
    #         statuses[status.author].append(status)
    # for row in parse_files.load_statuses("dataset/test_statuses.csv"):
    #     status = Status(row[0], row[1], row[2], row[3], datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S"), row[5], int(row[6]), int(row[7]), int(row[8]), int(row[9]), int(row[10]), int(row[11]), int(row[12]), int(row[13]), int(row[14]))
    #     if status.author not in statuses:
    #         statuses[status.author] = [status]
    #     else:
    #         statuses[status.author].append(status)


    # for row in parse_files.load_shares("dataset/original_shares.csv"):
    #     share = Share(row[0], row[1], datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"))
    #     if share.status_id not in shares:
    #         shares[share.status_id] = [share]
    #     else:
    #         shares[share.status_id].append(share)
    # for row in parse_files.load_shares("dataset/test_shares.csv"):
    #     share = Share(row[0], row[1], datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"))
    #     if share.status_id not in shares:
    #         shares[share.status_id] = [share]
    #     else:
    #         shares[share.status_id].append(share)
    

    # for row in parse_files.load_reactions("dataset/original_reactions.csv"):
    #     reaction = Reaction(row[0], row[1], row[2], datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S"))
    #     if reaction.status_id not in reactions:
    #         reactions[reaction.status_id] = [reaction]
    #     else:
    #         reactions[reaction.status_id].append(reaction)
    # for row in parse_files.load_reactions("dataset/test_reactions.csv"):
    #     reaction = Reaction(row[0], row[1], row[2], datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S"))
    #     if reaction.status_id not in reactions:
    #         reactions[reaction.status_id] = [reaction]
    #     else:
    #         reactions[reaction.status_id].append(reaction)
    

    # for row in parse_files.load_comments("dataset/original_comments.csv"):
    #     comment = Comment(row[0], row[1], row[2], row[3], row[4], datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S"), int(row[6]), int(row[7]))
    #     if comment.status_id not in comments:
    #         comments[comment.status_id] = [comment]
    #     else:
    #         comments[comment.status_id].append(comment)
    # for row in parse_files.load_comments("dataset/test_comments.csv"):
    #     comment = Comment(row[0], row[1], row[2], row[3], row[4], datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S"), int(row[6]), int(row[7]))
    #     if comment.status_id not in comments:
    #         comments[comment.status_id] = [comment]
    #     else:
    #         comments[comment.status_id].append(comment)

    # with open("pickles/entities.pickle", "rb") as f:
    #     data = pickle.load(f)
    #     users = data["users"]
    #     friends = data["friends"]

    # dictionary = {"users": users, "friends": friends, "statuses": statuses, "shares": shares, "reactions": reactions, "comments": comments}
    # with open("pickles/test_entities.pickle", "wb") as f:
    #     pickle.dump(dictionary, f)

    # trie = Trie(reduce(lambda x, y: x + y, statuses.values()))
    # with open("pickles/test_trie.pickle", "wb") as f:
    #     pickle.dump(trie, f)

    # with open("pickles/trie.pickle", "rb") as f:
    #     trie = pickle.load(f)


    # with open("pickles/entities.pickle", "rb") as f:
    #     data = pickle.load(f)
    #     users = data["users"]
    #     friends = data["friends"]
    #     statuses = data["statuses"]
    #     shares = data["shares"]
    #     reactions = data["reactions"]
    #     comments = data["comments"]

    with open("pickles/test_entities.pickle", "rb") as f:
        data = pickle.load(f)
        users = data["users"]
        friends = data["friends"]
        statuses = data["statuses"]
        shares = data["shares"]
        reactions = data["reactions"]
        comments = data["comments"]

    # graph = create_graph(users)
    # with open("pickles/user_graph.pickle", "wb") as f:
    #     pickle.dump(graph, f)

    # with open("pickles/user_graph.pickle", "rb") as f:
    #     graph = pickle.load(f)

    with open("pickles/friend_user_graph.pickle", "rb") as f:
        graph = pickle.load(f)

    # graph = add_friend_affinities(graph)
    # with open("pickles/friend_user_graph.pickle", "wb") as f:
    #     pickle.dump(graph, f)

    # with open("pickles/trie.pickle", "rb") as f:
    #     trie = pickle.load(f)
    with open("pickles/test_trie.pickle", "rb") as f:
        trie = pickle.load(f)
    # trie = Trie(reduce(lambda x, y: x + y, statuses.values()))

    name = input("Enter a user's name: ").title()
    while name not in users:
        print("User with that name doesnt exist.")
        name = input("Enter a user's name: ").title()

    while True:
        print("[1] Get recommended statuses\n[2] Search\n[3] Log Out")
        try:
            choice = int(input("> "))
            if choice == 1:
                recommended_statuses = sorted(reduce(lambda x, y: x + y, statuses.values()), key = edgerank, reverse = True)
                for status in recommended_statuses[:10]:
                    # print(f"Affinity: {0 if graph.get_edge_data(name, status.author) is None else graph.get_edge_data(name, status.author)['weight']}, Weight: {calculate_status_weight(status)}, Edgerank: {edgerank(status)}, Time posted: {status.publish_time}")
                    # print(tabulate([[f"{status.message[:150]}...", status.author]], headers = ["Message", "Author"], tablefmt="fancy_grid"))
                    # print(format_status(status))
                    print_status(status)
            elif choice == 2:
                query = input("Enter search: ").lower()
                if query[-1] == '*':
                    print(", ".join(trie.search_prefix(query[:-1])))
                elif query[0] == '"' and query[-1] == '"':
                    results = trie.search_exact_query(query[1:-1].lower())
                    results.sort(key = edgerank, reverse = True)
                    for result in results[:10]:
                        # print(tabulate([[f"{result.message[:150]}...", result.author]], headers = ["Message", "Author"], tablefmt="fancy_grid"))
                        print_status(result)
                else:
                    results = list(trie.search_query(query))
                    results.sort(key = lambda result: result[0] + edgerank(result[1]), reverse = True)
                    results = list(map(lambda x: x[1], results))
                    for result in results[:10]:
                        # print(tabulate([[f"{result.message[:150]}...", result.author]], headers = ["Message", "Author"], tablefmt="fancy_grid"))
                        print_status(result)
            elif choice == 3:
                break
            else:
                raise Exception
        except:
            pass

    # with open("pickles/user_graph.pickle", 'wb') as f:
    #     pickle.dump(graph, f)
    
    # dictionary = {"users": users, "friends": friends, "statuses": statuses, "shares": shares, "reactions": reactions, "comments": comments}
    # with open("pickles/entities.pickle", "wb") as f:
    #     pickle.dump(dictionary, f)
