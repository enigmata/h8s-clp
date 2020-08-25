from command import Command, CommandInterface

class Monitor(Command):

    def __init__(self, owning_service, version):

        self.owning_service = owning_service
        self.interface = CommandInterface('monitor', 'Monitor Insteon messages', version, self, 
                                          {'command_string': {'type':str, 
                                                              'nargs':'+', 
                                                              'action':'store', 
                                                              'help':'full command string to send to PLM'}})


    def execute(self, args, output_text):

        if self.owning_service.is_initialized():

            plm = self.owning_service.get_plm()
            plm.monitor()
            ret = ['Monitoring terminated']
        else:
            ret = ['PLM is not initialized']

        return ret

