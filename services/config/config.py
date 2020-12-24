import sys, os, importlib

root_dir = sys.path[0]
lib_root_dir   = os.path.join(root_dir,'lib')

lib_dirs = [os.path.join(lib_root_dir, dirname) 
               for dirname in os.listdir(lib_root_dir)
                   if os.path.isdir(os.path.join(lib_root_dir, dirname)) and
                      not dirname.startswith('.')]

for dir in range(len(lib_dirs)):
    if os.path.isdir(os.path.join(lib_dirs[dir], 'lib')):
       lib_dirs[dir] = os.path.join(lib_dirs[dir], 'lib') 
    sys.path.insert(1, lib_dirs[dir])

from service import Service

class Config(Service):
    def __init__(self):
        self.service_modules = {}
        self.SERVICE_MODULES_IDX_MOD = 0
        self.SERVICE_MODULES_IDX_OBJ = 1
        self.services_dir = os.path.join(root_dir,'services')

        for service_name in os.listdir(self.services_dir):
            if not service_name == 'config' and not service_name.startswith('__'):
                service_dir = os.path.join(self.services_dir, service_name)
                if os.path.isdir(service_dir): 
                    service_key = 'services.' + service_name
                    service_mod = importlib.import_module( service_key )
                    service_obj = getattr( service_mod, service_name.capitalize() )(service_dir)
                    self.service_modules[service_key] = [ service_mod, service_obj ]

        Service.__init__(self,
                         os.path.join(self.services_dir, 'config'),
                         name='config', 
                         description = 'Manages the configuration of the mesh',
                         version=1)

        self.state = 'initialized'

        self.load_commands()

    def services(self):
        for service in self.service_modules:
            yield self.service_modules[service][ self.SERVICE_MODULES_IDX_OBJ ]
        yield self


    def all_commands(self):
        for service in self.services():
            for command in service.command_interfaces():
                yield command


    def execute_service_command(self, command, args):
        service,cmd = command.split('.')

        if service == 'config':
            output = self.execute_command(cmd, args)
        else:
            output = self.service_modules['services.'+service][self.SERVICE_MODULES_IDX_OBJ].execute_command(cmd, args)

        return output
