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
        output = {"homes": results}

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

@bp.route('/<id>', methods=['PUT','DELETE','GET'])
def homes_put_delete_get(id):
    #---- PUT: MODIFY A SPECIFIC HOME ----#
    if request.method == 'PUT':
        content = request.get_json()
        home_key = client.key(constants.homes, int(id))
        home = client.get(key=home_key)
        home.update({"name": content["name"], 'type': content['type'], 'length': content['length']})
        client.put(home)
        return ('',200)

    #---- DELETE: REMOVE A SPECIFIC HOME ----#
    elif request.method == 'DELETE':
        # Check if JWT missing/invalid
        jwt_param = request.args.get("jwt")

        if jwt_param is None:
            print("no params")
            return("Missing/Invalid JWT", 401)

        else:
            # Get the home
            home_key = client.key(constants.homes, int(id))
            home = client.get(key=home_key)

            # Get the home's owner
            home_owner = home['owner']
            print("home_owner is: ", home_owner)


            # Confirm user is authorized to delete
            req = requests.Request()

            id_info = id_token.verify_oauth2_token(
            request.args['jwt'], req, constants.client_id)
            if(id_info['email'] == home_owner):

                # Check if home is docked in a slip --> if home_id == slip["current_home"]
                # Get that slip
                query = client.query(kind=constants.slips)
                query.add_filter('current_home', '=', id)
                queryresults = list(query.fetch())
                print("queryresults is: ", queryresults)
                for e in queryresults:
                    print("number is: ", e["number"])
                    print("current_home is: ", e["current_home"])
                    print("slip id is: ", e.key.id)
                    slip_id = e.key.id

                    slip_key = client.key(constants.slips, slip_id)
                    slip = client.get(key=slip_key)
                    slip["current_home"] = "null"
                    slip["arrival_date"] = "null"
                    client.put(slip)
                client.delete(home_key)

                return ('Deleted',204)
            else:
                return('Not authorized to delete home owned by another', 403)

    #---- GET: VIEW A SPECIFIC HOME ----#
    elif request.method == 'GET':
        query = client.query(kind=constants.homes)
        first_key = client.key(constants.homes,int(id))
        query.key_filter(first_key,'=')
        results = list(query.fetch())
        for e in results:
            e["id"] = id
            # url = "http://localhost:8080/homes/" + id
            url = constants.appspot_url + constants.homes + "/" + id
            e["home_url"] =url
        return json.dumps(results)


    else:
        return 'Method not recognized'
