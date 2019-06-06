from flask import Blueprint, request
from google.cloud import datastore
import json
import constants

client = datastore.Client()

bp = Blueprint('cargo', __name__, url_prefix='/cargos')

@bp.route('/', methods=['POST','GET'])
def cargos_get_post():
    #---- POST: CREATE A NEW CARGO ----#
    if request.method == 'POST':
        content = request.get_json()
        new_cargo = datastore.entity.Entity(key=client.key(constants.cargos))
        new_cargo.update({"weight": content["weight"], 'content': content['content'], 'delivery_date': content['delivery_date']})
        client.put(new_cargo)
        cargo_id = str(new_cargo.key.id)
        url = constants.appspot_url + constants.cargos + "/" + cargo_id
        new_cargo["cargo_url"] = url
        client.put(new_cargo)
        new_cargo["carrier"] = {"id": "null", "name": "null", "boat_url": "null"}
        client.put(new_cargo)
        return (str(new_cargo.key.id), 201)

    #---- GET: VIEW ALL CARGOS ----#
    elif request.method == 'GET':
        query = client.query(kind=constants.cargos)
        q_limit = int(request.args.get('limit', '3'))
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
        output = {"cargos": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output)

    else:
        return 'Method not recognized'

@bp.route('/<id>', methods=['PUT','DELETE','GET'])
def cargo_put_delete_get(id):
    #---- PUT: MODIFY A SPECIFIC CARGO ----#
    if request.method == 'PUT':
        content = request.get_json()
        cargo_key = client.key(constants.cargos, int(id))
        cargo = client.get(key=cargo_key)
        cargo.update({"weight": content["weight"], 'content': content['content'], 'delivery_date': content['delivery_date']})
        client.put(cargo)
        return ('',200)

    #---- DELETE: ELIMINATE A SPECIFIC CARGO (NOT the same as unload)----#
    elif request.method == 'DELETE':
        # Get the cargo
        cargo_key = client.key(constants.cargos, int(id))
        cargo = client.get(key=cargo_key)

        # 1. Update boat, if any
        if cargo["carrier"]["name"] != "null":
            # Get the boat
            boat_id = cargo["carrier"]["id"]
            boat_key = client.key(constants.boats, int(boat_id))
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

    #---- GET: VIEW A SPECIFIC CARGO ----#
    elif request.method == 'GET':
        query = client.query(kind=constants.cargos)
        cargo_key = client.key(constants.cargos,int(id))
        query.key_filter(cargo_key,'=')
        results = list(query.fetch())
        for e in results:
            e["id"] = id


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
