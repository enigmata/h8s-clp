import os
import importlib
import re


class Service():
    """
    A Service class is the generic representation of a nexus service, which
    is responsible for carrying out required functions of the service, and 
    maintaining its own lifecycle. 

    The attributes of a Service:
        Name:         Since word uniquely identifying the service's responsibility
        Description:  One-line English description of the service
        Version:      Triple:  <version>.<release>.<modification>
        Commands:     Behaviours of the service, actions to change state of the service
        State:        State of the service as it progresses through its lifecycle
    
    NOTE: You do not instantiate the Service class. A service will specialize
          the Service class as a subclass which is then instantiated.
    """

    def __init__(self, path, name, description, version):

        self.name = name
        self.description = description
        self.version = version
        self.state = None  # TBD
        self.commands = {}
        self.COMMANDS_IDX_MOD = 0 # command's python module
        self.COMMANDS_IDX_OBJ = 1 # command's python object
        self.COMMANDS_IDX_VER = 2 # version of the command (from filename)
        self.COMMANDS_IDX_SAW = 3 # highest cmd version found in file system
        self.re_command_fname = re.compile(r'^(([^_.].*)_v(\d+))\.py$')
        self.root_dir = path
        self.cmd_dir  = os.path.join(self.root_dir, 'commands')
        self.service_name = os.path.basename(self.root_dir)

    def getName(self):
        return self.name

    def getServiceName(self):
        return self.service_name

    def getDescription(self):
        return self.description

    def getVersion(self):
        return self.version

    def getState(self):
        return self.state

    def getPath(self):
        return self.root_dir

    def load_commands(self):

        for command_fname in os.listdir(self.cmd_dir):
            
            m = self.re_command_fname.match(command_fname)
            if m and os.path.isfile(os.path.join(self.cmd_dir, command_fname)):

                command_name = m.group(2)
                command_ver = long(m.group(3))

                if command_name in self.commands and command_ver > self.commands[command_name][self.COMMANDS_IDX_VER]:

                    # not clear if order of deletion matters, so I will err on the side of caution 
                    del self.commands[command_name][self.COMMANDS_IDX_OBJ] 
                    del self.commands[command_name][self.COMMANDS_IDX_MOD] 
                    del self.commands[command_name]

                if command_name not in self.commands:

                    command_fullname = m.group(1)
                    command_mod = importlib.import_module('services.'+self.service_name+'.commands.'+command_fullname)
                    command_obj = getattr( command_mod, command_name.capitalize() )(self, command_ver)
                    self.commands[command_name] = [ command_mod, command_obj, command_ver, command_ver ]

                else:

                    if command_ver > self.commands[command_name][self.COMMANDS_IDX_SAW]:
                        self.commands[command_name][self.COMMANDS_IDX_SAW] = command_ver


        for command_name in self.commands:

            if self.commands[command_name][self.COMMANDS_IDX_SAW] == self.commands[command_name][self.COMMANDS_IDX_VER]:

                # command loaded is at same version as highest command file on disk,
                # so just reset that we saw it to prepare for the next time we load commands
                self.commands[command_name][self.COMMANDS_IDX_SAW] = 0

            else: # either command file on disk (all vers) are gone, or we're rolling back to earlier ver

                command_ver = self.commands[command_name][self.COMMANDS_IDX_SAW] 

                # not clear if order of deletion matters, so I will err on the side of caution 
                del self.commands[command_name][self.COMMANDS_IDX_OBJ] 
                del self.commands[command_name][self.COMMANDS_IDX_MOD] 
                del self.commands[command_name]

                if command_ver > 0:
                   
                    # we're rolling back to an earlier version of command, and we've already
                    # made room for it because we've deleted the newer version from the dict
                    command_mod = importlib.import_module('services.'+self.service_name+'.commands.'+command_name+'_v'+command_ver)
                    command_obj = getattr( command_mod, command_name.capitalize() )(self, command_ver)
                    self.commands[command_name] = [ command_mod, command_obj, command_ver, 0 ]
    

    def command_interfaces(self):

        for command in self.commands:
            yield self.commands[command][self.COMMANDS_IDX_OBJ].getInterface()


    def execute_command(self, command, args, output_text):

        return self.commands[command][self.COMMANDS_IDX_OBJ].execute(args, output_text)


