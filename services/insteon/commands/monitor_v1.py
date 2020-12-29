from command import Command, CommandInterface

class Monitor(Command):
    def __init__(self, owning_service, version):
        self.owning_service = owning_service
        self.interface = CommandInterface('monitor', 'Monitor Insteon messages', version, self, 
                                          {'--filter_command': {'type':str,
                                                                'dest':'num',
                                                                'action':'store',
                                                                'help':'show only received msgs of this command number'}})

    def execute(self, args):
        if self.owning_service.is_initialized():
            plm = self.owning_service.get_plm()
            plm.monitor(args.num)
            ret = ['Monitoring terminated']
        else:
            ret = ['PLM is not initialized']

        return ret
