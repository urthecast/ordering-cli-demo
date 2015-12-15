# Urthecast Ordering CLI tool

## Disclaimer

This should be considered ALPHA code. This tool is designed for informational and demonstration purposes only. It should not be used in a production environment.

## Intro

This tool is designed to show how you can use the Urthecast Ordering API to purchase satellite imagery in GeoTIFF format.

## Setup

First, this tool requires the following environment variables to be present::

```
UC_API_KEY=123
UC_API_SECRET=456
```

Second, this tool requires Python 2.7 and the [Requests](http://docs.python-requests.org/) library. You may install this locally or globally using PIP.

## Usage

To purchase a GeoTIFF image, call the script as follows:

```
python order.py SCENE_ID
```

The script will proceed to:

1. Create a new order
2. Add the supplied scene ID as a line item to the order
3. Purchase the order
4. Poll the Delivery API until the download URL is present
5. Download the scene to disk

Errors will be printed to the console.