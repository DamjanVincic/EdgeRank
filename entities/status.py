class Status(object):
    def __init__(self, id, message, status_type, link, publish_time, author, reaction_count, comment_count, share_count, like_count, num_loves, num_wows, num_hahas, num_sads, num_angrys):
        self.id = id
        self.message = message
        # self.link_name = link_name
        self.type = status_type
        self.link = link
        self.publish_time = publish_time
        self.author = author
        self.reaction_count = reaction_count
        self.comment_count = comment_count
        self.share_count = share_count
        self.like_count = like_count
        self.num_loves = num_loves
        self.num_wows = num_wows
        self.num_hahas = num_hahas
        self.num_sads = num_sads
        self.num_angrys = num_angrys
