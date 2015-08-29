from command import Command, CommandInterface

class Services(Command):

    def __init__(self, owning_service, version):

        self.owning_service = owning_service
        choices=self.services_list()

        self.interface = CommandInterface('services', 'List nexus services', version, self,
                                          {'service': {'type':str, 
                                                       'choices':choices, 
                                                       'action':'store', 
                                                       'help':'which service(s) to list'},
                                           '--verbose': {'action':'store_true', 
                                                         'help':'additional detail on each service'}})

    def execute(self, args, output_text):

        if output_text:

            if args.verbose:
                output = ['%s\n  %s\n  State=%s\n  Version=%d\n  Root directory=%s' % \
                          (s.getName(), s.getDescription(), s.getState(), s.getVersion(), s.getPath())
                             for s in self.owning_service.services()
                                 if args.service=='all' or args.service==s.getName()]
            else:
                output = ['%-12s%-15s%7d' % (s.getName(), s.getState(), s.getVersion())
                                           for s in self.owning_service.services()
                                               if args.service=='all' or args.service==s.getName()]
                output.insert(0, 'Name        State          Version')

        else:
        
            output = [s for s in self.owning_service.services()]

        return output

    def services_list(self):

        slist=['all']

        for s in self.owning_service.services():
            slist.append(s.getName())
        return slist

