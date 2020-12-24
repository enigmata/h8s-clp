from command import Command, CommandInterface

class Commands(Command):
    def __init__(self, owning_service, version):
        self.owning_service = owning_service
        self.plm = owning_service.get_plm()

        self.interface = CommandInterface('commands', 'List Insteon PLM commands', version, self,
                                          {'type': {'type':str, 
                                                    'choices':['send','receive'],
                                                    'action':'store', 
                                                    'help':'which type of command to list'},
                                           '--verbose': {'action':'store_true', 
                                                         'help':'additional detail on each command'}})

    def execute(self, args):
        if args.type == 'send':
            cmds = self.plm.get_send_cmds()
            if args.verbose:
                output = [f'{cmd:30}\n  {cmds[cmd][2]}\n  Command: {cmds[cmd][0]}\n  Syntax:  {cmds[cmd][1]}' for cmd in cmds]
            else:
                output = [f'{cmd:30} {cmds[cmd][0]}' for cmd in cmds]
                output.insert(0, '%-30s %s' % ("Name", "Hex Command String"))
        else:
            cmds = self.plm.get_receive_cmds()
            if args.verbose:
                output = [f'\n{cmds[cmd][2]}\n  Command: {cmd}\n  Msg len: {cmds[cmd][0]} bytes\n  Msg syntax: "{cmds[cmd][1]}"' for cmd in cmds]
            else:
                output = [f'{cmd:8} {cmds[cmd][2]}' for cmd in cmds]
                output.insert(0, '%-8s %s' % ("Command", "Description"))

        return output
