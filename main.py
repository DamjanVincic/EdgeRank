import csv
import networkx as nx
import parse_files
from entities.status import Status
from entities.comment import Comment
from entities.share import Share
from entities.reaction import Reaction


statuses = {}
shares = {}
reactions = {}
comments = {}

def load_users(path):
    with open(path, encoding = 'utf-8') as f:
        reader = csv.reader(f)
        data = list(reader)
    return data[1:]

if __name__ == "__main__":
    users = load_users("dataset/friends.csv")
    for row in parse_files.load_statuses("dataset/original_statuses.csv"):
        status = Status(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14])
        if status.author not in statuses:
            statuses[status.author] = [status]
        else:
            statuses[status.author].append(status)

    for row in parse_files.load_shares("dataset/original_shares.csv"):
        share = Share(row[0], row[1], row[2])
        if share.status_id not in shares:
            shares[share.status_id] = [share]
        else:
            shares[share.status_id].append(share)
    
    for row in parse_files.load_reactions("dataset/original_reactions.csv"):
        reaction = Reaction(row[0], row[1], row[2], row[3])
        if reaction.status_id not in reactions:
            reactions[reaction.status_id] = [reaction]
        else:
            reactions[reaction.status_id].append(reaction)
    
    for row in parse_files.load_comments("dataset/original_comments.csv"):
        comment = Comment(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
        if comment.status_id not in comments:
            comments[comment.status_id] = [comment]
        else:
            comments[comment.status_id].append(comment)
