import os, sys

from service import Service

class Serial(Service):

    def __init__(self, path):
        Service.__init__(self,
                         path,
                         name='serial', 
                         description = 'Serial port management',
                         version=1)

        self.state = 'initialized'

        self.load_commands()
