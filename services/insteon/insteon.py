from .insteon_plm import InsteonPLM, InsteonPLMConfigError
from service import Service

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

