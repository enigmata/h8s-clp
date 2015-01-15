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
            print 'before cmdstr=%r, len=%d' % (cmdstr, len(cmdstr))
            cmdstr = ''.join([cmdstr,args])
            print 'after cmdstr=%r, len=%d' % (cmdstr,len(cmdstr))
            writelen = len(cmdstr)
            numwritten = self.plm.write( cmdstr )
            print 'wrote %d of %d' % (numwritten, writelen)
            if numwritten == writelen:
                # need to clear out any leading nulls or garbage, until
                # we see the STX (Start TeXt) byte signaling the beginning
                # of the reply string proper
                byteread = self.plm.read(1)
                print 'first byte read=%r' % byteread
                while byteread != self.IMParms['IM_COMM_STX']:
                    print 'not STX: %r' % byteread
                    byteread = self.plm.read(1)

                # now we can get the proper IM response string
                response = self.plm.read(respLen) 
                print 'response=%r, actual len=%d, expected len=%d' % (response, len(response), respLen)
    
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
        USBDevices = glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    
        # test each serial device to see if an Insteon PLM is attached
        for device in USBDevices:
            try:
                print 'serial port: %s' % (device)
                self.plm = serial.Serial(port=device, baudrate=self.IMParms['IM_BAUDRATE'], 
                                                      timeout=self.IMParms['IM_CMD_TIMEOUT'])
            except serial.SerialException:  # TODO: convert each exception to a log write
                print 'Failed to configure serial port: %s' % (device)
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
    
            print 'Failed to send IM command to serial port %s' % (device)
            self.plm.close()
            self.plm = None # assume not a PLM on this port
    
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

