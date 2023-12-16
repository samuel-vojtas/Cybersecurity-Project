#!/usr/bin/env python3

"""
    argument_parser.py: Module for parsing arguments.

    Author: Samuel Vojtas
"""

import argparse

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

def parse_args(argv, argc):
    """ Parse arguments for the script """

    parser = argparse.ArgumentParser(description=
            """Instantiate Nebula network based on a configuration file. Create CA, certificates & keys for clients of the network in ${PROJ}/generated directory. 

            In case \"--init-containers\" flag was specified, create Docker containers for network clients, distribute their files to assigned containers and start Nebula service.
            """)

    parser.add_argument(
        '--no-containers',
        help='DO NOT instantiate containers for clients of the network',
        action='store_true',
    )

    parser.add_argument(
        '--config-file',
        help='specify configuration file for the network, default is ${PROJ}/conf/network-config.yaml'
    )

    args, unknown_args = parser.parse_known_args()

    if unknown_args:
        parser.print_help()
        exit(EXIT_FAILURE)

    return args
