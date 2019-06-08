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

bp = Blueprint('home', __name__, url_prefix='/homes')

@bp.route('', methods=['POST','GET', 'DELETE', 'PUT'])
def homes_get_post():
    #---- POST: CREATE A NEW HOME ----#
    if request.method == 'POST':
        # Check JWT: Missing/Invalid JWT --> 401
        jwt_param = request.args.get("jwt")
        if jwt_param is None:
            print("no params")
            return("Missing/Invalid JWT", 401)

        # Check JWT: Valid JWT --> proceed to POST
        else:
            print("yes params")
            # Get the JWT info
            req = requests.Request()
            id_info = id_token.verify_oauth2_token(
            request.args['jwt'], req, constants.client_id)
            print("req is: ", req)
            print("User's email is: id_info[email] = ", id_info['email'])

            # Make a new home
            content = request.get_json()
            new_home = datastore.entity.Entity(key=client.key(constants.homes))
            new_home.update({"family": content["family"], 'address': content['address'], 'phone': content['phone'], 'owner': id_info['email']})
            client.put(new_home)

            # Check if user['email'] already exists
            query = client.query(kind=constants.users)
            query.add_filter('email', '=', id_info['email'])
            queryresults = list(query.fetch())
            if (queryresults):
                print("Email exists in user DB")

            # If user doesn't already exist, create new user entity
            else:
                print("Email does not yet exist in user DB")
                new_user = datastore.entity.Entity(key=client.key(constants.users))
                new_user.update({"email": id_info['email']})
                client.put(new_user)

            # Return 201 and new home's ID
            return (str(new_home.key.id), 201)


    #---- GET: VIEW ALL HOMES ----#
    elif request.method == 'GET':
        query = client.query(kind=constants.homes)
        print("query is: ", query)
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
            e["home_url"] = constants.appspot_url + constants.homes + "/" + str(e.key.id)
        collection_header = "Home Collection Size is: " + str(count) + " total homes in collection"
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


    #---- DELETE: DELETE ALL HOMES (NOT ALLOWED) ----#
    elif request.method == 'DELETE':
        return ('Method not allowed', 405)

    #---- EDIT: EDIT ALL HOMES (NOT ALLOWED) ----#
    elif request.method == 'PUT':
        return ('Method not allowed', 405)

    else:
        return ('Method not recognized', 405)

@bp.route('/<hid>', methods=['PUT','DELETE','GET'])
def homes_put_delete_get(hid):
    # Check JWT: Missing/Invalid JWT --> 401
    jwt_param = request.args.get("jwt")
    if jwt_param is None:
        print("no params")
        return("Missing/Invalid JWT", 401)

    # Check JWT: Valid JWT --> Check if authorized user
    else:
        # Get the home to check the correct user
        home_key = client.key(constants.homes, int(hid))
        home = client.get(key=home_key)

        # Get the home's owner
        home_owner = home['owner']
        print("home_owner is: ", home_owner)

        # Confirm user is authorized to access
        req = requests.Request()

        id_info = id_token.verify_oauth2_token(
        request.args['jwt'], req, constants.client_id)

        # IF USER AUTHORIZED, CAN DO GET, PUT, DELETE METHODS
        if(id_info['email'] == home_owner):

    #---- GET: VIEW A SPECIFIC HOME ----#
            if request.method == 'GET':
                query = client.query(kind=constants.homes)
                first_key = client.key(constants.homes,int(hid))
                query.key_filter(first_key,'=')
                results = list(query.fetch())
                for e in results:
                    e["id"] = hid
                    url = constants.appspot_url + constants.homes + "/" + hid
                    e["home_url"] = url
                return json.dumps(results)

    #---- PUT: MODIFY A SPECIFIC HOME ----#
            elif request.method == 'PUT':
                content = request.get_json()
                home_key = client.key(constants.homes, int(hid))
                home = client.get(key=home_key)
                # Can only edit family, address, phone properties
                home.update({"family": content["family"], 'address': content['address'], 'phone': content['phone']})
                client.put(home)
                return ('',200)

    #---- DELETE: REMOVE A SPECIFIC HOME ----#
            elif request.method == 'DELETE':
               # Check if home contains pets, if so, update each pet[foster] to null
                if 'pets' in boat.keys():
                    print("home[pets] is: ", home["pets"])
                    print("type of home[pets] is: ", type(home["pets"]))
                    for i in home["cargo"]:
                        print("i is: ", i)
                        print("i[id] is: ", i["id"])
                        print("i[cargo_url] is: ", i["cargo_url"])
                        cargo_id = i["id"]
                        cargo_key = client.key(constants.cargos, int(cargo_id))
                        cargo = client.get(key=cargo_key)
                        print("before update cargo[carrier]")
                        print("cargo[carrier][id] was: ", cargo["carrier"]["id"])
                        print("cargo[carrier][name] was: ", cargo["carrier"]["name"])
                        print("cargo[carrier][boat_url] was: ", cargo["carrier"]["home_url"])

                        cargo["carrier"]["id"] = "null"
                        cargo["carrier"]["name"] = "null"
                        cargo["carrier"]["boat_url"] = "null"
                        client.put(cargo)
                        print("cargo[carrier][id] is now: ", cargo["carrier"]["id"])
                        print("cargo[carrier][name] is now: ", cargo["carrier"]["name"])
                        print("cargo[carrier][home_url] is now: ", cargo["carrier"]["home_url"])

                # Actually delete the home <-- UNCOMMENT THIS AFTER DEBUG
                # client.delete(home_key)   <-- UNCOMMENT THIS AFTER DEBUG


    #---- NOT A RECOGNIZED METHOD ----#
            else:
                return ('Method not recognized', 405)

        # IF USER NOT AUTHORIZED, CANNOT DO ANY OF THE ABOVE METHODS
        else:
            return('Not authorized to access home owned by another', 403)
