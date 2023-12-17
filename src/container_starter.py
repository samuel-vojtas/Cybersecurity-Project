#!/usr/bin/env python3

'''
    container_starter.py: Run containers, distribute keys & certificates among them and start Nebula service on them

    Author: Samuel Vojtas
'''

import os, yaml, subprocess

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
IMAGE = 'nebula-image'
PROJ_DIR = os.path.abspath(os.path.join(__file__, '..', '..'))
CONTAINER_DIR = '/home/root/proj'
GENERATED_DIR = os.path.join(PROJ_DIR, 'generated')
NETWORK_CONFIG = os.path.join(PROJ_DIR, 'conf', 'network-config.yaml')

def collect_names(network_config):
    """
    Collect names for the resources (including the lighthouse) to create the containers.
    """
    with open(network_config, 'r') as fp:
        config = yaml.safe_load(fp)

    names = []

    try:
        names.append(config['lighthouse']['name'])

        for resource in config['resources']:
            names.append(resource['name'])

    except KeyError:
        print('  [*] There is a resource with unspecified name')
        print('  [*] Exiting...')
        exit(EXIT_FAILURE)

    return names

def init_container(name):
    """
    Init container with given name.
    """
    # Start the container
    subprocess.run([
        'docker', 'run', '-it', '--rm', '--cap-add=NET_ADMIN', '--detach', '--name', name, f'--volume={PROJ_DIR}:{CONTAINER_DIR}', IMAGE 
    ])

    # Create TUN device
    subprocess.run([
        'docker', 'exec', name, 'mkdir', '-p', '/dev/net'
    ])
    subprocess.run([
        'docker', 'exec', name, 'mknod', '/dev/net/tun', 'c', '10', '200'
    ])
    subprocess.run([
        'docker', 'exec', name, 'chmod', '666', '/dev/net/tun'
    ])

    # Create Nebula configuration directory
    subprocess.run([
        'docker', 'exec', name, 'mkdir', '-p', '/etc/nebula'
    ])

    # Copy the files to the container
    subprocess.run([
        'docker', 'cp', os.path.join(GENERATED_DIR, 'ca.crt'), f'{name}:/etc/nebula/ca.crt'
    ])
    subprocess.run([
        'docker', 'cp', os.path.join(GENERATED_DIR, name + '-config.yaml'), f'{name}:/etc/nebula/config.yaml'
    ])
    subprocess.run([
        'docker', 'cp', os.path.join(GENERATED_DIR, name + '.crt'), f'{name}:/etc/nebula/host.crt'
    ])
    subprocess.run([
        'docker', 'cp', os.path.join(GENERATED_DIR, name + '.key'), f'{name}:/etc/nebula/host.key'
    ])

def start_nebula(name):
    """
    Start Nebula service.
    """
    subprocess.run([
        'docker', 'exec', '--detach', name, 'nebula', '-config', '/etc/nebula/config.yaml'
    ])

def run_containers(network_config=NETWORK_CONFIG, init_lighthouse_container=True):
    """
    Run all containers and distribute them the files for Nebula network. Then, start the Nebula service on them.
    """
    names = collect_names(network_config)

    # Skip the first entry (lighthouse entry) in the script if lighthouse container should not be initialised
    if not init_lighthouse_container:
        names = names[1:]

    # Distribute the files
    for name in names:
        init_container(name)

    print('  [*] Nebula files were distributed among the containers')

    if not init_lighthouse_container:
        input('  [*] Waiting to start Nebula service on remote lighthouse')

    print('  [*] Starting Nebula service on the containers')
    # Start the Nebula service
    for name in names:
        # Lighthouse is the first entry in the list, so it will always be started as first container (if it is in the list)
        start_nebula(name)

if __name__ == '__main__':
    run_containers(network_config=NETWORK_CONFIG, init_lighthouse_container=True)
    
