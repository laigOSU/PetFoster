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

#--------------------------------------------------#
# 1. /homes - POST, GET, DELETE, PUT
#--------------------------------------------------#
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

#--------------------------------------------------#
# 2. /homes/{hid} - GET, PUT, DELETE
#--------------------------------------------------#
@bp.route('/<hid>', methods=['GET','PUT','DELETE'])
def homes_put_delete_get(hid):
    # Check JWT: Missing/Invalid JWT --> 401
    jwt_param = request.args.get("jwt")
    if jwt_param is None:
        print("no params")
        return("Missing/Invalid JWT", 401)

    # Check JWT: Valid JWT --> Check if authorized user
    else:
        # Check if hid exists
        query = client.query(kind=constants.homes)
        first_key = client.key(constants.homes,int(hid))
        query.key_filter(first_key,'=')
        results = list(query.fetch())
        if len(results) == 0:
            return ("Page not found (this home uri does not exist)", 404)

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

        #---- PUT: MODIFY A SPECIFIC HOME ----#
                elif request.method == 'PUT':
                    content = request.get_json()
                    home_key = client.key(constants.homes, int(hid))
                    home = client.get(key=home_key)
                    # Can only edit family, address, phone properties
                    home.update({"family": content["family"], 'address': content['address'], 'phone': content['phone']})
                    client.put(home)
                    return ('',204)

        #---- DELETE: REMOVE A SPECIFIC HOME ----#
                elif request.method == 'DELETE':
                   # Check if home contains pets, if so, update each pet[foster] to null
                    if 'pets' in home.keys():
                        print("home[pets] is: ", home["pets"])
                        print("type of home[pets] is: ", type(home["pets"]))
                        for i in home["pets"]:
                            print("i is: ", i)
                            print("i[id] is: ", i["id"])
                            print("i[pet_url] is: ", i["pet_url"])
                            pet_id = i["id"]

                            # Get the pet id and the query that pet
                            pet_key = client.key(constants.pets, int(pet_id))
                            pet = client.get(key=pet_key)

                            print("before update pet[foster]")
                            print("pet[foster][id] was: ", pet["foster"]["id"])
                            print("pet[foster][family] was: ", pet["foster"]["family"])
                            print("pet[foster][home_url] was: ", pet["foster"]["home_url"])

                            # Update the pet's foster information
                            pet["foster"]["id"] = "null"
                            pet["foster"]["family"] = "null"
                            pet["foster"]["home_url"] = "null"
                            client.put(pet)

                            print("after update pet[foster]")
                            print("pet[foster][id] is now: ", pet["foster"]["id"])
                            print("pet[foster][family] is now: ", pet["foster"]["family"])
                            print("pet[foster][home_url] is now: ", pet["foster"]["home_url"])

                    # Actually delete the home
                    client.delete(home_key)
                    return ("", 204)

        #---- NOT A RECOGNIZED METHOD ----#
                else:
                    return ('Method not recognized', 405)

            # IF USER NOT AUTHORIZED, CANNOT DO ANY OF THE ABOVE METHODS
            else:
                return('Not authorized to access home owned by another', 403)


#--------------------------------------------------#
# 3. /homes/{hid}/pets/{pid} - PUT, DELETE
#--------------------------------------------------#
@bp.route('/<hid>/pets/<pid>', methods=['PUT','DELETE'])
def assign_remove_pet(hid,pid):

    # CHECK JWT HERE ----__________


    #---- PUT: ASSIGN A PET TO A HOME ----#
    if request.method == 'PUT':
        # Get client input
        content = request.get_json()

        # Get the home based on the hid
        home_key = client.key(constants.homes, int(hid))
        home = client.get(key=home_key)

        # Get the pet based on the pid
        pet_key = client.key(constants.pets, int(pid))
        pet = client.get(key=pet_key)

        # Set the pet_url
        pet_url = constants.appspot_url + constants.pets + "/" + str(pid)

        # Set the home_url
        home_url = constants.appspot_url + constants.homes + "/" + str(hid)

        # Declare the pet_json, to append to home["pets"]
        pet_json = {"id": pet.id, "pet_url": pet_url}
        # print("pet_json is: ", pet_json)
        # print("BEFORE: home is: ", home)
        # print("BEFORE: pet is: ", pet)

        # A. Check if pet not yet assigned to any home
        if pet["foster"]["family"] == "null":

            # 1. Update the home --> home[pet] = pid
            print("Pet not yet assigned to any home. So append (or add).")

            if 'pets' in home.keys():
                home['pets'].append(pet_json)
                print("Appending subsequent pet to this boat")
            else:
                home['pets'] = [pet_json]
                print("Adding first pet to this home.")

            client.put(home)

            # 2. Update the pet --> pet[foster] = hid
            pet["foster"]["id"] = home.key.id
            pet["foster"]["family"] = home["family"]
            pet["foster"]["home_url"] = home_url

            client.put(pet)
            # print("AFTER: home is: ", home)
            # print("AFTER: pet is: ", pet)
            return("Pet assigned to this home", 200)
        # B. Otherwise, pet already assigned somewhere, so 403 error.
        else:
            print("Pet already assigned to a home, cannot re-assign unless pet is removed from current foster.")
            return("Pet already assigned to a foster home.", 403)
        # return ("", 200)

    #---- DELETE: REMOVE A PET FROM A HOME ----#
    if request.method == 'DELETE':
        # Get the home based on the hid
        home_key = client.key(constants.homes, int(hid))
        home = client.get(key=home_key)

        # Get the pet based on the pid
        pet_key = client.key(constants.pets, int(pid))
        pet = client.get(key=pet_key)

        # Declare the pet_json to work with home[pets]
        pet_url = constants.appspot_url + constants.pets + "/" + str(pid)
        pet_json = {"id": pet.id, "pet_url": pet_url}
        print("pet_json is: ", pet_json)

        # print("BEFORE: home is: ", home)
        # print("BEFORE: pet is: ", pet)

        if 'pets' in home.keys():
            # 1. Update the home[pets] --> remove pid (pet_json)
            print("home[pets] is: ", home["pets"])

            home['pets'].remove(pet_json)
            client.put(home)

            # 2. Update the pet[foster] = null
            pet["foster"]["id"] = "null"
            pet["foster"]["family"] = "null"
            pet["foster"]["home_url"] = "null"

            client.put(pet)
        # print("AFTER: home is: ", home)
        # print("AFTER: pet is: ", pet)


        print("Pet #", pid, "removed from this home.")
        return("Pet removed", 200)

















###
