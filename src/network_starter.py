#!/usr/bin/env python3

"""
    network_starter.py: Generate files for Nebula network in ${PROJECT_DIR}/generated.

    Author: Samuel Vojtas
"""

import os, yaml, subprocess

PROJECT_DIR = os.path.abspath(os.path.join(__file__, '..', '..'))
NETWORK_CONFIG = os.path.join(PROJECT_DIR, 'conf', 'network-config.yaml')
DEFAULT_CONFIG = os.path.join(PROJECT_DIR, 'conf', 'default-config.yaml')

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

def parse_config(network_config):
    """
    Parse main configuration file, whose path is provied in "network_config" argument.
    """
    # Load YAML configuration
    with open(network_config, 'r') as fp:
        config = yaml.safe_load(fp)

    # Check if all resource names & IPs are unique
    resources = config['resources']
    names = list(map(lambda resource : resource.get('name'), resources))
    ips   = list(map(lambda resource : resource.get('ip'), resources))

    if len(names) != len(set(names)):
        print('  [*] Configuration file contains duplicite names')
        print('  [*] Exiting...')
        exit(EXIT_FAILURE)

    if len(ips) != len(set(ips)):
        print('  [*] Configuration file contains duplicite ips')
        print('  [*] Exiting...')
        exit(EXIT_FAILURE)

    # Check if lighthouse information is specified in config
    if 'lighthouse' not in config.keys():
        print('  [*] Lighoutse information is missing in the configuration file')
        print('  [*] Exiting...')
        exit(EXIT_FAILURE)

    if 'name' not in config['lighthouse'] or 'ip' not in config['lighthouse'] or 'routable_ip' not in config['lighthouse'] or 'routable_port' not in config['lighthouse']:
        print('  [*] Not enough information about the lighthouse')
        print('  [*] Exiting...')
        exit(EXIT_FAILURE)

    # Check format of IP for lighthouse
    lighthouse_ip, lighthouse_subnet_length = config['lighthouse']['ip'].split('/')
    if not lighthouse_ip or not lighthouse_subnet_length:
        print('  [*] IP or subnetlength of the lighthouse was wrongly specified')
        print('  [*] Exiting...')
        exit(EXIT_FAILURE)

    # Check if all resources have properly specified information
    for idx, resource in enumerate(config['resources']):
        if 'name' not in resource or 'ip' not in resource:
            print('  [*] Not enough information about the resource no. {idx + 1}')
            print('  [*] Exiting...')
            exit(EXIT_FAILURE)
        
        # Check format for IP for the resource
        ip, subnet_length = resource['ip'].split('/')
        if not ip or not subnet_length:
            print('  [*] IP or subnetlength of the resource was wrongly specified')
            print('  [*] Exiting...')
            exit(EXIT_FAILURE)

    print(f'  [*] Configuration file {network_config} was parsed')

    return config

def get_default_config():
    """
    Retrieve a dictionary from default configuration for the resource.
    """
    with open(DEFAULT_CONFIG, 'r') as fp:
        default_config = yaml.safe_load(fp)

    return default_config

def init_ca():
    """
    Create new Certificate Authority (CA) for signing certificates.
    """

    print('  [*] Creating new certificate authority')

    cmd = f'{PROJECT_DIR}/bin/nebula-cert ca -name "cybersecurity-project"'
    rv = subprocess.run(cmd.split(' '))

    if rv.returncode == EXIT_FAILURE:
        print('  [*] Certificate authority already exists')
        print('  [*] Exiting...')
        exit(EXIT_FAILURE)
    else:
        print('  [*] Certificate authority successfully created')

    return EXIT_SUCCESS

def is_ca_initialised():
    """
    Check if CA is already created, i.e. there is ca.key & ca.crt in generated files.
    """
    rv = os.path.exists('ca.key') and os.path.exists('ca.crt')
    if rv:
        print('  [*] ca.crt & ca.key already exists')
        print('  [*] Certificates and keys will not be generated')
    return rv

