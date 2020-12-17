import json

class DevicesIOError(Exception):
    def __init__(self, msg):
        self.data = msg

class Devices():
    """
    A devices class is the generic representation of the set of devices that
    is managed by a service.

    Common attributes of device:
        Name:        Short identifier of the device
        Type:        Kind of device, using hierachical format where necessary 
                       ('<rootname>/<parentname>/...')
        Room:        Where the device is located in the house
        Location:    Where the device is located in the room
        Active:      Is the device in service
        Properties:  Attributes unique to the device type
    
    NOTE: You do not instantiate the Devices class. A service will specialize
          the Devices class, which is then embedded in this service object
    """

    def __init__(self, service):
        
        try:
            f = open(os.path.join(os.path.dirname(sys.modules[service].__file__), 'devices.json'))
            self.devices = json.load(f)
            f.close()
        except IOError:
            self.devices = {}
            raise DevicesIOError('Cannot read devices.json file')


    def get_device(self):

        for dev in self.devices:
            yield self.devices[dev]

    def get_devices(self):

        return self.devices

