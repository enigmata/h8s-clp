#!/usr/bin/env python

import services.config # well-known service, to bootstrap us in
import argparse
import sys, readline

def buildCmdLineParser(cfg, **parser_args):

    # overall clp cmd parser
    clp_parser = argparse.ArgumentParser(description='Command Line Parser for Nexus', **parser_args)

    subparsers = clp_parser.add_subparsers(title='Nexus commands',
                                           description='Query, or take action against, the nexus',
                                           dest='command', 
                                           help='Command help')

    # "quit" the CLP
    clp_parser_quit = subparsers.add_parser('quit', help='Quit the CLP')
    clp_parser_quit.add_argument('quit', action='store_true',
                                         help='Exit the CLP')

    # "refresh" the CLP in case command set has changed dynamically
    clp_parser_refresh = subparsers.add_parser('refresh', help='Refresh the command set')
    clp_parser_refresh.add_argument('refresh', action='store_true', help='Refresh the commmand set')

    for command in cfg.all_commands():
        
        clp_subparser = subparsers.add_parser(command.getFQN(), help=command.getDescription())

        arg = command.getArgs()

        for arg_name in arg:
            clp_subparser.add_argument(arg_name, **arg[arg_name])

    return clp_parser




def interactiveMode( cfg ):

    clp_parser = buildCmdLineParser(cfg, prog='')

    while True:

        try:
            cmdline = input('> ')
        except EOFError:
            break

        cmdline_tokens = cmdline.split()
        if len(cmdline_tokens) == 0: continue

        try:
            args = clp_parser.parse_args(cmdline_tokens)
        except:
            # command line help was requested, so no args are available
            args = None
        else:
            # proper command was entered, process result
            #print '\nArgs = %r' % args

            if args.command=='quit' and args.quit:
                break
            elif args.command=='refresh' and args.refresh:
                print('TODO: code to refresh commands thru config service')
            else:
                output = cfg.execute_service_command( args.command, args, output_text = True )
                print
                for line in output: print(line)



if __name__ == '__main__':

    cfg = services.config.Config()

    interactiveMode(cfg)

    # TODO: only support one mode: interactive or batch, then
    #       convert into main() with a return code thereby
    #       allowing the cleaner:  sys.exit(main())
    sys.exit(0)

