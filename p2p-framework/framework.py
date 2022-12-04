import socket
import struct
import threading
import time
import traceback
import PeerConnection
import debug


class Peer:
    """A peer in the network"""

    def __init__(self, maxPeers, serverPort, myid=None, serverHost=None):
        self.debug = 0

        self.maxPeers = int(maxPeers)
        self.serverPort = int(serverPort)

        # if passed used else determines the ip automatically.
        if serverHost:
            self.serverHost = serverHost
        else:
            self.__initserverHost()

        # my id if passed else host:port is id
        if myid:
            self.myid = myid
        else:
            self.myid = f'{serverHost}:{serverPort}'

        self.peerlock = threading.Lock()

        # for known peers
        # host=> port
        self.peers = {}

        # to stop main loop
        self.shutdown = False

        self.handlers = {}

        self.router = None

    def __initserverHost(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("www.google.com", 80))
        self.serverHost = s.getsockname()[0]
        s.close()

    def __debug(self, msg):
        if self.debug:
            debug.peerDebug(msg)

    def makeServerSocket(self, port, backlog=5):

        # create socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # set some options like reusing the addr.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind
        s.bind(('', port))
        # listen
        s.listen(backlog)
        return s

    def __handlePeer(self, clientSock):
        self.__debug('New child ' + str(threading.currentThread().getName()))
        host, port = clientSock.getpeername()
        self.__debug('Connected' + str(host) + str(port))

        peerConn = PeerConnection.PeerConnection(
            None, host, port, clientSock, debug=False)

        try:
            msgType, msgData = peerConn.recvData()

            if msgType:
                msgType = msgType.upper()

            if msgType not in self.handlers:
                self.__debug(f'Not handled: {msgType}: {msgData}')
            else:
                self.__debug(f'Handling peer msg: {msgType}: {msgData}')
                self.handlers[msgType](peerConn, msgData)
        except KeyboardInterrupt:
            raise
        except:
            if self.debug:
                traceback.print_exc()

        self.__debug('Disconnecting ' + str(host) + str(port))
        peerConn.close()

    def mainServerLoop(self):
        s = self.makeServerSocket(self.serverPort)
        s.settimeout(2)
        self.__debug('Server started: %s (%s:%d)'
                     % (self.myid, self.serverHost, self.serverPort))

        # start while loop
        while not self.shutdown:
            try:
                self.__debug("Listening for connections")
                clientSock, clientAddr = s.accept()
                # None, puts in blocking mode
                clientSock.settimeout(None)

                trd = threading.Thread(
                    target=self.__handlePeer, args=[clientSock])
                trd.start()
            except KeyboardInterrupt:
                # this allows ctrl+C to stop the program
                print('shutting main loop ctrl+C')
                self.shutdown = True
                continue
            except:
                if self.debug:
                    traceback.print_exc()
                    continue
        # end while loop

        self.__debug('Main loop exiting')

        s.close()

    def __runStabilizer(self, stabilizer, delay):
        # calls stabilizer for every delay second for this peer.
        while not self.shutdown:
            stabilizer()
            time.sleep(delay)

    def setMyId(self, myid):
        self.myid = myid

    def startStabilizer(self, stabilizer, delay):
        # creates a new thread for the stabilizer to run

        newThread = threading.Thread(
            target=self.__runStabilizer, args=[stabilizer, delay])
        newThread.start()

    def addHandler(self, msgType, handler):
        # Adds the handler for the given msgType with this peer
        assert len(msgType) == 4
        self.handlers[msgType] = handler

    def addRouter(self, router):
        # adds a routing func with this peer

        self.router = router

    def addPeer(self, peerID, host, port):
        maxPeers = self.maxPeers
        if peerID not in self.peers and (maxPeers == 0 or len(self.peers) < maxPeers):
            self.peers[peerID] = (host, int(port))
            return True
        else:
            return False

    def getPeer(self, peerID):
        assert peerID in self.peers
        return self.peers[peerID]

    def removePeer(self, peerID):
        if peerID in self.peers:
            del self.peers[peerID]

    def addPeerAt(self, loc, peerID, host, port):
        self.peers[loc] = (peerID, host, int(port))

    def getPeerAt(self, loc):
        if loc not in self.peers:
            return None
        return self.peers[loc]

    def removePeerAt(self, loc):
        self.removePeer(loc)

    def getPeerIds(self):
        # gives a list of all known peer id's
        return self.peers.keys()

    def numberOfPeers(self):
        # gives the number of known peers
        return len(self.peers)

    def maxPeersReached(self):
        assert self.maxPeers == 0 or len(self.peers) <= self.maxPeers
        return self.maxPeers > 0 and len(self.peers) == self.maxPeers

    def sentToPeer(self, peerID, msgType, msgData, waitForReply=True):
        # sends message to the peer. Route will be deicded by router func.

        nextPID = None
        host = None
        port = None
        if self.router:
            nextPID, host, port = self.router(peerID)

        if not self.router or not nextPID:
            self.__debug('Unable to route %s to %s' % (msgType, peerID))
            return None

        return self.connectAndSend(host, port, msgType, msgData, pid=nextPID, waitForReply=waitForReply)

    def connectAndSend(self, host, port, msgType, msgData, pid=None, waitForReply=True):
        # uses peerConn to send msg and wait(if true) for a reply

        msgResponse = []

        try:
            peerConn = PeerConnection.PeerConnection(
                pid, host, port, debug=self.debug)
            peerConn.sendData(msgType, msgData)
            self.__debug(f'Sent {pid}: {msgType}')

            if waitForReply:
                onReply = peerConn.recvData()
                while (onReply != (None, None)):
                    msgResponse.append(onReply)
                    self.__debug(f'got reply {pid}:{msgResponse}')
                    onReply = peerConn.recvData()
            peerConn.close()
        except KeyboardInterrupt:
            raise
        except:
            if self.debug:
                traceback.print_exc()

        return msgResponse

    def pingLivePeers(self):
        # pings all peers, Removes inactive peers, can be used as a stabilizer

        peerToDel = []

        for pid in self.peers:
            isConnected = False

            try:
                self.__debug(f'Checking peer: {pid}')
                host, port = self.peers[pid]
                peerConn = PeerConnection.PeerConnection(
                    pid, host, port, debug=self.debug)
                peerConn.sendData('PING', '')
                isConnected = True
            except:
                peerToDel.append(pid)
            if isConnected:
                peerConn.close()

        self.peerlock.acquire()
        try:
            for pid in peerToDel:
                if pid in self.peers:
                    del self.peers[pid]
        finally:
            self.peerlock.release()
