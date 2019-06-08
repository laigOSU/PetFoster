from flask import Blueprint, request, make_response
from flask import request
from google.cloud import datastore
from json2html import *
import json
import constants

from requests_oauthlib import OAuth2Session
from google.oauth2 import id_token
from google.auth import crypt
from google.auth import jwt
from google.auth.transport import requests
import jwt

client = datastore.Client()

bp = Blueprint('pet', __name__, url_prefix='/pets')

#--------------------------------------------------#
# 1. /pets - POST, GET, DELETE, PUT
#--------------------------------------------------#
@bp.route('', methods=['POST','GET', 'DELETE', 'PUT'])
def pets_get_post():
    #---- POST: CREATE A NEW PET ----#
    if request.method == 'POST':
        content = request.get_json()
        new_pet = datastore.entity.Entity(key=client.key(constants.pets))
        new_pet.update({"name": content["name"], 'species': content['species'], 'breed': content['breed']})
        client.put(new_pet)
        new_pet["foster"] = {"id": "null", "family": "null", "home_url": "null"}
        client.put(new_pet)
        return (str(new_pet.key.id), 201)

    #---- GET: VIEW ALL PETS ----#
    elif request.method == 'GET':
        query = client.query(kind=constants.pets)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        count = len(list(query.fetch()))
        print("count is: ", count)
        g_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = g_iterator.pages
        results = list(next(pages))
        if g_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
            e["pet_url"] = constants.appspot_url + constants.pets + "/" + str(e.key.id)
        collection_header = "Pet Collection Size is: " + str(count) + " total pets in collection"
        output = {collection_header: results}

        if next_url:
            output["next"] = next_url
        # return json.dumps(output)

        # If client's Accept header is set application/json:
        if 'application/json' in request.accept_mimetypes:
         # return json.dumps(results)
         res = make_response(json.dumps(output))
         res.mimetype = 'application/json'
         res.status_code = 200
         return res

        # Else, any other client Accept header is not acceptable format
        else:
          error_message = 'Not Acceptable: Must accept application/json only'
          res = make_response(error_message)
          res.status_code = 406
          return res

    #---- DELETE: DELETE ALL PETS (NOT ALLOWED) ----#
    elif request.method == 'DELETE':
        return ('Method not allowed', 405)

    #---- EDIT: EDIT ALL PETS (NOT ALLOWED) ----#
    elif request.method == 'PUT':
        return ('Method not allowed', 405)

    #---- UNRECOGNIZED METHODS ----#
    else:
        return ('Method not recognized', 405)


#--------------------------------------------------#
# 2. /pets/{pid} - GET, PUT, DELETE
#--------------------------------------------------#
@bp.route('/<pid>', methods=['PUT','DELETE','GET'])
def pet_put_delete_get(pid):
    #---- GET: VIEW A SPECIFIC PET ----#
    if request.method == 'GET':
        query = client.query(kind=constants.pets)
        pet_key = client.key(constants.pets,int(pid))
        query.key_filter(pet_key,'=')
        results = list(query.fetch())
        for e in results:
            e["id"] = pid
            e["pet_url"] = constants.appspot_url + constants.pets + "/" + pid
        # return json.dumps(results)

        # If client's Accept header is set application/json:
        if 'application/json' in request.accept_mimetypes:
            # return json.dumps(results)
            res = make_response(json.dumps(results))
            res.mimetype = 'application/json'
            res.status_code = 200
            return res

        # Else, any other client Accept header is not acceptable format
        else:
            error_message = 'Not Acceptable: Must accept application/json only'
            res = make_response(error_message)
            res.status_code = 406
            return res


    #---- PUT: MODIFY A SPECIFIC PET ----#
    elif request.method == 'PUT':
        content = request.get_json()
        pet_key = client.key(constants.pets, int(pid))
        pet = client.get(key=pet_key)
        # Can only edit name, species, breed properties
        pet.update({"name": content["name"], 'species': content['species'], 'breed': content['breed']})
        client.put(pet)
        return ('',204)

    #---- DELETE: REMOVE A SPECIFIC PET FROM THE SYSTEM (NOT the same as unassign from foster home)----#
    elif request.method == 'DELETE':
        # Get the pet
        pet_key = client.key(constants.pets, int(pid))
        pet = client.get(key=pet_key)

        # 1. Update home, if any
        if pet["foster"]["family"] != "null":
            # Get the home
            home_id = pet["foster"]["id"]
            home_key = client.key(constants.homes, int(home_id))
            home = client.get(key=home_key)
            print("home is: ", home)

            # Update home's pets array
            pet_url = constants.appspot_url + constants.pets + "/" + str(pid)
            pet_json = {"id": pet.id, "pet_url": pet_url}
            print("pet_json is: ", pet_json)
            print("pet.id is: ", pet.id)
            print("type of pet.id is: ", type(pet.id))
            print("pet.key.id is: ", pet.key.id)
            print("type of pet.key.id is: ", type(pet.key.id))

            # Remove the pet from home and save to the modified home to datastore
            home["pets"].remove(pet_json)
            client.put(home)

        # 2. Remove the pet entirely
        client.delete(pet_key)

        return ('',204)



    else:
        return 'Method not recognized'
