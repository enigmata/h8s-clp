from command import Command, CommandInterface

class Send_cmd(Command):
    def __init__(self, owning_service, version):

        self.owning_service = owning_service
        self.interface = CommandInterface('send_cmd', 'Send Insteon command without protocol control', version, self, 
                                          {'command_string': {'type':str, 
                                                              'nargs':'+', 
                                                              'action':'store', 
                                                              'help':'full command string to send to PLM'}})

    def execute(self, args):
        if self.owning_service.is_initialized():
            if len(args.command_string) > 1:
                cmd_args = args.command_string[1].decode('hex')
            else:
                cmd_args = ''

            plm = self.owning_service.get_plm()
            success, response = plm.send_command(args.command_string[0], cmd_args)
            if success: 
                ret = ['  --> %s = %s' % (key,''.join('\\x'+c.encode('hex') for c in response[key])) for key in response]
            else:
                ret = ['PLM command execution failure']
        else:
            ret = ['PLM is not initialized']

        return ret
