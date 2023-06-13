import csv
import networkx as nx
from datetime import datetime
import pickle
from functools import reduce
from tabulate import tabulate
import parse_files
from entities.status import Status
from entities.comment import Comment
from entities.share import Share
from entities.reaction import Reaction

users = {}
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

def load_users(path):
    users = {}
    with open(path, encoding = 'utf-8') as f:
        reader = csv.reader(f)
        data = list(reader)
        for row in data[1:]:
            users[row[0]] = row[2:]
    return users

def create_graph(data):
    graph = nx.DiGraph()
    for user, friends in data.items():
        graph.add_node(user)
        for friend in friends:
            graph.add_node(friend)
            graph.add_edge(user, friend, weight = calculate_user_affinity(user, friend))
            graph.add_edge(friend, user, weight = calculate_user_affinity(friend, user))
    return graph

if __name__ == "__main__":
    with open("entities.pickle", "rb") as f:
        data = pickle.load(f)
        users = data["users"]
        statuses = data["statuses"]
        shares = data["shares"]
        reactions = data["reactions"]
        comments = data["comments"]
    

    with open("user_graph.pickle", "rb") as f:
        graph = pickle.load(f)


    # users = load_users("dataset/friends.csv")
    # for row in parse_files.load_statuses("dataset/original_statuses.csv"):
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
    
    # for row in parse_files.load_reactions("dataset/original_reactions.csv"):
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

    # graph = create_graph(users)

    name = input("Enter a user's name: ").title()
    while name not in users:
        print("User with that name doesnt exist.")
        name = input("Enter a user's name: ").title()

    recommended_statuses = sorted(reduce(lambda x, y: x + y, statuses.values()), key = lambda status: calculate_status_weight(status) if graph.get_edge_data(name, status.author) is None else calculate_status_weight(status) + 5*graph.get_edge_data(name, status.author)['weight'], reverse = True)
    
    for status in recommended_statuses[:10]:
        print(tabulate([[f"{status.message[:150]}...", status.author]], headers = ["Message", "Author"], tablefmt="fancy_grid"))

    # with open("user_graph.pickle", 'wb') as f:
    #     pickle.dump(graph, f)
    
    # dictionary = {"users": users, "statuses": statuses, "shares": shares, "reactions": reactions, "comments": comments}
    # with open("entities.pickle", "wb") as f:
    #     pickle.dump(dictionary, f)
