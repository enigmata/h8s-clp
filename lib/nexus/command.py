

class CommandInterface():
    """
    Anything that wants to work with commands, will do so through
    this command interface. The command interface lives in a command,
    but it is gotten typically from the Config service which obtains
    all command interfaces through the services it has found and
    instantiated.
    """

    def __init__(self, name, description, version, command, args):
        
        self.name        = name
        self.fqn         = command.getService().getServiceName() + '.' + name
        self.description = description
        self.version     = version
        self.command     = command
        self.args        = args
    
    def getName(self):
        return self.name

    def getFQN(self):
        return self.fqn

    def getDescription(self):
        return self.description

    def getVersion(self):
        return self.version

    def getCommand(self):
        return self.command

    def getArgs(self):
        return self.args

    def execute(self, args):
        self.command.execute(args)
        

class Command():
    """
    A Command class is the generic representation of a command of a nexus service,
    which is responsible for carrying out some particular function of the service

    NOTE: You do not instantiate the Command class. A particular service's command 
          will specialize the Command class as a subclass which is then instantiated
          by the owning service.
    """

    def getService(self):
        return self.owning_service

    def getInterface(self):
        return self.interface

