#!/usr/bin/env python3


import getpass
from hs_restclient import (HydroShare,
                           HydroShareAuthBasic,
                           HydroShareHTTPException)


def __connect(username, host='www.hydroshare.org', verify=True):
    u = username
    p = getpass.getpass('Password:')
    auth = HydroShareAuthBasic(username=u, password=p)
    return HydroShare(hostname=host, auth=auth, verify=verify)


def connect(host='www.hydroshare.org', verify=True):
    u = input('username: ')
    return __connect(u, host=host, verify=verify)


def authenticate(username, host='www.hydroshare.org', tries=3, 
                 ssl_verification=True):

    auth_success = False
    attempt = 1
    while not auth_success:
        hs = __connect(username, host, verify=ssl_verification)
        try:
            hs.getUserInfo()
            auth_success = True
        except HydroShareHTTPException:
            print('  Authorization Failed - Attempt %d' % attempt)
        attempt += 1
        if attempt > tries:
            print('  Authorization Failed')
            return 0

    print('  Authorization Successful')
    return hs
