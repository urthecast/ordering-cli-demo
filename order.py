import requests
import os
import sys
import time
import wget
import json

# Try to get the key and secret from ENV
UC_API_KEY = os.environ.get('UC_API_KEY')
UC_API_SECRET = os.environ.get('UC_API_SECRET')
UC_API_HOST = os.getenv('UC_API_HOST', 'https://api.urthecast.com/')

# Valid dataset combinations
datasets = {
    'theia': ['red', 'green', 'blue', 'near-ir'],
    'landsat-8': ['red', 'green', 'blue', 'pan', 'near-ir', 'near-ir-2',
                  'short-wave-ir', 'short-wave-ir-2', 'long-wave-ir',
                  'long-wave-ir-2', 'coastal-blue'],
    'deimos-1': ['red', 'green', 'near-ir'],
    'deimos-2': ['red', 'green', 'blue', 'near-ir', 'pan'],
    'sentinel-2a': ['red', 'green', 'blue', 'near-ir', 'coastal-blue',
                    'short-wave-ir', 'short-wave-ir-2', 'short-wave-ir-3',
                    'red-edge', 'red-edge-2', 'red-edge-3', 'red-edge-4',
                    'water-vapour'],
}


def error_and_quit(message, exit_code=1):
    """ Generic error handling function """
    print "------"
    print "ERROR!"
    print "------"
    print message
    sys.exit(exit_code)


def uc_get_metadata(scene_id):
    """
    Try to get the metadata for the scene
    Throws an error and quits if the scene ID can't be found
    """
    response = uc_make_request('v1/archive/scenes', {'id': scene_id})
    resp = response.json()
    if resp['meta']['total'] == 0:
        error_and_quit("Scene ID " + scene_id + " could not be found.")
    return resp


def uc_create_order():
    """ Create a new Order """
    response = uc_make_post_request('v1/ordering/orders')
    resp = response.json()
    if response.status_code != 201:
        print response
        error_and_quit("Could not create Order. Do you have access to this API?")
    return resp


def uc_get_order(order_id):
    """ Get an Order """
    response = uc_make_request('v1/ordering/orders/' + order_id)
    return response.json()


def uc_create_line_item(order_id, scene_id, aoi_id=False):
    """ Create a new Line Item

    NOTE: For now, all datasets for a sensor are always included.
          You can always specify a custom subset of datasets manually.
    """
    line_item_url = 'v1/ordering/orders/' + order_id + '/line_items'
    body = {'type': 'scene',
            'metadata': {'scene_id': scene_id,
                         'datasets': datasets[scene_metadata['payload'][0]['sensor_platform']]
                         }
            }
    # If the user included an AOI ID, add it to the payload
    if (aoi_id):
        body['metadata']['geometry'] = aoi_id
    response = uc_make_post_request(line_item_url, body)
    return response.json()


def uc_purchase_order(order_id):
    """ Purchase an order """
    purchase_url = 'v1/ordering/purchase'
    body = {'order_id': order_id}
    response = uc_make_post_request(purchase_url, body)
    return response.json()


def uc_get_deliveries_for_order(order_id):
    """ Get all of the outstanding deliveries for the order """
    deliveries_url = 'v1/ordering/deliveries'
    response = uc_make_request(deliveries_url, {'order_id': order_id})
    return response.json()


def api_request_error(url, response):
    # If an error is received during API request, dump some helpful debug data
    error = '\n'.join(["The following API request failed:",
                       "---------------------------------",
                       url,
                       '',
                       '',
                       "The following response was received:",
                       "---------------------------------",
                       json.dumps(response.json()),
                       '',
                       '',
                       "Please contact platform@urthecast.com and reference request_id '",
                       "\t\t" + response.json()['request_id'],
                       "' with any questions or concerns."])
    error_and_quit(error)


def uc_make_request(route, user_params={}):
    """ Helper method to make UC API requests """
    default_params = {'api_key': UC_API_KEY,
                      'api_secret': UC_API_SECRET
                      }
    params = default_params.copy()
    params.update(user_params)
    url = UC_API_HOST + route
    r = requests.get(url, params=params)
    # If we got a 4xx or 5xx response, we need to generate an error
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        api_request_error(url, r)
    return r


def uc_make_post_request(route, body={}):
    """ Helper method to make POST UC API requests """
    default_params = {'api_key': UC_API_KEY,
                      'api_secret': UC_API_SECRET
                      }
    url = UC_API_HOST + route
    r = requests.post(url, params=default_params, json=body, headers={'Content-Type': 'application/json'})
    # If we got a 4xx or 5xx response, we need to generate an error
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        api_request_error(url, r)
    return r


def validate_arguments():
    """ Helper method to validate arugments passed to tool are valid """
    # Confirm we have key and secret before we go any farther
    if UC_API_KEY is None or UC_API_SECRET is None:
        message = '\n'.join(["Urthecast API key and secret required.",
                             "Please set the UC_API_KEY and UC_API_SECRET environment variables and try again."])
        error_and_quit(message)
    # Validate the command line arguments
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        message = '\n'.join(["Please call this script with the Scene ID you wish to purchase and download as a GeoTIFF.",
                             "Optionally, you may include an AOI ID which will crop the scene to that geometry."])
        error_and_quit(message)


if __name__ == '__main__':
    validate_arguments()

    # Save the scene ID we're going to be ordering and downloading
    scene_id = sys.argv[1]

    if len(sys.argv) == 3:
        aoi_id = sys.argv[2]
    else:
        aoi_id = False

    # First, let's confirm this scene exists and display some metadata:
    scene_metadata = uc_get_metadata(scene_id)
    print "Scene ID {0} found. Captured by {1} ({2} sensor platform)".format(scene_id,
                                                                             scene_metadata['payload'][0]['owner'],
                                                                             scene_metadata['payload'][0]['sensor_platform'])

    # Second, let's create a new order object
    order = uc_create_order()
    order_id = order['payload'][0]['id']
    print "Created a new order with ID " + order_id

    # Third, let's create a line item for the scene the user selected to the newly created order object
    line_item = uc_create_line_item(order_id, scene_id, aoi_id)
    print "Added line item for Scene ID {0} to Order ID {1} (estimated cost: {2})".format(scene_id,
                                                                                          order_id,
                                                                                          line_item['payload'][0]['estimated_cost'])

    if (aoi_id):
        print "Scene will be cropped according to the geometry specified in AOI ID " + aoi_id

    # Fourth, let's purchase the order!
    purchase = uc_purchase_order(order_id)
    print "Purchased order " + order_id + ". Order is now in state " + purchase['payload'][0]['state'] + "."

    # Fifth, let's poll for updates from this new order...
    print "Beginning to poll for order updates..."
    while(1):
        time.sleep(5)
        order = uc_get_order(order_id)

        if order['payload'][0]['state'] == 'processing':
            sys.stdout.write('.')
            sys.stdout.flush()
        else:
            print ""
            print "Order state is now " + order['payload'][0]['state']
            break

    # Sixth, and finally, get and download all of the Order Deliveries
    deliveries = uc_get_deliveries_for_order(order_id)
    for delivery in deliveries['payload']:
        print "Delivery " + delivery['id'] + "is now ready."
        print "URL for download: " + delivery['url']
        print "Automatically Downloading..."
        filename = wget.download(delivery['url'])
        print "Download now available at " + filename
