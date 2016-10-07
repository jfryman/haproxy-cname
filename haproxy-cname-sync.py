#!/usr/bin/env python
#
# Renders HAProxy map files for custom CNAMES
#
# Part of Auth0 October Hack-a-thon: provide CNAME support to customers
#

import requests
import os
import re
import time
import pprint

# First Hammer
ACME_ROOT_DIR = os.getenv('CNAMER_ACME_ROOT_DIR', '/etc/haproxy')
CNAME_MAP_FILE = os.getenv('CNAMER_MAP_FILE')
REGION_MAP_FILE = os.getenv('CNAMER_REGION_MAP_FILE')
ENDPOINT = os.getenv('CNAMER_ENDPOINT')
SSL_DIR = os.getenv('CNAMER_SSL_DIR')
TOKEN = os.getenv('CNAMER_TOKEN')
ENV = os.getenv('ENV', 'dev')
MAX_HTTP_RETRIES=10

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=MAX_HTTP_RETRIES)
session.mount('http://', adapter)
session.mount('https://', adapter)

def write_file(target, contents):
    """
    Generic file writer
    """

    # Ensure directory exists
    file_dirname = os.path.dirname(target)
    if not os.path.exists(file_dirname):
        os.makedirs(file_dirname)

    file = open(target, "w")
    print(target)
    file.write(contents)
    file.close()

def write_haproxy_map(mappings, target):
    """
    Generic HAProxy Map file generator
    """
    file = open(target, "w")
    for mapping in mappings:
        for key, value in mapping.items():
            entry = " ".join([key, value]) + '\n'
            file.write(entry)
    file.close()

def eu_region_regex():
    return ".*\.eu\.auth0\.com"

def au_region_regex():
    return ".*\.au\.auth0\.com"

def extract_region(mapping):
    backend = mapping['backend']

    if re.match(eu_region_regex(), backend) is not None:
        return { mapping['backend']: 'eu-{}'.format(ENV) }
    elif re.match(au_region_regex(), backend) is not None:
        return { mapping['backend']: 'au-{}'.format(ENV) }
    else:
        return { mapping['backend']: 'us-{}'.format(ENV) }

def extract_cname(mapping):
    """
    Lambda function to extract CNAME -> Tenant Mapping
    """
    return {mapping['cname']: mapping['backend']}

def get_endpoint(endpoint, max_tries=MAX_HTTP_RETRIES):
    """
    Attempts to retrieve HTTP endpoint, using token-based auth.
    Retries on failure up to `max_tries`
    """

    headers = {"Authorization": "Bearer {}".format(TOKEN)}

    remaining_tries = max_tries
    while remaining_tries > 0:
        try:
            return session.get(endpoint, headers=headers).json()
        except:
            time.sleep(1)

        remaining_tries = remaining_tries - 1

    raise Exception("Unable to get data")

def save_acme_challenge_token(challenge, token_dir):
    """
    Writes ACME challenge token to filesystem

    Expects payload:
    {
        "path": "/.well-known/acme-challenge/_somerandomkey",
        "data": "deadbeef"
    }
    """
    filename = token_dir + challenge['path']
    token = challenge['data']

    write_file(filename, token)

def save_certificate(mapping, ssl_dir):
    """
    Writes SSL Certificate to filesystem

    Expects payload:
    {
        "cert": "-----BEGIN CERTIFICATE------..."
        "key": "-----BEGIN PRIVATE KEY-----..."
    }
    """
    cert, key = (mapping['cert'], mapping['key'])
    filename = mapping['cname'] + ".pem"

    ssl_file = "/".join([ssl_dir, filename])
    ssl_file_content = "".join([cert, key])
    write_file(ssl_file, ssl_file_content)

def cname_preflight():
    if not os.path.exists(directory):
        os.makedirs(directory)

def main():
    """
    Main entry point for Python Application
    """
    mappings = get_endpoint(ENDPOINT)

    cname_map = [extract_cname(m) for m in mappings]
    region_map = [extract_region(m) for m in mappings]

    write_haproxy_map(cname_map, CNAME_MAP_FILE)
    write_haproxy_map(region_map, REGION_MAP_FILE)

    for mapping in mappings:
        if 'letsencrypt' in mapping:
            save_acme_challenge_token(mapping['letsencrypt'], ACME_ROOT_DIR)
        elif 'cert' in mapping:
            save_certificate(mapping, SSL_DIR)

main()
