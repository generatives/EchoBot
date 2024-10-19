class Peer:
    def __init__(self, pyreNode, uuid, name, headers):
        self.pyreNode = pyreNode
        self.uuid = uuid
        self.name = name
        self.headers = headers
        self.groups = []

    def whisper(self, msg):
        self.pyreNode.whisper(self.uuid, msg)