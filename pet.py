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
        new_pet["carrier"] = {"id": "null", "family": "null", "home_url": "null"}
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

    #---- DELETE: ELIMINATE A SPECIFIC CARGO (NOT the same as unload)----#
    elif request.method == 'DELETE':
        # Get the cargo
        cargo_key = client.key(constants.cargos, int(pid))
        cargo = client.get(key=cargo_key)

        # 1. Update boat, if any
        if cargo["carrier"]["name"] != "null":
            # Get the boat
            boat_pid = cargo["carrier"]["pid"]
            boat_key = client.key(constants.boats, int(boat_pid))
            boat = client.get(key=boat_key)
            print("boat is: ", boat)

            # Update boat's cargo array
            cargo_json = {"id": cargo.id, "cargo_url": cargo["cargo_url"]}
            print("cargo.id is: ", cargo.id)
            print("type of cargo.id is: ", type(cargo.id))
            print("cargo.key.id is: ", cargo.key.id)
            print("type of cargo.key.id is: ", type(cargo.key.id))

            boat["cargo"].remove(cargo_json)
            client.put(boat)

        # 2. Remove the cargo entirely
        client.delete(cargo_key)

        return ('',200)




        # The below is for debugging --------
        cargo_key = client.key(constants.cargos, int(id))
        cargo = client.get(key=cargo_key)
        # print("cargo[carrier]: ", cargo["carrier"])
        # print("cargo[carrier][name]: ", cargo["carrier"]["name"])
        # print("cargo[carrier][id]: ", cargo["carrier"]["id"])
        # print("cargo[carrier][boat_url]: ", cargo["carrier"]["boat_url"])
        # print("cargo is", cargo)
        # The above is for debugging --------

        return json.dumps(results)


    else:
        return 'Method not recognized'
