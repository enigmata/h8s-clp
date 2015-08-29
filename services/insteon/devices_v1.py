from command import Command, CommandInterface

class Devices(Command):

    def __init__(self, owning_service, version):

        self.owning_service = owning_service
        self.plm = owning_service.get_plm()

        self.interface = CommandInterface('devices', 'List Insteon devices', version, self,
                                          {'type': {'type':str, 
                                                    'choices':['all','switchlinc','lamplinc','outletlinc','inlinelinc','keypadlinc','plm'],
                                                    'action':'store', 
                                                    'nargs':'?',
                                                    'default':'all',
                                                    'help':'which type of device to list'},
                                           '--verbose': {'action':'store_true', 
                                                         'help':'additional detail on each device'}})

    def execute(self, args, output_text):

        devices = self.plm.get_devices()

        if output_text:
    
            output=['DeviceID  Type         Name']

            for dev in devices:

                if args.type == 'all' or args.type == devices[dev]['type'].lower():
                    if args.verbose:
                        output.append('%s\n  Type       : %s\n  Name       : %s\n  Room       : %s\n  Location   : %s\n  Category   : %s\n  Subcategory: %s' % \
                                      (dev,devices[dev]['type'],devices[dev]['display_name'],devices[dev]['room'],
                                       devices[dev]['location'],devices[dev]['category'],devices[dev]['subcategory']))
                    else:
                        output.append('%s  %-12s %s' % (dev,devices[dev]['type'],devices[dev]['display_name']))

        else:
            output=devices

        return output


