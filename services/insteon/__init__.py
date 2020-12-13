import serial
import glob
import re
from ruamel.yaml import YAML
import os
import sys
import json
from service import Service

# Terminology:
#   IM = Insteon PLM

# Insteon service exceptions
class InsteonException(Exception):
    def __init__(self, msg):
        self.data = msg
class InsteonPLMConfigError(InsteonException): pass
class InsteonPLMConfigInfo(InsteonException):  pass

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
            stream = file(os.path.join(os.path.dirname(sys.modules['services.insteon'].__file__), 'insteon.yaml'), 'r')
        except IOError:
            stream = None  # ensure to raise native exception

        if not stream:
            raise InsteonPLMConfigError('Cannot open or read insteon json config files')

        # self.IMSendCmds, self.IMReceiveCmds, self.IMParms = yaml.load_all(stream)
        yaml = YAML(typ='safe')
        self.IMSendCmds, self.IMReceiveCmds, self.IMParms = yaml.load_all(stream)
        if not self.IMSendCmds or not self.IMReceiveCmds or not self.IMParms:
            stream.close()
            raise InsteonPLMConfigError('Cannot read insteon.yaml config file')

        try:
            f = open(os.path.join(os.path.dirname(sys.modules['services.insteon'].__file__), 'devices.json'))
            self.devices = json.load(f)
            f.close()
        except IOError:
            raise InsteonPLMConfigError('Cannot read devices.json file')

        stream.close()

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

        responseGroups = {}
        commandSuccessful = False
        cmd = cmd.upper()

        if cmd in self.IMSendCmds:
            cmdstr, syntax, cmdhelp = self.IMSendCmds[cmd]
            cmdstr = ''.join([cmdstr,args])
            print('  --> cmdstr=%s, len=%d' % (''.join('\\x'+c.encode('hex') for c in cmdstr),len(cmdstr)))
            writelen = len(cmdstr)
            numwritten = self.plm.write( cmdstr )
            if numwritten == writelen:

                while True:
                    # need to clear out any leading nulls or garbage, until
                    # we see the STX (Start TeXt) byte signaling the beginning
                    # of the reply string or other monitor messages we need
                    # to consume until we get the reply message for the command
                    # we sent

                    byteread = self.plm.read(1)
                    sys.stdout.write('  --> bytes read=%s' % '\\x'+byteread.encode('hex'))
                    while (byteread != self.IMParms['IM_COMM_STX']):
                        sys.stdout.write(' ' + '\\x'+byteread.encode('hex'))
                        byteread = self.plm.read(1)

                    cmdnum = self.plm.read(1)
                    print('\n  --> cmd # = %s' % '\\x'+cmdnum.encode('hex'))

                    if cmdnum in self.IMReceiveCmds:

                        respLen, respRegex, respDescription = self.IMReceiveCmds[cmdnum]

                        # now we can get the proper IM response string
                        response = self.plm.read(respLen) 
                        print('  --> response=%s, actual len=%d, expected len=%d' % (''.join('\\x'+c.encode('hex') for c in response), len(response), respLen))
    
                        if cmdnum == cmdstr[1]:
                            # validate the response to the command we sent
                            m = re.match(respRegex, response)
                            if m: 
                                responseGroups = m.groupdict()
                                if responseGroups['ack'] == self.IMParms['IM_CMD_SUCCESS']:
                                    commandSuccessful = True
                                else:
                                    responseGroups = {}
                            break
                    else:
                        break
        else:
            print(f'ERROR: Command not recognized: "{cmd}"')

        return commandSuccessful, responseGroups 


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

            byteread = self.plm.read(1)
            sys.stdout.write('  --> bytes read=%s' % '\\x'+byteread.encode('hex'))
            while (byteread != self.IMParms['IM_COMM_STX']):
                sys.stdout.write(' ' + '\\x'+byteread.encode('hex'))
                byteread = self.plm.read(1)

            cmdnum = self.plm.read(1)
            print('\n  --> cmd # = %s' % '\\x'+cmdnum.encode('hex'))

            if cmdnum in self.IMReceiveCmds:

                respLen, respRegex, respDescription = self.IMReceiveCmds[cmdnum]

                # now we can get the proper IM response string
                response = self.plm.read(respLen) 
                print('  --> response=%s, actual len=%d, expected len=%d' % (''.join('\\x'+c.encode('hex') for c in response), len(response), respLen))
    
                #m = re.match(respRegex, response)
                #if m: 
                #    responseGroups = m.groupdict()
                #    if responseGroups['ack'] == self.IMParms['IM_CMD_SUCCESS']:
                #        commandSuccessful = True
                #    else:
                #        responseGroups = {}

                #break

            else:
                print('  --> ERROR: Did not recognize the command received. Aborting so that you can fix my metadata.')
                break


    def disconnect(self):

        if self.plm:
            self.plm.close()
            self.plm = None

    def connect(self):
    
        # if there's already an open serial port with PLM attached,
        # then we need to first close it so we can try a fresh connect
        self.disconnect()

        # grab all serial devices as potentially having an Insteon PLM attached
        # NOTE: this is known to work on Linux; not sure about OS X
        USBDevices = glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    
        # test each serial device to see if an Insteon PLM is attached
        for device in USBDevices:

            print(f'testing serial port: {device}')

            # check to see if something is connected to the port
            base = os.path.basename(device)
            if os.path.exists('/sys/class/tty/%s/device' % (base,)):
                # the insteon PLM is a USB-Serial device, so chk if that is what we have
                sys_dev_path = '/sys/class/tty/%s/device/driver/%s' % (base, base)
                if os.path.exists(sys_dev_path):
                    sys_usb = os.path.dirname(os.path.dirname(os.path.realpath(sys_dev_path)))

                    vendor = read_line(sys_usb+'/idVendor')
                    product = read_line(sys_usb+'/idProduct')
                    print(f'  --> USB device vendor_id:product_id={vendor}:{product}')

                    # insteon PLM is an FTDI (vendor=0403) USB USART (product=6001)
                    if (vendor == '0403' and product == '6001'):

                        # chk if this FTDI USB UART is an insteon PLM
                        try:
                            self.plm = serial.Serial(port=device, baudrate=self.IMParms['IM_BAUDRATE'], timeout=5)
                        except serial.SerialException:  # TODO: convert each exception to a log write
                            print('  --> Failed to open serial port')
                            self.plm = None # assume not a PLM on this port
                            continue
                        except OSError:
                            print('  --> Unable to access serial port')
                            self.plm = None # assume not a PLM on this port
                            continue
    
                        # successfully opened serial port, so now see if what's on the
                        # other end of the port is an Insteon PLM by asking for it's version
                        success, response = self.send_command('GET_VERSION')
                        if success: 
                            print('Insteon PLM ID= %s.%s.%s; Device category=%s, subcategory=%s; firmware version=%s' % \
                                  ('\\x'+response['id1'].encode('hex'),
                                   '\\x'+response['id2'].encode('hex'),
                                   '\\x'+response['id3'].encode('hex'),
                                   '\\x'+response['dev_cat'].encode('hex'),
                                   '\\x'+response['dev_subcat'].encode('hex'), 
                                   '\\x'+response['firm_ver'].encode('hex')))
                            break  # found PLM, so all done
                        else:
                            print('  --> failed to send IM command to serial port')
                            self.plm.close()
                            self.plm = None # assume not a PLM on this port
                    else:
                        print('  --> not an FTDI UART')
                else:
                    print('  --> not a USB serial device')
            else:
                print('  --> nothing connected to the port')
    
        # if we get here without finding a PLM on a USB port, then
        # we've exhausted all possibilities and must raise an error
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
        #print self.commands


    def get_plm(self):

        return self.plm

    def is_initialized(self):

        return self.state == 'initialized'

