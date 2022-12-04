import socket
import struct
import traceback
import debug


class PeerConnection:
    def __init__(self, peerID, host, port, sock=None, debug=False):

        self.id = peerID
        self.debug = debug

        if not sock:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((host, int(port)))
        else:
            self.s = sock

        self.sd = self.s.makefile('rw', 0)

    def __debug(self, msg):

        if self.debug:
            debug.peerDebug(msg)

    def recvData(self):
        # recieve a msg from a peerConn.

        try:
            # parse the incoming msg
            msgType = self.sd.read(4)
            if not msgType:
                return (None, None)

            strlen = self.sd.read(4)

            msgLen = int(struct.unpack("!L", strlen)[0])

            msg = ""

            while len(msg) != msgLen:
                data = self.sd.read(min(2048, msgLen - len(msg)))

                if not len(data):
                    break
                msg += data

            if len(msg) != msgLen:
                return (None, None)

        except KeyboardInterrupt:
            raise
        except:
            if self.debug:
                traceback.print_exc()
            return (None, None)

        return (msgType, msg)

    def sendData(self, msgType, msgData):
        # send msg using peerConn.

        try:
            msg = self.__packMsg(msgType, msgData)
            self.sd.write(msg)
            self.sd.flush()
        except KeyboardInterrupt:
            raise
        except:
            if self.debug:
                traceback.print_exc()
            return False
        return True

    def __packMsg(self, msgType, msgData):
        msgLen = len(msgData)
        msg = struct.pack("!4sL%ds" % msgLen, msgType, msgLen, msgData)
        return msg

    def close(self):
        # closes the socket

        self.s.close()
        self.s = None
        self.sd = None

    def __str__(self):

        return f'|{self.id}|'
