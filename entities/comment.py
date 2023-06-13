class Comment(object):
    def __init__(self, id, status_id, parent_id, message, author, publish_time, reaction_count, like_count):
        self.id = id
        self.status_id = status_id
        self.parent_id = parent_id
        self.message = message
        self.author = author
        self.publish_time = publish_time
        self.reaction_count = reaction_count
        self.like_count = like_count