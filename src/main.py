#!/usr/bin/env python3

"""
    main.py: Script to instantiate Nebula network.

    Author: Samuel Vojtas
"""

import sys, os

from argument_parser import parse_args
from network_starter import init_network
from container_starter import run_containers

PROJECT_DIR = os.path.abspath(os.path.join(__file__, '..', '..'))
NETWORK_CONFIG = os.path.join(PROJECT_DIR, 'conf', 'network-config.yaml')

if __name__ == '__main__':
    # Parse arguments for the script
    args = parse_args(sys.argv, len(sys.argv))
    if args.config_file:
    	network_config = os.path.abspath(args.config_file)
    else:
        network_config = os.path.abspath(NETWORK_CONFIG)

    # Generate all necessary files for the network into ${PROJECT_DIR}/generated
    init_network(network_config)

    # Create containers for all network clients, distribute all their files to those containers and start Nebula service
    if not args.no_containers:
        run_containers(network_config, init_lighthouse_container=not args.no_lighthouse_container)

