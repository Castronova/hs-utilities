#!/usr/bin/env python3

import os
import sys
import time
import signal
import getpass
import datetime
import pandas as pd
import multiprocessing as mp
import hs_restclient as hsapi
from multiprocessing import Value, Lock


class Timeout():
    """
    Timeout class using ALARM signal.
    """

    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()


def check_resource_for_spam(q, out_q, hs, val, lock):
    """
    Checks if the given resource is spam
    """

    while True:
        resid = q.get()
        if resid is None:
            return

        with Timeout(10):
            sysmeta = hs.getSystemMetadata(resid)
            title = None
            if sysmeta['public']:
                scimeta = hs.getScienceMetadata(resid)
                title = scimeta['title']

                # TODO: check if the resource is spam.
                # maybe implement a spam classifier using scikit learn
                # https://medium.com/@kopilov.vlad/detect-sms-spam-in-kaggle-with-scikit-learn-5f6afa7a3ca2
                # ...
                # for now, performing a very crude and slow matching
                keywords = ['cheap',
                            'deal',
                            'airlines',
                            'airline',
                            'frontier',
                            'southwest',
                            'packages',
                            'vacation']
                text = title.lower()
                spam = False
                for kw in keywords:
                    if kw in text:
                        spam = True

                # add spam to the` output queue
                if spam:
                    out_q.put([resid, title])

                    with lock:
                        val.value += 1
                        print('\r--> checking for spam resources... found %d '
                              % val.value, end='', flush=True)


def split_date_range(n):
    begin = datetime.date(2015, 5, 1)
    end = datetime.datetime.now().date()
    intervals = n

    date_list = []
    delta = (end - begin)/intervals
    st = begin
    for i in range(1, intervals + 1):
        et = begin+i*delta
        date_list.append([st, et])
        st = et

    return date_list


def query_resource_ids(in_q, out_q, hs, val, lock):
    """
    Queries HS resource IDs
    """

    while True:
        st, et = in_q.get()
        if st is None:
            break

        resources = hs.resources(from_date=st, to_date=et)
        for resource in resources:
            resid = resource['resource_id']
            out_q.put(resid)

            with lock:
                val.value += 1
                print('\r--> collecting resource ids... found %d ' % val.value,
                      end='', flush=True)



def collect_resource_ids(hs):
    """
    Invokes the resource search using MultiProcessing
    """

    NCORE = mp.cpu_count()
    in_q = mp.Queue()
    out_q = mp.Queue()
    v = Value('i', 0)
    lock = Lock()

    print('--> populating job queue ', end='')
    # split the date range of HS resources
    dates = split_date_range(1000)
    for date in dates:
        in_q.put(date)
    # tell workers to exit
    for _ in range(NCORE):
        in_q.put([None, None])

    print('\n--> collecting resource ids... ', end='')
    pool = mp.Pool(NCORE, initializer=query_resource_ids,
                   initargs=(in_q, out_q, hs, v, lock))

    # wait for all processes to finish
    while not in_q.empty():
        time.sleep(1)

    # dequeue out_q to prevent join from freezing
    res_ids = []
    cnt = 0
    while not out_q.empty():
        cnt += 1
        val = out_q.get()
        res_ids.append(val)
    pool.close()
    pool.join()
    return res_ids


def get_spam_resources(hs, reslist):
    """
    Invokes the spam resource search using MultiProcessing
    """

    NCORE = mp.cpu_count()
    in_q = mp.Queue()
    out_q = mp.Queue()
    v = Value('i', 0)
    lock = Lock()

    print('\n--> populating job queue...', end='')
    for res in reslist:
        in_q.put(res)
    # tell workers to exit
    for _ in range(NCORE):
        in_q.put(None)

    print('\n--> searching for spam resources')
    pool = mp.Pool(NCORE, initializer=check_resource_for_spam,
                   initargs=(in_q, out_q, hs, v, lock))

    # wait for all processes to finish
    while not in_q.empty():
        time.sleep(1)

    # dequeue out_q to prevent join from freezing
    spam = []
    while not out_q.empty():
        val = out_q.get()
        spam.append(val)
    pool.close()
    pool.join()
    return spam


def connect():
    """
    Create a connection to HS using the HS-API
    """

    tries = 0
    host = input('Enter host address (default www.hydroshare.org): ') or 'www.hydroshare.org'
    while 1:
        u = input('Enter HS username: ')
        p = getpass.getpass('Enter HS password: ')
        auth = hsapi.HydroShareAuthBasic(username=u, password=p)
        hs = hsapi.HydroShare(hostname=host, auth=auth)
        try:
            hs.getUserInfo()
            break
        except hsapi.exceptions.HydroShareHTTPException:
            print('Authentication failed, attempt %d' % (tries+1))
            tries += 1

        if tries >= 3:
            print('Number of attempts exceeded, exiting')
            sys.exit(1)
        print('')

    return hs


if __name__ == "__main__":

    # connect to hydroshare
    hs = connect()

    # get all available resources
    # note: this will be restricted by user accessibility
    res_ids = collect_resource_ids(hs)

    # check resources for spam
    spam = get_spam_resources(hs, res_ids)

    print('Possible spam resources: ')
    for item in spam:
        print('%s: %s' % (item[0], item[1]))

    print('done') 
