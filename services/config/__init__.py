import sys, os, importlib

# set up the import path to find the (3rd party) libs we need
nexus_root_dir = sys.path[0]
lib_root_dir   = os.path.join(nexus_root_dir,'lib')

lib_dirs = [os.path.join(lib_root_dir, dirname) 
               for dirname in os.listdir(lib_root_dir)
                   if os.path.isdir(os.path.join(lib_root_dir, dirname)) and
                      not dirname.startswith('.')]

for dir in range(len(lib_dirs)):
    if os.path.isdir(os.path.join(lib_dirs[dir], 'lib')):
       lib_dirs[dir] = os.path.join(lib_dirs[dir], 'lib') 
    sys.path.insert(1, lib_dirs[dir])

#print lib_dirs

from service import Service

class Config(Service):

    def __init__(self):

        # import the services modules dynamically
        self.service_modules = {}
        self.SERVICE_MODULES_IDX_MOD = 0
        self.SERVICE_MODULES_IDX_OBJ = 1
        self.services_dir = os.path.join(nexus_root_dir,'services')

        for service_name in os.listdir(self.services_dir):

            if not service_name == 'config':
                service_dir = os.path.join(self.services_dir, service_name)
                if os.path.isdir(service_dir): 

                    service_key = 'services.' + service_name
                    service_mod = importlib.import_module( service_key )
                    service_obj = getattr( service_mod, service_name.capitalize() )(service_dir)
                    self.service_modules[service_key] = [ service_mod, service_obj ]

        #print self.service_modules

        # finally, set us up as a proper service
        Service.__init__(self,
                         os.path.join(self.services_dir, 'config'),
                         name='config', 
                         description = 'Manages the configuration of the nexus',
                         version=1)

        self.state       = 'initialized'

        self.load_commands()
        #print self.commands


    def services(self):

        for service in self.service_modules:
            yield self.service_modules[service][ self.SERVICE_MODULES_IDX_OBJ ]
        yield self


    def all_commands(self):

        for service in self.services():
            for command in service.command_interfaces():
                yield command


    def execute_service_command(self, command, args, output_text):
 
        service,cmd = command.split('.')

        if service == 'config':
            output = self.execute_command(cmd, args, output_text)
        else:
            output = self.service_modules['services.'+service][self.SERVICE_MODULES_IDX_OBJ].execute_command(cmd, args, output_text)

        return output



