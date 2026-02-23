import json
import sys
from twisted.internet import reactor, protocol, stdio
from twisted.protocols import basic

class CallCenterClient(protocol.Protocol):
    """
    Handles the TCP network connection and incoming data from the server
    """

    def connectionMade(self):
        # Attach the keyboard reader to Twisted's event loop 
        stdio.StandardIO(KeyboardReader(self))
        sys.stdout.write("> ")
        sys.stdout.flush()

    def dataReceived(self, data):
        """
        Processes and displays JSON responses received from the server
        """
        try:
            resp = json.loads(data.decode('utf-8'))
            sys.stdout.write(f"\r{resp['response']}\n> ")
            sys.stdout.flush()
        except Exception:
            pass

class KeyboardReader(basic.LineReceiver):
    """
    Reads and parses user input from the terminal
    """
    from os import linesep
    delimiter = linesep.encode('utf-8')

    def __init__(self, protocol_instance):
        self.proto = protocol_instance

    def lineReceived(self, line):
        # Converts terminal input into the required JSON format and sends it
        text = line.decode('utf-8').strip()
        if not text:
            sys.stdout.write("> ")
            sys.stdout.flush()
            return
        
        parts = text.split()
        if len(parts) >= 2:
            # Send to server
            sending = json.dumps({"command": parts[0], "id": parts[1]})
            self.proto.transport.write(sending.encode('utf-8'))
        else:
            sys.stdout.write("Usage: <command> <id>\n> ")
            sys.stdout.flush()

class CallCenterClientFactory(protocol.ClientFactory):
    """
    Factory to create and manage instances of the CallCenterClient protocol
    """
    def buildProtocol(self, addr):
        return CallCenterClient()

if __name__ == "__main__":
    # Connect to the server container on the specified port
    reactor.connectTCP("server", 5678, CallCenterClientFactory())
    reactor.run()