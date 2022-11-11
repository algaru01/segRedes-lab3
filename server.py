#!/usr/bin/env python3
import crypt
from uuid import uuid4

import json
import os

from hmac import compare_digest as compare_hash 

from flask import make_response, request, send_from_directory

g_dict_tokens = {}

def routeApp(app):

    @app.route('/signup', methods=['POST'])
    def signup():
        if not request.is_json:
            return make_response('Missing JSON', 400)

        if "username" not in request.get_json():
            return make_response("Missing 'username' param.", 400)
        if "password" not in request.get_json():
            return make_response("Missing 'password' param.", 400)

        user = request.get_json()["username"]
        pswd = request.get_json()["password"]

        hashed_pswd =crypt.crypt(pswd, crypt.mksalt(crypt.METHOD_SHA512))

        with open("shadow", "a") as f:
            f.write(f"{user}:{hashed_pswd}\n")
            f.close()

        token = uuid4()

        g_dict_tokens[user] = token

        return {"access_token": str(token)}

    @app.route('/login', methods=['POST'])
    def login():
        if not request.is_json:
            return make_response('Missing JSON', 400)

        if "username" not in request.get_json():
            return make_response("Missing 'username' param.", 400)
        if "password" not in request.get_json():
            return make_response("Missing 'password' param.", 400)

        user = request.get_json()["username"]
        pswd = request.get_json()["password"]

        with open("shadow", "r") as f:
            user_found = False
            for line in f:
                if line.find(user) != -1:
                    hash = line.split(":")[1].rstrip()
                    if compare_hash(hash, crypt.crypt(pswd, hash)):
                        user_found = True
                        break
                    else:
                        return make_response("Incorrect password", 401)
            f.close()
            if not user_found:
                return make_response("User not found", 404)

        token = uuid4()

        g_dict_tokens[user] = token

        return {"access_token": str(token)}

    @app.route('/<username>/<doc_id>', methods=['POST'])
    def create_json(username, doc_id):
        if username not in g_dict_tokens.keys():
            return make_response("Invalid token", 401)

        if not request.is_json:
            return make_response('Missing JSON', 400)

        #POn aqui que es el nombre del argumento
        if request.data is None:
            return make_response('Missing JSON file', 400)

        data = json.loads(request.data.decode())

        filepath = f'{username}/{doc_id}.json'

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return {"size": os.stat(filepath).st_size}
        
    @app.route('/<username>/<doc_id>', methods=['GET'])
    def get_json(username, doc_id):
        if username not in g_dict_tokens.keys():
            return make_response("Invalid token", 401)

        if not request.is_json:
            return make_response('Missing JSON', 400)

        if request.data is None:
            return make_response('Missing JSON file', 400)

        filepath = f'{username}/{doc_id}.json'
        with open(filepath, 'r', encoding='utf-8') as f:
            doc = json.load(f)

        return doc

    @app.route('/<username>/<doc_id>', methods=['PUT'])
    def update_json(username, doc_id):
        if username not in g_dict_tokens.keys():
            return make_response("Invalid token", 401)

        if not request.is_json:
            return make_response('Missing JSON', 400)

        if request.data is None:
            return make_response('Missing JSON file', 400)

        data = json.loads(request.data.decode())

        filepath = f'{username}/{doc_id}.json'

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return {"size": os.stat(filepath).st_size}

    @app.route('/<username>/<doc_id>', methods=['DELETE'])
    def delete_json(username, doc_id):
        if username not in g_dict_tokens.keys():
            return make_response("Invalid token", 401)

        if not request.is_json:
            return make_response('Missing JSON', 400)

        if request.data is None:
            return make_response('Missing JSON file', 400)

        filepath = f'{username}/{username}/{doc_id}.json'
        try:
            os.remove(filepath)
        except FileNotFoundError:
            return make_response('JSON file not found', 404)

        return {}

    @app.route('/<username>/_all_docs', methods=['GET'])
    def get_all_jsons(username):
        if username not in g_dict_tokens.keys():
            return make_response("Invalid token", 401)

        if not request.is_json:
            return make_response('Missing JSON', 400)

        if request.data is None:
            return make_response('Missing JSON file', 400)

        response = {}
        
        for file in os.listdir(f'./{username}'):
            filepath = f'{username}/{username}/{doc_id}.json'


