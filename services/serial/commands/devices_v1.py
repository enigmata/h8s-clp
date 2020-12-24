import os
import serial.tools

from command import Command, CommandInterface

if os.name == 'posix':
    from serial.tools.list_ports_posix import comports
else:
    raise ImportError(f'ERROR: platform ("{os.name}") not supported')

class Devices(Command):
    def __init__(self, owning_service, version):

        self.owning_service = owning_service

        self.interface = CommandInterface('devices', 'List serial devices', version, self,
                                          {'--verbose': {'action':'store_true',
                                                         'help':'additional detail on each device'},
                                           '--symlinks': {'action':'store_true',
                                                          'help':'include symlinks to real devices'},
                                           '--entry': {'type':int,
                                                       'help':'list the numbered entry'}
                                            })

    def execute(self, args):
        devices= sorted(comports(include_links=args.symlinks))
        return [f'{port}' + (f'\n   ID={hwid}: {desc}' if args.verbose else '')
                  for entry, (port, desc, hwid) in enumerate(devices, 1)
                      if args.entry is None or args.entry == entry]
