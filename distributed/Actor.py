import threading
from distributed.Node import Node

class Actor:
    def __init__(self, ctx, headers = {}, groups = []):
        self.should_run = True
        self.node = Node(ctx, headers, groups)
        self.node.peer_entered += self.peer_entered
        self.node.peer_exited += self.peer_exited
        self.node.peer_joined += self.peer_joined
        self.node.peer_left += self.peer_left
        self.node.whisper_recieved += self.whisper_recieved
        self.node.shout_recieved += self.shout_recieved

    def __run(self):
        self.node.start()
        self.starting()

        while(self.should_run):
            self.node.poll()
            self.poll()

        self.stopping()
        self.node.stop()

    def starting(self):
        pass

    def peer_entered(self, peer):
        pass

    def peer_exited(self, peer):
        pass

    def peer_joined(self, peer, group_name):
        pass

    def peer_left(self, peer, group_name):
        pass

    def whisper_recieved(self, peer, cmds):
        pass

    def shout_recieved(self, peer, group_name, cmds):
        pass

    def poll(self):
        pass

    def stopping(self):
        pass

    def shout(self, group_name, msg):
        self.node.shout(group_name, msg)

    def start(self):
        self.thread = threading.Thread(target=self.__run)
        self.thread.start()

    def stop(self):
        self.should_run = False
        self.thread.join()
