import threading


def peerDebug(msg):
    """ Prints a messsage to the screen with the name of the current thread """
    print("[%s] %s" % (str(threading.currentThread().getName()), msg))
