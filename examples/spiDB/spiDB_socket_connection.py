from spinnman.connections.udp_packet_connections.udp_connection \
    import UDPConnection

from threading import Thread
import traceback
import logging

import time
import struct

import sys

from enum import Enum

logger = logging.getLogger(__name__)

class dbCommands(Enum):
    PUT  = 0
    PULL = 1

def var_type(a):
    if type(a) is int:
        return 0
    if type(a) is str:
        return 1

    return 0

def bytearray(a):
    if type(a) is str:
        return a
    elif type(a) is int:
        return struct.pack('I', a)[0]

class sdp_packet():
    def __init__(self, bytestring):
        header = struct.unpack_from("HHIII", bytestring)

        (self.cmd_rc, self.seq, self.arg1, self.arg2, self.arg3) = header

        #arg2 represents info. first 12 bits are the size
        self.data = struct.unpack_from("{}s".format(self.arg2 & 0xFFF), bytestring, struct.calcsize("HHIII"))[0]

    def __str__(self):
        return "cmd_rc: {}, seq: {}, arg1: {}, arg2: {}, arg3: {}, data: {}"\
                .format(self.cmd_rc, self.seq, self.arg1, self.arg2, self.arg3, self.data)

    def reply_data(self):
        self.chip_x = (self.arg1 & 0x00FF0000) >> 16
        self.chip_y = (self.arg1 & 0x0000FF00) >> 8
        self.core   = (self.arg1 & 0x000000FF)

        if self.core is 255:
            return "FAIL - (id: {}, rtt: {})"\
                .format(self.seq, self.arg3)

        if self.cmd_rc is dbCommands.PUT.value:
            return "OK - (id: {}, rtt: {}ms, chip: {}-{}, core: {})"\
                .format(self.seq, self.arg3/1000000.0, self.chip_x, self.chip_y, self.core)
        else:
            return "OK - (id: {}, rtt: {}ms, chip: {}-{}, core: {}, data: {})"\
                .format(self.seq, self.arg3/1000000.0, self.chip_x, self.chip_y, self.core, self.data)

class SpiDBSocketConnection(Thread):
    """ A connection from the toolchain which will be notified\
        when the database has been written, and can then respond when the\
        database has been read, and further wait for notification that the\
        simulation has started.
    """

    def __init__(self, local_port=19999):
        """

        :param start_callback_function: A function to be called when the start\
                    message has been received.  This function should not take\
                    any parameters or return anything.
        :type start_callback_function: function() -> None
        :param local_host: Optional specification of the local hostname or\
                    ip address of the interface to listen on
        :type local_host: str
        :param local_port: Optional specification of the local port to listen\
                    on.  Must match the port that the toolchain will send the\
                    notification on (19999 by default)
        :type local_port: int
        """

        self.conn = UDPConnection()

        Thread.__init__(self,
                        name="spynnaker database connection for {}"
                        .format(local_port))

        self.ip_address = "192.168.240.253" #todo should not be hardcoded
        self.port = 11111
        self.start()

        self.current_message_id = -1
        self.command_buffer = []

    def put(self, k, v):
        k_str = bytearray(k)
        v_str = bytearray(v)
        self.current_message_id += 1

        k_size   = len(k_str)
        v_size   = len(v_str)
        k_v_size = k_size+v_size

        s = struct.pack("IBBIBI{}s".format(k_v_size),
                        self.current_message_id, dbCommands.PUT.value,
                        var_type(k), len(k_str),
                        var_type(v), len(v_str), "{}{}".format(k_str, v_str))

        #print ":".join("{:02x}".format(ord(c)) for c in s)

        return (self.current_message_id, s)

    def pull(self, k):
        k_str = bytearray(k)
        self.current_message_id += 1

        k_size   = len(k_str)

        s = struct.pack("IBBIBI{}s".format(k_size),
                        self.current_message_id, dbCommands.PULL.value,
                        var_type(k), k_size,
                        0, 0,
                        k_str)

        return (self.current_message_id, s)

    def flush(self, id_bytestrings):

        id_to_index = {}

        ret = [None] * len(id_bytestrings)

        for i, id_bytestring in enumerate(id_bytestrings):
            id_to_index[id_bytestring[0]] = i
            time.sleep(0.001)
            self.conn.send_to(id_bytestring[1], (self.ip_address, self.port))

        for i, id_bytestring in enumerate(id_bytestrings):
            try:
                bytestring = self.conn.receive(1)
                sdp_h = sdp_packet(bytestring)
                ret[id_to_index[sdp_h.seq]] = sdp_h.reply_data()
            except:
                pass

        return ret

    def run(self):
        time.sleep(9) #todo hmmmmmmmmmm

        self.command_buffer = [self.put("A","A"),
                               self.put("B","B"),
                               self.put("C","C"),
                               self.put("D","D"),
                               self.put("E","E"),
                               self.put("F","F"),
                               self.put("G","G")
                               ]
        print self.flush(self.command_buffer)
        self.command_buffer = []

        while True:
            try:
                #do the loop through TODO
                cmd = raw_input("> ")

                if(cmd == "flush"):
                    print self.flush(self.command_buffer)
                    self.command_buffer = []
                elif(cmd == "exit"):
                    sys.exit(0)
                else:
                    self.command_buffer.append(eval(cmd))

            except Exception:
                traceback.print_exc()
                time.sleep(1)