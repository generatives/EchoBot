
from pyre import Pyre 
import zmq 
import uuid
import json

from utils.EventHandler import EventHandler
from distributed.Peer import Peer

class Node():

    def __init__(self, ctx, headers = {}, groups = []):
        self.ctx = ctx
        self.__headers = headers
        self.__groups_to_join = groups
        self.peers = {}
        self.groups = []
        
        self.peer_entered = EventHandler()
        self.peer_exited = EventHandler()
        self.peer_joined = EventHandler()
        self.peer_left = EventHandler()
        self.whisper_recieved = EventHandler()
        self.shout_recieved = EventHandler()

    def start(self):
        self.node = Pyre()

        for key, value in self.__headers.items():
            self.node.set_header(key, value)

        for group_name in self.__groups_to_join:
            self.join_group(group_name)
            
        self.node.start()

        self.poller = zmq.Poller()
        self.poller.register(self.node.socket(), zmq.POLLIN)

    def join_group(self, group_name):
        self.node.join(group_name)
        self.groups.append(group_name)

    def leave_group(self, group_name):
        self.node.leave(group_name)
        self.groups.remove(group_name)

    def poll(self):
        items = dict(self.poller.poll(0))
        if self.node.socket() in items and items[self.node.socket()] == zmq.POLLIN:
            cmds = self.node.recv()
            msg_type = cmds.pop(0).decode('UTF-8')
            peer_uuid = uuid.UUID(bytes=cmds.pop(0))
            peer_name = cmds.pop(0)

            print(f"{msg_type} from peer {peer_uuid} {peer_name}: {cmds}")
            
            if msg_type == "ENTER":
                headers = json.loads(cmds.pop(0).decode('UTF-8'))
                peer = Peer(self.node, peer_uuid, peer_name, headers)
                self.peers[peer_uuid] = peer
                self.peer_entered(peer)
            else:
                peer = self.peers[peer_uuid]
                if msg_type == "EXIT":
                    self.peers.pop(peer_uuid)
                    self.peer_exited(peer)
                elif msg_type == "JOIN":
                    group_name = cmds.pop(0).decode('UTF-8')
                    peer.groups.append(group_name)
                    self.peer_joined(peer, group_name)
                elif msg_type == "LEAVE":
                    group_name = cmds.pop(0).decode('UTF-8')
                    peer.groups.remove(group_name)
                    self.peer_left(peer, group_name)
                elif msg_type == "WHISPER":
                    self.whisper_recieved(peer, cmds)
                elif msg_type == "SHOUT":
                    group_name = cmds.pop(0).decode('UTF-8')
                    self.shout_recieved(peer, group_name, cmds)

    def shout(self, group_name, msg):
        self.node.shout(group_name, msg)

    def stop(self):
        self.node.stop()
