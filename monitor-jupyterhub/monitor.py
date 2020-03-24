#!/usr/bin/env python3

import docker
from datetime import datetime

BLACKLIST = 'jh.blacklist'
#LOGPATH = 'logs'

# function: get running containers
def get_running_containers(client):

    # get a list of running containers that use the singleuser image
    containers = client.containers.list()
    container_list = []
    container_dict = {}
    for container in containers:
        if 'cuahsi/singleuser' in container.image.tags[0]:
            container_dict['container'] = container
            container_dict['sha'] = container.image.id
            container_dict['username'] = container.name.replace('jupyter-','')
            container_list.append(container_dict)
    return container_list
    

# function: check against blacklist
def check_against_blacklist(username):
    with open(BLACKLIST, 'r') as f:
        blacklisted_users = f.readlines()

    if username in blacklisted_users:
        return True

    return False


# function: update blacklist
def update_blacklist(username):
    with open(BLACKLIST, 'a') as f:
        f.writelines([username])

# function: stop container
def stop_container(container, timeout=1):
    container.stop(timeout=timeout)

# function: get container logs
def get_container_logs(container):
    return container.logs()

# TODO function: send notification email

# function: check container usage
def get_container_stats(containers):
    
    for container_dict in containers:
        c = container_dict['container']
        stats = c.stats(stream=False)
        #container_dict.update(stats['cpu_stats'])
        container_dict['cpu_percent'] = calculate_cpu_percent(stats)
        
    return containers

# function: compute cpu %
def calculate_cpu_percent(d):
    # taken from https://github.com/TomasTomecek/sen/blob/master/sen/util.py#L158 
    cpu_count = len(d["cpu_stats"]["cpu_usage"]["percpu_usage"])
    cpu_percent = 0.0
    cpu_delta = float(d["cpu_stats"]["cpu_usage"]["total_usage"]) - \
                float(d["precpu_stats"]["cpu_usage"]["total_usage"])
    system_delta = float(d["cpu_stats"]["system_cpu_usage"]) - \
                   float(d["precpu_stats"]["system_cpu_usage"])
    if system_delta > 0.0:
        cpu_percent = cpu_delta / system_delta * 100.0 * cpu_count
    return cpu_percent

# function: check container lifespan
def get_container_lifespans(containers):

    # loop through container dictionary and compute container
    # running times in hours
    for container_dict in containers:
        c = container_dict['container']
        started_at = c.attrs['State']['StartedAt'].split('.')[0]
        started_dt = datetime.strptime(started_at, '%Y-%m-%dT%H:%M:%S')
        diff = datetime.utcnow() - started_dt
        hrs = diff.total_seconds() / 3600
        container_dict['lifespan_hrs'] = hrs
        return containers


# function: main
if __name__ == '__main__':
    client = docker.from_env()

    containers = get_running_containers(client)

    containers = get_container_lifespans(containers)

    containers = get_container_stats(containers)

    import pdb; pdb.set_trace()

    # TODO: check all containers against blacklist and kill as necessary
    for container in containers:
        c = container['container']
        username = container['username']
        is_blacklisted = check_against_blacklist(username)
        if is_blacklisted:
            update_blacklist(username)
            stop_container(c)

    # remove containers that are over 1 hour old
    # remove containers that are consuming > 100% cpu
    max_age = 1.0
    max_cpu = 100.0
    for container in containers:
        age = container['lifespan_hrs']
        cpu = container['cpu_percent']
        c = container['container']
        if (age > max_age) or (cpu > max_cpu):
            with open(c['sha']+'.logs', 'w') as f:
                f.write(get_container_logs(c))
            stop_container(c)

            # TODO: add to blacklist

            # TODO: send email



