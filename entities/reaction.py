class Reaction(object):
    def __init__(self, status_id, reaction_type, reactor, reaction_time):
        self.status_id = status_id
        self.type = reaction_type
        self.reactor = reactor
        self.reaction_time = reaction_time