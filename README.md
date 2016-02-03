# Urthecast Ordering CLI tool

## Disclaimer

This should be considered ALPHA code. This tool is designed for informational and demonstration purposes only.

## Intro

This tool is designed to show how you can use the Urthecast Ordering API to purchase satellite imagery in GeoTIFF format.

## Setup

First, this tool requires the following environment variables to be present:

```
UC_API_KEY=123
UC_API_SECRET=456
```

If you wish to use an environment besides production you may also set:

```
UC_API_HOST=
```

Secondly, this tool requires Python 2.7 and the [PIP](https://pip.pypa.io/en/stable/installing/) python package manager.

Once PIP is installed, run:

```
pip install -r requirements.txt
```

## Usage

To purchase a GeoTIFF image with all possible datasets, call the script as follows:

```
python order.py SCENE_ID
```

If you wish to crop a scene to an existing [Area of Interest](https://developers.urthecast.com/docs/aois), call the script as follows:

```
python order.py SCENE_ID AOI_ID
```

The script will proceed to:

1. Create a new order
2. Add the supplied scene ID as a line item to the order (includes all datasets/bands, optionally cropping to AOI_ID)
3. Purchase the order
4. Poll the Delivery API until the download URL is available
5. Download the scene to disk

For more information about the Urthecast Ordering API, please [read the docs](https://developers.urthecast.com/docs/orders).

Errors will be printed to the console.

## Running tests

If you wish to run the test suite:

```
python tests/order_tests.py
```
