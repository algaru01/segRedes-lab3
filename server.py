#!/usr/bin/env python3
import crypt
from uuid import uuid4

import json
import os

import threading
import time

from hmac import compare_digest as compare_hash 

from flask import make_response, request, send_from_directory

VERSION = "1.0"

HEADER_AUTHORIZATION = "Authorization"

PARAM_USERNAME = "username"
PARAM_PASSWORD = "password"
PARAM_DOC_CONTENT = "doc_content"

SHADOW_FILE = "shadow"

SHADOW_USER = 0
SHADOW_HASHED_PSWD = 1
SHADOW_SEPARATOR = ":"

g_dict_tokens = {}

def routeApp(app, root_directory):

    def invalidate_user_token(user):
        time.sleep(300)
        del g_dict_tokens[user]

    @app.route('/version', methods=['GET'])
    def get_version():      
        return make_response(f"Current version is {VERSION}", 200)

    @app.route('/signup', methods=['POST'])
    def signup():
        if not request.is_json:
            return make_response('Missing JSON', 400)

        if PARAM_USERNAME not in request.get_json():
            return make_response(f"Missing '{PARAM_USERNAME}' param.", 400)
        if PARAM_PASSWORD not in request.get_json():
            return make_response(f"Missing '{PARAM_PASSWORD}' param.", 400)

        user = request.get_json()[PARAM_USERNAME]
        pswd = request.get_json()[PARAM_PASSWORD]

        try:
            with open(SHADOW_FILE, "r") as f:
                for line in f:
                    if user == line.split(SHADOW_SEPARATOR)[SHADOW_USER].rstrip():
                        return make_response("Username in use.", 401)
        except FileNotFoundError:
            pass

        hashed_pswd =crypt.crypt(pswd, crypt.mksalt(crypt.METHOD_SHA512))
        with open(SHADOW_FILE, "a+") as f:
            f.write(f"{user}:{hashed_pswd}\n")

        os.makedirs(f"{root_directory}/{user}", exist_ok=True)

        token = str(uuid4())

        g_dict_tokens[user] = token
        threading.Thread(target=invalidate_user_token, args=(user,)).start()

        return {"access_token": token}

    @app.route('/login', methods=['POST'])
    def login():
        if not request.is_json:
            return make_response('Missing JSON', 400)

        if PARAM_USERNAME not in request.get_json():
            return make_response(f"Missing '{PARAM_USERNAME}' param.", 400)
        if PARAM_PASSWORD not in request.get_json():
            return make_response(f"Missing '{PARAM_PASSWORD}' param.", 400)

        user = request.get_json()[PARAM_USERNAME]
        pswd = request.get_json()[PARAM_PASSWORD]

        if user in g_dict_tokens:
            return make_response("User already logged in", 401)

        user_found = False
        try:
            with open(SHADOW_FILE, "r") as f:
                for line in f:
                    if user == line.split(SHADOW_SEPARATOR)[SHADOW_USER].rstrip():
                        hash = line.split(SHADOW_SEPARATOR)[SHADOW_HASHED_PSWD].rstrip()
                        if compare_hash(hash, crypt.crypt(pswd, hash)):
                            user_found = True
                            break
                        else:
                            return make_response("Incorrect password", 401)
        except FileNotFoundError:
            pass

        if not user_found:
            return make_response("User not found", 404)

        token = str(uuid4())

        g_dict_tokens[user] = token
        threading.Thread(target=invalidate_user_token, args=(user,)).start()

        return {"access_token": token}

    @app.route('/<username>/<doc_id>', methods=['POST'])
    def create_json(username, doc_id):
        if not request.is_json:
            return make_response('Missing JSON', 400)

        if HEADER_AUTHORIZATION not in request.headers:
            return make_response(f"Missing '{HEADER_AUTHORIZATION}' in header.", 400)
        if username not in g_dict_tokens.keys():
            return make_response("User is not logged in.", 401)
        if g_dict_tokens[username] != request.headers[HEADER_AUTHORIZATION]:
            return make_response("Invalid token", 401)

        if request.data is None:
            return make_response('Missing JSON file', 400)
        if PARAM_DOC_CONTENT not in request.data.decode():
            return make_response(f"Missing '{PARAM_DOC_CONTENT}' param", 400)
        if doc_id == "_all_docs":
            return make_response('Forbidden doc id.', 400)

        data = json.loads(request.data.decode())

        filepath = f'{root_directory}/{username}/{doc_id}.json'

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data[PARAM_DOC_CONTENT], f, ensure_ascii=False, indent=4)

        return {"size": os.stat(filepath).st_size}
        
    @app.route('/<username>/<doc_id>', methods=['GET'])
    def get_json(username, doc_id):
        if not request.is_json:
            return make_response('Missing JSON', 400)

        if username not in g_dict_tokens.keys():
            return make_response("Invalid token", 401)

        filepath = f'{root_directory}/{username}/{doc_id}.json'
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                doc = json.load(f)
        except FileNotFoundError:
            return make_response('JSON file not found', 404)

        return doc

    @app.route('/<username>/<doc_id>', methods=['PUT'])
    def update_json(username, doc_id):
        if not request.is_json:
            return make_response('Missing JSON.', 400)

        if HEADER_AUTHORIZATION not in request.headers:
            return make_response(f"Missing '{HEADER_AUTHORIZATION}' in header.", 400)
        if username not in g_dict_tokens.keys():
            return make_response("User is not logged in.", 401)
        if g_dict_tokens[username] != request.headers[HEADER_AUTHORIZATION]:
            return make_response("Invalid token.", 401)

        if request.data is None:
            return make_response('Missing JSON file.', 400)
        if PARAM_DOC_CONTENT not in request.data.decode():
            return make_response(f"Missing '{PARAM_DOC_CONTENT}' param", 400)
        if doc_id == "_all_docs":
            return make_response('Forbidden doc id.', 400)

        data = json.loads(request.data.decode())

        filepath = f'{root_directory}/{username}/{doc_id}.json'

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data[PARAM_DOC_CONTENT], f, ensure_ascii=False, indent=4)

        return {"size": os.stat(filepath).st_size}

    @app.route('/<username>/<doc_id>', methods=['DELETE'])
    def delete_json(username, doc_id):
        if not request.is_json:
            return make_response('Missing JSON', 400)

        if HEADER_AUTHORIZATION not in request.headers:
            return make_response(f"Missing '{HEADER_AUTHORIZATION}' in header.", 400)
        if username not in g_dict_tokens.keys():
            return make_response("User is not logged in.", 401)
        if g_dict_tokens[username] != request.headers[HEADER_AUTHORIZATION]:
            return make_response("Invalid token.", 401)

        filepath = f'{root_directory}/{username}/{doc_id}.json'
        try:
            os.remove(filepath)
        except FileNotFoundError:
            return make_response('JSON file not found', 404)

        return {}

    @app.route('/<username>/_all_docs', methods=['GET'])
    def get_all_jsons(username):
        if not request.is_json:
            return make_response('Missing JSON', 400)

        if HEADER_AUTHORIZATION not in request.headers:
            return make_response(f"Missing '{HEADER_AUTHORIZATION}' in header.", 400)
        if username not in g_dict_tokens.keys():
            return make_response("User is not logged in.", 401)
        if g_dict_tokens[username] != request.headers[HEADER_AUTHORIZATION]:
            return make_response("Invalid token.", 401)
        
        response = []
        try:
            for file in os.listdir(f'{root_directory}/{username}'):
                filepath = f'{root_directory}/{username}/{file}'
                with open(filepath, 'r', encoding='utf-8') as f:
                    response.append(json.load(f))
        except FileNotFoundError:
            return make_response('JSON files not found', 404)

        return response

