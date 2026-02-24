import json
from twisted.internet import reactor, protocol

class CallCenterManager:
    """
    Manages the call center logic
    """
    
    def __init__(self):
        self.operators = {
            "A": {"state": "available", "current_call": None},
            "B": {"state": "available", "current_call": None}
        }
        self.queue = []
        self.active_timeouts = {}
        self.active_proto = None 

    def process_command(self, command, identifier, proto):
        """
        Routes incoming commands to their respective functions
        """
        self.active_proto = proto
        if command == "call":
            return self.handle_call(identifier)
        elif command == "answer":
            return self.handle_answer(identifier)
        elif command == "reject":
            return self.handle_reject(identifier)
        elif command == "hangup":
            return self.handle_hangup(identifier)
        return "Invalid command."

    def handle_call(self, call_id, from_queue=False):
        """
        Processes a new call and assigns it to an available operator
        """
        received_msg = f"Call {call_id} received\n" if not from_queue else ""
        
        for op_id, info in self.operators.items():
            if info["state"] == "available":
                info["state"] = "ringing" 
                info["current_call"] = call_id
                
                if op_id in self.active_timeouts:
                    try: self.active_timeouts[op_id].cancel()
                    except: pass

                self.active_timeouts[op_id] = reactor.callLater(10, self.trigger_timeout, call_id, op_id)
                return f"{received_msg}Call {call_id} ringing for operator {op_id}".strip()
        
        # if theres no operator call goes to the queue (only if its a new call)
        if not from_queue:
            self.queue.append(call_id)
            return f"{received_msg}Call {call_id} waiting in queue".strip()
        
        return ""

    def trigger_timeout(self, call_id, op_id):
        """
        Handles the event where an operator fails to answer within the time limit
        """
        if self.operators[op_id]["state"] == "ringing":
            timeout_msg = f"Call {call_id} ignored by operator {op_id}"
            
            self.operators[op_id]["state"] = "available"
            self.operators[op_id]["current_call"] = None
            
            if op_id in self.active_timeouts:
                del self.active_timeouts[op_id]

            if self.active_proto:
                self.active_proto.transport.write(json.dumps({"response": timeout_msg}).encode('utf-8'))

    def handle_answer(self, op_id):
        """
        Change the operator state if he accepts the call 
        """
        if op_id in self.operators and self.operators[op_id]["state"] == "ringing":
            if op_id in self.active_timeouts:
                self.active_timeouts[op_id].cancel()
                del self.active_timeouts[op_id]
            
            self.operators[op_id]["state"] = "busy"
            call_id = self.operators[op_id]["current_call"]
            return f"Call {call_id} answered by operator {op_id}"
        
        return f"Operator {op_id} is not receiving a call."

    def handle_reject(self, op_id):
        """
        Handles manual call rejection by an operator, returning the call to the queue
        """
        if op_id in self.operators and self.operators[op_id]["state"] == "ringing":
            if op_id in self.active_timeouts:
                self.active_timeouts[op_id].cancel()
                del self.active_timeouts[op_id]
                
            call_id = self.operators[op_id]["current_call"]
            self.operators[op_id]["state"] = "available" 
            self.operators[op_id]["current_call"] = None
            
            reject_msg = f"Call {call_id} rejected by operator {op_id}"
            self.queue.insert(0, call_id) 
            next_step = self.get_next_queue_output()

            return f"{reject_msg}\n{next_step}" if next_step else reject_msg
        return f"Operator {op_id} is not receiving a call."

    def handle_hangup(self, call_id):
        """
        Terminates an active or ringing call and attempts to deliver the next queued call
        """
        for op_id, info in self.operators.items():
            if info["current_call"] == call_id:
                # If there was not an operator responsible for this call its missed
                if info["state"] == "ringing":
                    if op_id in self.active_timeouts:
                        self.active_timeouts[op_id].cancel()
                        del self.active_timeouts[op_id]
                    
                    info["state"] = "available" 
                    info["current_call"] = None
                    
                    msg = f"Call {call_id} missed"
                    next_call = self.get_next_queue_output() 
                    return f"{msg}\n{next_call}" if next_call else msg

                # If the call was in progress, it is finished
                elif info["state"] == "busy":
                    info["state"] = "available"
                    info["current_call"] = None
                    
                    msg = f"Call {call_id} finished and operator {op_id} available"
                    next_call = self.get_next_queue_output()
                    return f"{msg}\n{next_call}" if next_call else msg

        # If the call is still in the queue, its missed
        if call_id in self.queue:
            self.queue.remove(call_id)
            return f"Call {call_id} missed" 
        
        return f"Call {call_id} not found."

    def get_next_queue_output(self):
        """
        Retrieves and delivers the next call from the top of the queue
        """
        if self.queue:
            return self.handle_call(self.queue.pop(0), from_queue=True)
        return None
        
class CallCenterProtocol(protocol.Protocol):
    """
    Twisted Protocol implementation for call center communication
    """
    def dataReceived(self, data):
        # Decodes incoming JSON data and writes the manager's response back to the transport
        try:
            msg = json.loads(data.decode('utf-8'))
            response = self.factory.manager.process_command(msg['command'], msg['id'], self)
            self.transport.write(json.dumps({"response": response}).encode('utf-8'))
        except Exception:
            pass

class CallCenterFactory(protocol.Factory):
    """
    Factory class to instantiate the CallCenterProtocol and persistent manager
    """
    def __init__(self):
        self.manager = CallCenterManager()
    def buildProtocol(self, addr):
        proto = CallCenterProtocol()
        proto.factory = self
        return proto

if __name__ == "__main__":
    # Start the server on the designated TCP port
    print("Call Center Server active on port 5678...")
    reactor.listenTCP(5678, CallCenterFactory())
    reactor.run()
