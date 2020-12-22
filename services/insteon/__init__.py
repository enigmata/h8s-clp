import codecs
import glob
import json
import os
import re
import serial
import sys

from pathlib import Path
from ruamel.yaml import YAML
from service import Service

# Terminology:
#   IM = Insteon PLM

# Insteon service exceptions
class InsteonException(Exception):
    def __init__(self, msg):
        self.data = msg
class InsteonPLMConfigError(InsteonException): pass
class InsteonPLMConfigInfo(InsteonException):  pass

if os.name == 'posix':
    from serial.tools.list_ports_posix import comports
else:
    raise InsteonPLMConfigError(f'Platform ("{os.name}") is not supported')


def read_line(filename):
    """help function to read a single line from a file; otherwise returns none"""
    try:
        f = open(filename)
        line = f.readline().strip()
        f.close()
        return line
    except IOError:
        return None


class InsteonPLM:
    """ 
    An InsteonPLM class represents an physical Insteon Power Line
    modem (PLM), and faciliates communications between the Insteon
    service and the PLM by talking the serial protocol, as strings
    of hex bytes according to a finite state machine                
    """

    def __init__(self):

        self.plm = None  # represents serial port to which plm is attached

        try:
            cfg_file= Path(os.path.join(os.path.dirname(sys.modules['services.insteon'].__file__), 'insteon.yaml'))
        except IOError:
            cfg_file = None  # ensure to raise native exception

        if not cfg_file:
            raise InsteonPLMConfigError('Cannot open or read insteon json config files')

        yaml = YAML(typ='safe')
        self.IMSendCmds, self.IMReceiveCmds, self.IMParms = yaml.load_all(cfg_file)
        if not self.IMSendCmds or not self.IMReceiveCmds or not self.IMParms:
            raise InsteonPLMConfigError('Cannot read insteon.yaml config file')

        try:
            f = open(os.path.join(os.path.dirname(sys.modules['services.insteon'].__file__), 'devices.json'))
            self.devices = json.load(f)
            f.close()
        except IOError:
            raise InsteonPLMConfigError('Cannot read devices.json file')

    def get_send_cmds(self):

        return self.IMSendCmds

    def get_receive_cmds(self):

        return self.IMReceiveCmds

    def get_devices(self):

        return self.devices

    def send_command(self, cmd, args=''):
        """
        Send a command to the PLM without governance by the protocol.
        That is, allow any valid command to be sent to the PLM without
        checking if it is a valid successor to the previous command.
        This will work in all cases because Insteon commands are idempotent.
        """

        resp_groups = {}
        cmd = cmd.upper()

        if cmd in self.IMSendCmds:
            cmd_str, _, cmd_help = self.IMSendCmds[cmd]
            cmd_str = ''.join([cmd_str,args])
            cmd_bytes = bytearray.fromhex(cmd_str)
            write_len = len(cmd_bytes)
            num_written = self.plm.write(cmd_bytes)

            if num_written == write_len:
                while True:
                    # need to clear out any leading nulls or garbage, until
                    # we see the STX (Start TeXt) byte signaling the beginning
                    # of the reply string or other monitor messages we need
                    # to consume until we get the reply message for the command
                    # we sent
                    byte_read = self.plm.read(1)
                    while (byte_read != bytearray.fromhex(self.IMParms['IM_COMM_STX'])):
                        byte_read = self.plm.read(1)

                    cmd_num_bytes = self.plm.read(1)
                    cmd_num = cmd_num_bytes.hex()

                    if cmd_num in self.IMReceiveCmds:
                        resp_len, resp_regex, resp_description = self.IMReceiveCmds[cmd_num]
                        resp_bytes = self.plm.read(resp_len)
                        resp = resp_bytes.hex()
    
                        if cmd_num == cmd_str[2:4]:
                            m = re.match(resp_regex, resp)
                            if m: 
                                resp_groups = m.groupdict()
                                if resp_groups['ack'] != self.IMParms['IM_CMD_SUCCESS']:
                                    resp_groups = {}
                            break
                    else:
                        break
        else:
            print(f'ERROR: Command not recognized: "{cmd}"')

        return resp_groups


    def monitor(self):
        """
        Query the PLM for messages, of which there are two types
        that are send from the PLM to the host (this code):
        1) Responses to 0x60 series commands
        2) All 0x50 series commands received by the PLM sent
           by other devices, hosts
        """

        while True:
            # need to clear out any leading nulls or garbage, until
            # we see the STX (Start TeXt) byte signaling the beginning
            # of the reply string or other monitor messages we need
            # to consume until we get the reply message for the command
            # we sent

            byte_read = self.plm.read(1)
            while (byte_read != bytearray.fromhex(self.IMParms['IM_COMM_STX'])):
                byte_read = self.plm.read(1)

            cmd_num_bytes = self.plm.read(1)
            cmd_num = cmd_num_bytes.hex()

            if cmd_num in self.IMReceiveCmds:
                resp_len, resp_regex, resp_description = self.IMReceiveCmds[cmd_num]
                print(f'{resp_description}:')

                resp_bytes = self.plm.read(resp_len)
                resp = resp_bytes.hex()
    
                m = re.match(resp_regex, resp)
                if m: 
                    resp_groups = m.groupdict()
                    print(f"  from: {resp_groups['from_id1']}.{resp_groups['from_id2']}.{resp_groups['from_id3']}")
                    print(f"  to:   {resp_groups['to_id1']}.{resp_groups['to_id2']}.{resp_groups['to_id3']}")
                    print(f"    => message flags: '{resp_groups['msg_flags']}' cmds: '{resp_groups['cmd1']}', '{resp_groups['cmd2']}'")
            else:
                print('  --> ERROR: Did not recognize the command received. Aborting so that you can fix my metadata.')
                break


    def disconnect(self):

        if self.plm:
            self.plm.close()
            self.plm = None

    def connect(self):
    
        self.disconnect()

        device = None
        for port, _, hwid in comports():
            if re.search(r"0403:6001", hwid):
                device = port
                break

        if device:
            try:
                self.plm = serial.Serial(port=device, baudrate=self.IMParms['IM_BAUDRATE'], timeout=5)
            except serial.SerialException:  # TODO: convert each exception to a log write
                print('  --> Failed to open serial port')
                self.plm = None
            except OSError:
                print('  --> Unable to access serial port')
                self.plm = None
    
            response = self.send_command('GET_VERSION')
            if response:
                print(f"Insteon PLM ID= {response['id1']}.{response['id2']}.{response['id3']}: ", end='')
                print(f"device category={response['dev_cat']}, subcategory={response['dev_subcat']}, firmware version={response['firm_ver']}")
            else:
                print('  --> failed to send IM command to serial port')
                self.plm.close()
                self.plm = None # assume not a PLM on this port

        if not self.plm:
            raise InsteonPLMConfigError('Could not find a PLM attached to a USB port')


class Insteon(Service):
    """
    An Insteon is a service that manages an Insteon network of devices.
    """

    def __init__(self, path): 
    
        Service.__init__(self,
                         path,
                         name='insteon', 
                         description = 'Manages the devices, scenes, and schedules of a network of Insteon devices', 
                         version=1)

        try:
            self.plm = InsteonPLM()
            self.plm.connect()
        except InsteonPLMConfigError as PLMerr:
            print(f'Insteon PLM config error: {PLMerr.data}')
            self.state = 'uninitialized'
        else:
            print('Insteon PLM found and configured successfully')
            self.state = 'initialized'

        self.load_commands()


    def get_plm(self):

        return self.plm

    def is_initialized(self):

        return self.state == 'initialized'

