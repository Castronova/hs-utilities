#!/usr/bin/env python3

import os
import hs_restclient
from lxml import etree 
#import xml.etree.ElementTree as et

bagdir = 'data/de421a2414784acfb5fb417c272eced1'
resmeta = os.path.join(bagdir, 'data/resourcemetadata.xml')
resmap = os.path.join(bagdir, 'data/resourcemap.xml')


# read resource metadata

tree = etree.parse(resmeta)
root = tree.getroot()
ns = root.nsmap
#root = etree.Element("root")
#tree = et.parse(resmeta)
#root = et.getroot()


import pdb; pdb.set_trace()
