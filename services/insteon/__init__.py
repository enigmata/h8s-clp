import serial
import glob
import re
import yaml
#import json
import os
import sys
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

        self.IMSendCmds, self.IMReceiveCmds, self.IMParms = yaml.load_all(stream)
        if not self.IMSendCmds or not self.IMReceiveCmds or not self.IMParms:
            stream.close()
            raise InsteonPLMConfigError('Cannot read insteon.yaml config file')

        stream.close()

    def get_send_cmds(self):

        return self.IMSendCmds

    def get_receive_cmds(self):

        return self.IMReceiveCmds

    def sendCommandRaw(self, cmd, args=''):
        """
        Send a command to the PLM without governance by the protocol.
        That is, allow any valid command to be sent to the PLM without
        checking if it is a valid successor to the previous command.
        """

        responseGroups = {}
        commandSuccessful = False
        cmd = cmd.upper()

        if cmd in self.IMSendCmds:
            cmdstr, respLen, respRegex, syntax, cmdhelp = self.IMSendCmds[cmd]
            #print '  --> before cmdstr=%r, len=%d' % (cmdstr, len(cmdstr))
            cmdstr = ''.join([cmdstr,args])
            print '  --> cmdstr=%r, len=%d' % (cmdstr,len(cmdstr))
            writelen = len(cmdstr)
            numwritten = self.plm.write( cmdstr )
            #print '  --> wrote %d of %d' % (numwritten, writelen)
            if numwritten == writelen:
                # need to clear out any leading nulls or garbage, until
                # we see the STX (Start TeXt) byte signaling the beginning
                # of the reply string proper
                retries = 50
                byteread = self.plm.read(1)
                print '  --> first byte read=%r' % byteread
                while (retries > 0 and byteread != self.IMParms['IM_COMM_STX']):
                    print '  --> not STX: %r' % byteread
                    byteread = self.plm.read(1)
                    retries -= 1

                if retries > 0:

                    # now we can get the proper IM response string
                    response = self.plm.read(respLen) 
                    print '  --> response=%r, actual len=%d, expected len=%d' % (response, len(response), respLen)
    
                    # validate the response
                    m = re.match(respRegex, response)
                    if m: 
                        responseGroups = m.groupdict()
                        if responseGroups['ack'] == self.IMParms['IM_CMD_SUCCESS']:
                            commandSuccessful = True
                        else:
                            responseGroups = {}

        return commandSuccessful, responseGroups 


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

            print 'testing serial port: %s' % (device)

            # check to see if something is connected to the port
            base = os.path.basename(device)
            if os.path.exists('/sys/class/tty/%s/device' % (base,)):
                # the insteon PLM is a USB-Serial device, so chk if that is what we have
                sys_dev_path = '/sys/class/tty/%s/device/driver/%s' % (base, base)
                if os.path.exists(sys_dev_path):
                    sys_usb = os.path.dirname(os.path.dirname(os.path.realpath(sys_dev_path)))

                    vendor = read_line(sys_usb+'/idVendor')
                    product = read_line(sys_usb+'/idProduct')
                    print '  --> USB device vendor_id:product_id=%s:%s' % (vendor,product)

                    # insteon PLM is an FTDI (vendor=0403) USB USART (product=6001)
                    if (vendor == '0403' and product == '6001'):

                        # chk if this FTDI USB UART is an insteon PLM
                        try:
                            self.plm = serial.Serial(port=device, baudrate=self.IMParms['IM_BAUDRATE'], timeout=5)
                        except serial.SerialException:  # TODO: convert each exception to a log write
                            print '  --> Failed to open serial port'
                            self.plm = None # assume not a PLM on this port
                            continue
                        except OSError:
                            print '  --> Unable to access serial port'
                            self.plm = None # assume not a PLM on this port
                            continue
    
                        # successfully opened serial port, so now see if what's on the
                        # other end of the port is an Insteon PLM by asking for it's version
                        success, response = self.sendCommandRaw('GET_VERSION')
                        if success: 
                            print 'Insteon PLM ID= %r.%r.%r; Device category=%r, subcategory=%r; firmware version=%r' % \
                                  (response['id1'],response['id2'],response['id3'], response['dev_cat'], response['dev_subcat'], 
                                   response['firm_ver'])
                            break  # found PLM, so all done
                        else:
                            print '  --> failed to send IM command to serial port'
                            self.plm.close()
                            self.plm = None # assume not a PLM on this port
                    else:
                        print '  --> not an FTDI UART'
                else:
                    print '  --> not a USB serial device'
            else:
                print '  --> nothing connected to the port'
    
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
            print 'Insteon PLM config error: %s' % (PLMerr.data)
            self.state = 'uninitialized'
        else:
            print 'Insteon PLM found and configured successfully'
            self.state = 'initialized'

        self.load_commands()
        #print self.commands


    def get_plm(self):

        return self.plm

    def is_initialized(self):

        return self.state == 'initialized'

