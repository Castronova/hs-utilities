#!/usr/bin/env python3

import sys
sys.path.append('..')

import connect

from_res = 'de421a2414784acfb5fb417c272eced1'
#to_res = 'd2bab32e7c1d4d55b8cba7221e51b02d'
to_res = '6d5c7dbe0762413fbe6d7a39e4ba1986'

# establish a connection with hydroshare
hs = connect.connect(host='www.hydroshare.cuahsi.org', verify=False)
hs_prod = connect.connect()

# get the authorship from the 'from_res'
scimeta = hs.getScienceMetadata(from_res)
contributors = scimeta['contributors']

i = 0
for c in contributors:
    # remove the description field b/c it causes an error during update
    c.pop('description')

    print('%d.) %s ' % (i, c['name']))
    i += 1
    for k, v in c.items():
        if k != 'name':
            print('   %s: %s' % (k, v))


# set science metadata
print('  setting science metadata...', end='')
res = hs_prod.updateScienceMetadata(to_res, metadata={'contributors': contributors})
print('done')
