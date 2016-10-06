#!/usr/bin/env python
#
# Renders HAProxy map files for custom CNAMES
#
# Part of Auth0 October Hack-a-thon: provide CNAME support to customers
#
# Objectives:
# * [X] Setup test scaffolding
# * [ ] Test for validity of HAProxy Config
# * [ ] Call HTTP endpoint for certificate payload
# * [ ] Parse HTTP endpoint and render HAProxy CNAME -> tenant map
# * [ ] Parse HTTP endpoint and render HAProxy tenant -> region map
# * [ ] Create SSL files for each client

import requests
import os
import re
import pprint

# First Hammer
CNAME_MAP_FILE = os.getenv('A0_CNAME_MAP_FILE', "./test/maps/domain-to-tenant.map")
REGION_MAP_FILE = os.getenv('A0_CNAME_REGION_MAP_FILE', "./test/maps/domain-to-backend.map")
ENDPOINT = os.getenv('A0_CNAME_ENDPOINT', 'http://localhost:8080/db')
SSL_DIR = os.getenv('A0_CNAME_SSL_DIR', './test/ssl')
TOKEN = os.getenv('A0_CNAME_TOKEN', 'deadbeef')

def write_file(target, contents):
    file = open(target, "w")
    file.write(contents)
    file.close()

def write_haproxy_map(mappings, target):
    file = open(target, "w")
    for key, value in mappings:
        file.write("{} {}").format(key, walue)
    file.close()

def eu_region_regex():
    return ".*\.eu\.auth0\.com"

def au_region_regex():
    return ".*\.au\.auth0\.com"

def extract_region(mapping):
    backend = mapping['backend']

    if re.match(eu_region_regex(), backend) is not None:
        return { mapping['backend']: 'eu'}
    elif re.match(au_region_regex(), backend) is not None:
        return { mapping['backend']: 'au'}
    else:
        return { mapping['backend']: 'us'}

def extract_cname(mapping):
   return {mapping['cname']: mapping['backend']}

def get_cname_map(endpoint):
    return requests.get(endpoint).json()

def save_certificate(mapping, ssl_dir):
    cert, key = (mapping['cert'], mapping['key'])
    ssl_file = "{}/{}.pem".format(ssl_dir, mapping['cname'])
    ssl_file_content = "{}{}".format(cert, key)
    write_file(ssl_file, ssl_file_content)

def main():
    mappings = get_cname_map(ENDPOINT)

    cname_map = map(extract_cname, mappings)
    region_map = map(extract_region, mappings)
    # write_haproxy_map(cname_map, CNAME_MAP_FILE)
    # write_haproxy_map(region_map, REGION_MAP_FILE)

    for mapping in mappings:
        save_certificate(mapping, SSL_DIR)

main()
