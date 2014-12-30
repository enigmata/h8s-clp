from command import Command, CommandInterface

class Command_raw(Command):

    def __init__(self, owning_service, version):

        self.owning_service = owning_service
        self.interface = CommandInterface('command_raw', 'Send Insteon command without protocol control', version, self, 
                                          {'command_string': {'type':str, 
                                                              'nargs':'+', 
                                                              'action':'store', 
                                                              'help':'full command string to send to PLM'}})


    def execute(self, args, output_text):

        if self.owning_service.is_initialized():

            # print args, len(args.command_string)
            if len(args.command_string) > 1:
                cmd_args = args.command_string[1].decode('hex')
                # print '%s \"%r\" %d %r' % 
                #       (args.command_string[1], args.command_string[1].decode('hex'), len(args.command_string[1]), type(args.command_string[1]))
            else:
                cmd_args = ''

            plm = self.owning_service.get_plm()
            success, response = plm.sendCommandRaw(args.command_string[0], cmd_args)
            if success: 
                ret = ['%s = %s' % (key,''.join('\\x'+c.encode('hex') for c in response[key])) for key in response]
                # ret = ['Insteon PLM ID= %r.%r.%r; Device category=%r, subcategory=%r; firmware version=%r' % \
                #         (response['id1'],response['id2'],response['id3'], response['dev_cat'], response['dev_subcat'], 
                #          response['firm_ver'])]
            else:
                ret = ['PLM command execution failure']
        else:
            ret = ['PLM is not initialized']

        return ret

        #if output_text:

        #    output = ['%s\n  %s\n  State=%s\n  Version=%d\n  Root directory=%s' % \
        #              (s.getName(), s.getDescription(), s.getState(), s.getVersion(), s.getPath())
        #                 for s in self.owning_service.services()]

        #else:
        #
        #    output = [s for s in self.owning_service.services()]

        #return output


