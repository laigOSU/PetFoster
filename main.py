from google.cloud import datastore
from flask import Flask, request
from requests_oauthlib import OAuth2Session
import json
from google.oauth2 import id_token
from google.auth import crypt
from google.auth import jwt
from google.auth.transport import requests
import jwt

import constants
import pet
import home
import user

# This disables the requirement to use HTTPS so that you can test locally.
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.register_blueprint(home.bp)
app.register_blueprint(pet.bp)
app.register_blueprint(user.bp)
client = datastore.Client()

# These should be copied from an OAuth2 Credential section at
# https://console.cloud.google.com/apis/credentials
# client_id = r'371537407612-8tjsld73srjlpagoemihudhcjhbk25b0.apps.googleusercontent.com'
# client_secret = r'xUfAYR1s1KwVQL5-c-NYw7mE'

# This is the page that you will use to decode and collect the info from
# the Google authentication flow
# redirect_uri = 'http://127.0.0.1:8080/oauth'
redirect_uri = 'https://laig493.appspot.com/oauth'

# These let us get basic info to identify a user and not much else
# they are part of the Google People API
scope = ['https://www.googleapis.com/auth/userinfo.email',
             'https://www.googleapis.com/auth/userinfo.profile']
oauth = OAuth2Session(constants.client_id, redirect_uri=redirect_uri,
                          scope=scope)

# This link will redirect users to begin the OAuth flow with Google
@app.route('/')
def index():
    authorization_url, state = oauth.authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
        # access_type and prompt are Google specific extra
        # parameters.
        access_type="offline", prompt="select_account")
    return 'Please go <a href=%s>here</a> and authorize access.' % authorization_url

# This is where users will be redirected back to and where you can collect
# the JWT for use in future requests
@app.route('/oauth')
def oauthroute():
    token = oauth.fetch_token(
        'https://accounts.google.com/o/oauth2/token',
        authorization_response=request.url,
        client_secret=constants.client_secret)
    req = requests.Request()

    id_info = id_token.verify_oauth2_token(
    token['id_token'], req, constants.client_id)

    return "Your JWT is: %s" % token['id_token']

# This page demonstrates verifying a JWT. id_info['email'] contains
# the user's email address and can be used to identify them
# this is the code that could prefix any API call that needs to be
# tied to a specific user by checking that the email in the verified
# JWT matches the email associated to the resource being accessed.
@app.route('/verify-jwt')
def verify():
    req = requests.Request()

    id_info = id_token.verify_oauth2_token(
    request.args['jwt'], req, constants.client_id)

    return repr(id_info) + "<br><br> the user is: " + id_info['email']

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
