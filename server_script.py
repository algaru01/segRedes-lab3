
from flask import Flask

import argparse

from server import routeApp
import os

import ssl

IP = "myserver.local"
PORT = "5000"

CERT_PATH = "cert/server.crt"
CERT_KEY_PATH = "cert/server.key"

def main():
    '''Entry point'''
    args = parse_args()
    root_directory = get_root_directory(args)

    app = Flask("database")
    app.config['SERVER_NAME'] = f'{IP}:{PORT}'
    routeApp(app, root_directory)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.load_cert_chain(CERT_PATH, CERT_KEY_PATH) #Location of certificate & key
    app.run(port=5000, ssl_context=context)

def parse_args():
    '''Argument Parser'''
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--root-directory", dest="root_directory", type=str, required=True, help="Root directory of database")

    return parser.parse_args()

def get_root_directory(args):
    '''Gets root directory for database'''
    root_directory = args.root_directory

    if os.path.isdir(root_directory):
        print(f"Root Directory: {root_directory}.")
        return root_directory 
    else:
        print("Error: Root Directory given does not exist.")
        exit(1)

if __name__ == '__main__':
    main()   