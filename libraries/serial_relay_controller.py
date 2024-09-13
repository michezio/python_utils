import serial
import struct
import sys
import time
import os

class SerialController:
    """
    High-level simplified class to control a serial connection.
    Once initialized you cannot change the parameters of the serial
    connection but only use the provided limited set of high-level
    methods to control it.
    """

    def __init__(self, bytedelay:int=0, **kwargs):
        """
        Constructor
        
        Parameters
        ----------
        bytedelay : int
            delay between two consecutive packets to avoid packet collisions,
            expressed in multiples of the inverse of the baudrate.
            This delay is multiplied by the number of bytes of each packet
            so for example on a connection with a baudrate of 9600 using a
            bytedelay of 30 a message of 8 bytes will have a delay of
            8 * 30 / 9600 = 0.025 s (25 ms)
            
        """
        self._ser = serial.Serial(**kwargs)
        self._bytedelay = bytedelay
        self._packetdelay = bytedelay / self._ser.baudrate
    
    def __str__(self):
        return f"SerialController over {self._ser.port}"

    def __repr__(self):
        return f"SerialController with bytedelay={self._bytedelay} ({self._packetdelay*1000} ms) using {self._ser}"

    @staticmethod
    def _pack(bytes):
        return struct.pack('=' + 'c'*len(bytes), *map(lambda x: int.to_bytes(x, 1, sys.byteorder), bytes))
 
    def send_bytes_packet(self, *bytes):
        if not all(0 <= x <= 255 for x in bytes):
            raise ValueError("Bytes should be integers in range 0-255")
        self._ser.write(self._pack(bytes))
        if self._packetdelay > 0:
            time.sleep(self._packetdelay * len(bytes))

    def send_string_packet(self, string):
        self.send_bytes_packet(*map(lambda x: int(x, 16), string.split()))

    def read_bytes(self, num):
        return self._ser.read(num)

    def is_open(self):
        return self._ser.isOpen()

    def close(self):
        if self._ser.isOpen():
            self._ser.close()


class SerialRelayBoard:
    """
    Class to control a relay board with RS-232 interface
    that uses the chip SIPEX SP232EEN

    Attributes
    ----------
    CHECK, ACTIVATE, DEACTIVATE, TOGGLE, BANG, TOGGLE_NEXT
        aliases for the command bytes

    Methods
    -------
    close()
        used to close the connection to the serial port
    send_bytes_packet(*bytes...)
        generates and send a packet from the bytes passed as arguments.
        This method can work on any serial connected device
    send_string_packet(string)
        generates and send a packet from a string
        (eg. `"0x55 0x56 0x00 0x00 0x00 0x01 0x01 0xAD"`).
        This method can work on any serial connected device
    send_command(channel, command)
        send a packet specific for the SIPEX SP232EEN to execute
        `command` on the relay specified by `channel`.
        Command must be one of the aliases (argument of the class)

    Notes
    -----
    MESSAGING PROTOCOL

    8 Byte messages:
    HEAD_1 HEAD_2 0 0 0 CHANNEL COMMAND CHECKSUM

    COMMAND:        HEAD_1 HEAD_2 = 0x55 0x56
    RESPONSE:       HEAD_1 HEAD_2 = 0x33 0x3C

    Channel: CHANNEL from 1 to number of relays on board

    In command:
    ACTIVATE:       COMMAND = 0x01
    DEACTIVATE:     COMMAND = 0x02
    TOGGLE:         COMMAND = 0x03
    BANG (200 ms):  COMMAND = 0x04
    TOGGLE NEXT:    COMMAND = 0x05

    In response:
    STATUS ON:      COMMAND = 0x01
    STATUS OFF:     COMMAND = 0x02

    CHECKSUM:       Sum (modulo 256) of the first 7 bytes

    EXAMPLES:

    ACTIVATION:
    CH1: 0x55 0x56 0x00 0x00 0x00 0x01 0x01 0xAD
    CH2: 0x55 0x56 0x00 0x00 0x00 0x02 0x01 0xAE

    DEACTIVATION:
    CH1: 0x55 0x56 0x00 0x00 0x00 0x01 0x02 0xAE
    CH2: 0x55 0x56 0x00 0x00 0x00 0x02 0x02 0xAF

    TOGGLING:
    CH1: 0x55 0x56 0x00 0x00 0x00 0x01 0x03 0xAF
    CH2: 0x55 0x56 0x00 0x00 0x00 0x02 0x03 0xB0

    BANGING (200 ms):
    CH1: 0x55 0x56 0x00 0x00 0x00 0x01 0x04 0xB0
    CH2: 0x55 0x56 0x00 0x00 0x00 0x02 0x04 0xB1

    ASK STATUS (GET RESPONSE):
    CH1: 0x55 0x56 0x00 0x00 0x00 0x01 0x00 0xAC
    CH2: 0x55 0x56 0x00 0x00 0x00 0x02 0x00 0xAD

    RESPONSE STATUS ON:
    CH1: 0x33 0x3C 0x00 0x00 0x00 0x01 0x01 0x71
    CH2: 0x33 0x3C 0x00 0x00 0x00 0x02 0x01 0x72

    RESPONSE STATUS OFF:
    CH1: 0x33 0x3C 0x00 0x00 0x00 0x01 0x02 0x72
    CH2: 0x33 0x3C 0x00 0x00 0x00 0x02 0x02 0x73
    """
    
    CHECK = 0
    ACTIVATE = 1
    DEACTIVATE = 2
    TOGGLE = 3
    BANG = 4
    TOGGLE_NEXT = 5

    def __init__(self, port, relays=2):
        self._relays = relays
        self._serctrl = SerialController(
            port=port,
            baudrate=9600,
            bytedelay=30, # value found empirically to avoid packet collision 
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            timeout=1 # seconds
        )

    def __str__(self):
        return f"RS232 {self._relays}-relays board on {self._serctrl}"

    @staticmethod
    def _calculate_checksum(*bytes):
        return sum(bytes) % 256

    def send_command(self, channel, command):
        if not (0 <= channel <= 255):
            raise ValueError("Channel should be in range 0-255")
        if not (0 <= command <= 255):
            raise ValueError("Command should be in range 0-255")
        if channel > self._relays:
            raise ValueError(f"Channel {channel} not available on a {self._relays}-relays board")

        checksum = self._calculate_checksum(0x55, 0x56, channel, command)
        self._serctrl.send_bytes_packet(0x55, 0x56, 0x00, 0x00, 0x00, channel, command, checksum)
        
    def activate(self, relay):
        self.send_command(relay, self.ACTIVATE)

    def deactivate(self, relay):
        self.send_command(relay, self.DEACTIVATE)

    def toggle(self, relay):
        self.send_command(relay, self.TOGGLE)

    def bang(self, relay):
        self.send_command(relay, self.BANG)

    def toggle_next(self):
        self.send_command(0, self.TOGGLE_NEXT)
    
    def check(self, relay):
        self.send_command(relay, self.CHECK)
        value = self._serctrl.read_bytes(8)
        if len(value) == 8 and value[0] == 0x33 and value[1] == 0x3C and value[5] == relay:
            if value[6] in [1, 2] and value[7] == self.__checksum(0x33, 0x3C, relay, value[6]):
                if value[6] == 1:
                    return True
                elif value[6] == 2:
                    return False
    
        raise BufferError(f"Unexpected response from {self} after check request on relay {relay}")

    def is_open(self):
        return self._serctrl.is_open()

    def close(self):
        self._serctrl.close()
