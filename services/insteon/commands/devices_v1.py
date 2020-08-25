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
    
            output_mask = '%s  %-19s %-44s %-19s %s'
            if args.verbose:
                output = []
            else:
                output=[output_mask % ('DeviceID','Type','Name','Room','Location')]

            for dev in devices:

                if args.type == 'all' or devices[dev]['type'].lower().endswith(args.type):
                    if args.verbose:
                        output.append('ID = %s\n  Type       : %s\n  Name       : %s\n  Room       : %s\n  Location   : %s\n  Category   : %s\n  Subcategory: %s' % \
                                      (dev,devices[dev]['type'],devices[dev]['name'],devices[dev]['room'],
                                       devices[dev]['location'],devices[dev]['properties']['category'],devices[dev]['properties']['subcategory']))
                    else:
                        output.append(output_mask % (dev,devices[dev]['type'],devices[dev]['name'],devices[dev]['room'],devices[dev]['location']))

        else:
            output=devices

        return output