def create_certificate(resource):
    """
        Private key ({name}.key) & certificate ({name}.crt) for given ressource is created.
    """

    # Check if resource has a valid name
    if 'name' not in resource.keys():
        print('  [*] Resource does not have name specified')
        print('  [*] Exiting...')
        exit(EXIT_FAILURE)
    else:
        name = resource['name']

    # Check if resource has a valid IP address
    if 'ip' not in resource.keys():
        print('  [*] Resource does not have an IP address specified')
        print('  [*] Exiting...')
        exit(EXIT_FAILURE)
    else:
        ip = resource['ip']

    # Check if resource is assigned a group (this is not mandatory)
    if 'groups' in resource.keys():
        groups = resource['groups']
    else:
        groups = None

    cmd = [
        f'{PROJECT_DIR}/bin/nebula-cert',
        'sign',
        '-name', name,
        '-ip', f'{ip}',
    ]
    if groups:
        cmd = cmd + ['-groups', ','.join(groups)]

    rv = subprocess.run(cmd)

    if rv.returncode == EXIT_FAILURE:
        print(f'  [*] Resource \"{name}\" could not be signed')
        print(f'  [*] Exiting...')
        exit(EXIT_FAILURE)
    else:
        print(f'  [*] Certificate for resource \"{name}\" created')

    return EXIT_SUCCESS

def init_lighthouse(global_config_lighthouse):
    """
    Initialise the lighthouse for the network.
    """

    ip = global_config_lighthouse['ip']
    ip, subnet_length = ip.split('/')
    routable_ip = global_config_lighthouse['routable_ip']
    routable_port = global_config_lighthouse['routable_port']
    
    lighthouse_config = get_default_config()

    # Set this resource to be the lighthouse
    lighthouse_config['lighthouse']['am_lighthouse'] = True
    # Add only the lighthouse to its static_host_map
    lighthouse_config['static_host_map'] = {
        ip: [routable_ip + ':' + routable_port]
    }

    # Dump the configuration file for lighthouse
    with open('lighthouse-config.yaml', 'w') as fp:
        yaml.dump(lighthouse_config, fp)

    print('  [*] Configuration for lighthouse created - lighthouse-config.yaml')

    return EXIT_SUCCESS

def init_resource(global_config_resource, global_config_lighthouse):
    """
    Initialise one resource of the network.
    """
    name = global_config_resource['name']
    ip = global_config_resource['ip']
    ip, subnet_length = ip.split('/')
    groups = []
    if 'groups' in global_config_resource.keys():
        groups = global_config_resource['groups']

    lighthouse_ip = global_config_lighthouse['ip']
    lighthouse_ip, subnet_length = lighthouse_ip.split('/')
    lighthouse_routable_ip = global_config_lighthouse['routable_ip']
    lighthouse_routable_port = global_config_lighthouse['routable_port']

    resource_config = get_default_config()

    # Resource has to know how to find the lighthouse -> add the lighthouse to the static_host_map
    resource_config['static_host_map'] = {
            lighthouse_ip: [lighthouse_routable_ip + ':' + lighthouse_routable_port]
    }

    # Add lighthouse to the list of lighthouses
    resource_config['lighthouse']['hosts'] = [lighthouse_ip]

    # Set up firewall
    # Create new inbound firewall rule for each group the resource is in
    # ICMP is allowed by default
    inbound_rules = [{
        'port': 'any',
        'host': 'any',
        'proto': 'icmp'
    }]
    for group in groups:
        inbound_rules.append({
            'port': 'any',
            'group': group,
            'proto': 'any'
        })
    resource_config['firewall']['inbound'] = inbound_rules

    with open(f'{name}-config.yaml', 'w') as fp:
        yaml.dump(resource_config, fp)

    print(f'  [*] Configuration for resource {name} created - {name}-config.yaml')

    return EXIT_SUCCESS
    

def init_network(network_config):
    """
    Initialise network - thus the lighthouse, and all the resources.
    """
    # All files will be created in PROJECT_DIR/generated directory
    generated_dir = os.path.join(PROJECT_DIR, 'generated')
    if not os.path.exists(generated_dir):
        os.mkdir(generated_dir)
    else:
        os.chdir(generated_dir)
        contents = os.listdir(generated_dir)
        if os.listdir(generated_dir) != []:
            choice = input(f'  [*] Directory {generated_dir} already exists and it is not empty. Removing all its contents [Y/n] ')
            if choice.lower() != 'y':
                print('  [*] Exiting...')
                exit(EXIT_FAILURE)
            else:
                for f in contents:
                    os.remove(f)

    # Change directory there so all files will be created in this folder
    os.chdir(generated_dir)

    config = parse_config(network_config)

    # Do not initialise new CA if it is already initialised
    if not is_ca_initialised():
        init_ca()

        # Creat certificates
        create_certificate(config['lighthouse'])
        for resource in config['resources']:
            create_certificate(resource)

    # Create config files
    init_lighthouse(config['lighthouse'])
    for resource in config['resources']:
        init_resource(resource, config['lighthouse'])

if __name__ == '__main__':
    init_network(NETWORK_CONFIG)
