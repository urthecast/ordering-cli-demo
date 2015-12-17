import requests
import os
import sys
import time
import wget

# Try to get the key and secret from ENV
UC_API_KEY = os.environ.get('UC_API_KEY')
UC_API_SECRET = os.environ.get('UC_API_SECRET')
UC_API_HOST = os.getenv('UC_API_HOST', 'https://api.urthecast.com/')

# Valid dataset combinations
datasets = {
    'theia': ['red', 'green', 'blue', 'near-ir'],
    'landsat-8': ['red', 'green', 'blue', 'pan', 'near-ir', 'near-ir-2',
                  'short-wave-ir', 'short-wave-ir-2', 'long-wave-ir',
                  'long-wave-ir-2'],
    'deimos-1': ['red', 'green', 'near-ir']
}

# Generic error handling function
def error_and_quit(message, exit_code = 1):
    print "------"
    print "ERROR!"
    print "------"
    print message
    sys.exit(exit_code)

# Try to get the metadata for the scene
# Throws an error and quits if the scene ID can't be found
def uc_get_metadata(scene_id):
    response = uc_make_request('v1/archive/scenes', { 'id': scene_id })
    resp = response.json()
    if resp['meta']['total'] == 0:
        error_and_quit("Scene ID " + scene_id + " could not be found.")
    return resp

# Create a new Order
def uc_create_order():
    response = uc_make_post_request('v1/ordering/orders')
    resp = response.json()
    if response.status_code != 201:
        print response
        error_and_quit("Could not create Order. Do you have access to this API?")
    return resp

# Get an Order
def uc_get_order(order_id):
    response = uc_make_request('v1/ordering/orders/' + order_id)
    return response.json()

# Create a new Line Item
def uc_create_line_item(order_id, scene_id, aoi_id = False):
    # NOTE: For now, all datasets for a sensor are always included.
    #       You can always specify a custom subset of datasets manually.
    line_item_url = 'v1/ordering/orders/' + order_id + '/line_items'

    body = {
        'type': 'scene',
        'metadata': {
            'scene_id': scene_id,
            'datasets': ','.join(datasets[scene_metadata['payload'][0]['sensor_platform']])
        }
    }

    # If the user included an AOI ID, add it to the payload
    if (aoi_id):
        body['metadata']['geometry'] = aoi_id

    response = uc_make_post_request(line_item_url, body)
    return response.json()

# Purchase an order
def uc_purchase_order(order_id):
    purchase_url = 'v1/ordering/purchase'

    body = {
        'order_id': order_id
    }

    response = uc_make_post_request(purchase_url, body)
    return response.json()

# Get all of the outstanding deliveries for the order
def uc_get_deliveries_for_order(order_id):
    deliveries_url = 'v1/ordering/deliveries'
    response = uc_make_request(deliveries_url, { 'order_id': order_id })
    return response.json()

# Helper method to make UC API requests
def uc_make_request(route, user_params = {}):
    default_params = {
        'api_key': UC_API_KEY,
        'api_secret': UC_API_SECRET
    }

    params = default_params.copy()
    params.update(user_params)

    url = UC_API_HOST + route

    r = requests.get(url, params=params)
    return r

# Helper method to make POST UC API requests
def uc_make_post_request(route, body = {}):
    default_params = {
        'api_key': UC_API_KEY,
        'api_secret': UC_API_SECRET
    }

    url = UC_API_HOST + route

    r = requests.post(url, params=default_params, json=body, headers={'Content-Type': 'application/json'})
    return r

# Confirm we have key and secret before we go any farther
if UC_API_KEY == None or UC_API_SECRET == None:
    error_and_quit("Urthecast API key and secret required.\nPlease set the UC_API_KEY and UC_API_SECRET environment variables and try again.")

# Validate the command line arguments
if len(sys.argv) != 2 and len(sys.argv) != 3:
    error_and_quit("Please call this script with the Scene ID you wish to purchase and download as a GeoTIFF. Optionally, you may include an AOI ID which will crop the scene to that geometry.")

# Save the scene ID we're going to be ordering and downloading
scene_id = sys.argv[1]

if len(sys.argv) == 3:
    aoi_id = sys.argv[2]
else:
    aoi_id = False

# First, let's confirm this scene exists and display some metadata:
scene_metadata = uc_get_metadata(scene_id)
print "Scene ID " + scene_id + " found. Captured by " + scene_metadata['payload'][0]['owner'] + " (" + scene_metadata['payload'][0]['sensor_platform'] + " sensor platform)"

# Second, let's create a new order object
order = uc_create_order()
order_id = order['payload'][0]['id']
print "Created a new order with ID " + order_id

# Third, let's create a line item for the scene the user selected to the newly created order object
line_item = uc_create_line_item(order_id, scene_id, aoi_id)
print "Added line item for Scene ID " + scene_id + " to Order ID " + order_id + " (estimated cost: " + str(line_item['payload'][0]['estimated_cost']) + ")"

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
