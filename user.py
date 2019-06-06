from flask import Blueprint, request
from google.cloud import datastore
import json
import constants

from requests_oauthlib import OAuth2Session
from google.oauth2 import id_token
from google.auth import crypt
from google.auth import jwt
from google.auth.transport import requests
import jwt

client = datastore.Client()

bp = Blueprint('user', __name__, url_prefix='/users')

@bp.route('', methods=['GET'])
def users_get_post():
#---- GET: VIEW ALL USERS ----#
    query = client.query(kind=constants.users)
    results = list(query.fetch())
    for e in results:
        e["id"] = e.key.id
        url = constants.appspot_url + constants.users + "/" + str(e.key.id)
        e["user_url"] =url
    return json.dumps(results)

@bp.route('/<uid>/homes', methods=['GET'])
def get_users_boats(uid):
    # Check JWT params
    jwt_param = request.args.get("jwt")
    if jwt_param is None:
        print("no params")
        return("Missing/Invalid JWT", 401)
    else:
        print("yes params")

        # Get the JWT info
        req = requests.Request()
        id_info = id_token.verify_oauth2_token(
        request.args['jwt'], req, constants.client_id)
        print("req is: ", req)
        print("User's email is: id_info[email] = ", id_info['email'])
        jwt_email = id_info['email']
        print("jwt_email is: ", jwt_email)

        # Get the DB info on user of that user id (uid)
        user_key = client.key(constants.users, int(uid))
        my_user = client.get(key=user_key)
        db_email = my_user['email']
        print("db_email is: ", db_email)

        # Compare JWT email vs DB email matches
        if (db_email == jwt_email):
            print("Emails match, correct user")
            query = client.query(kind=constants.boats)
            query.add_filter('owner', '=', jwt_email)
            queryresults = list(query.fetch())
            print ("queryresults are: ", queryresults)
            print("jsondumped query results are: ", json.dumps(queryresults))

            return(json.dumps(queryresults))
        else:
            return("Not authorized to view boats of another user", 403)
