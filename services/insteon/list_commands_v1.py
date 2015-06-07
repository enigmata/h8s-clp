from command import Command, CommandInterface

class List_commands(Command):

    def __init__(self, owning_service, version):

        self.owning_service = owning_service
        self.plm = owning_service.get_plm()

        self.interface = CommandInterface('list_commands', 'List Insteon PLM commands', version, self,
                                          {'type': {'type':str, 
                                                    'choices':['send','receive'],
                                                    'action':'store', 
                                                    'help':'which type of command to list'},
                                           '--verbose': {'action':'store_true', 
                                                         'help':'additional detail on each command'}})

    def execute(self, args, output_text):

        if args.type == 'send':
            cmds = self.plm.get_send_cmds()
        else:
            cmds = self.plm.get_receive_cmds()

        if output_text:
    
            if args.type == 'send':
                if args.verbose:
                    output = ['%s\n  hex cmd string=%s\n  reply len=%d\n  reply regex=%s\n  syntax=%s\n  help=%s' % \
                              (cmd, ''.join('\\x'+c.encode('hex') for c in cmds[cmd][0]), cmds[cmd][1], cmds[cmd][2], cmds[cmd][3], cmds[cmd][4])
                                 for cmd in cmds]
                else:
                    output = ['%-30s %s' % (cmd, ''.join('\\x'+c.encode('hex') for c in cmds[cmd][0])) for cmd in cmds]
                    output.insert(0, 'Name                           Hex Command String')
            else:
                output=['tbd']

        else:
            output=cmds

        return output


