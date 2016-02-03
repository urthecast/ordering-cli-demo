import unittest
import sys
import os
import responses
from mock import patch

# Fixture data
UC_API_KEY = '123'
UC_API_SECRET = '456'
UC_API_HOST = 'https://api.urthecast.com/'
os.environ['UC_API_KEY'] = UC_API_KEY
os.environ['UC_API_SECRET'] = UC_API_SECRET
os.environ['UC_API_HOST'] = UC_API_HOST

# Silence all print statements to keep test output clean
class NullWriter:
    def write(self, s):
        pass
sys.stdout = NullWriter()

# Include the order.py file from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import order

class Test_error_and_quit(unittest.TestCase):
    # It should have a default sys.exit value of 1
    @patch('sys.exit')
    def test_default_exit_code(self, mock_sys_exit):
        order.error_and_quit('Testing errors! Everything is OK')
        mock_sys_exit.assert_called_with(1)

class Test_uc_make_request(unittest.TestCase):
    route = 'v1/archive/scenes'
    scene_url = UC_API_HOST + route

    # 401 - Unauthorized API request should throw an error
    @patch('sys.exit')
    @patch('order.api_request_error')
    @responses.activate
    def test_make_request_401(self, mock_api_request_error, mock_sys_exit):
        responses.add(responses.GET, self.scene_url,
            body='{"status": 401, "request_time": "2016-02-02T22:31:17Z", "messages": ["Unauthorized."], "meta": null, "request_id": "1ff887bb-8857-4906-a41c-b936715c5d84", "payload": null}',
            status=401,
            content_type='application/json')

        order.uc_make_request(self.route)
        assert mock_api_request_error.called

    # 500 - Internal server error API request should throw an error
    @patch('sys.exit')
    @patch('order.api_request_error')
    @responses.activate
    def test_make_request_500(self, mock_api_request_error, mock_sys_exit):
        responses.add(responses.GET, self.scene_url,
            body='{"status": 500, "request_time": "2016-01-30T20:45:03Z", "messages": ["Internal server error."], "meta": null, "request_id": "1ff887bb-8857-4906-a41c-b936715c5d84", "payload": null}',
            status=500,
            content_type='application/json')

        order.uc_make_request(self.route)
        assert mock_api_request_error.called

    # 200 - OK should not throw an error
    @patch('sys.exit')
    @patch('order.api_request_error')
    @responses.activate
    def test_make_request_200(self, mock_api_request_error, mock_sys_exit):
        responses.add(responses.GET, self.scene_url,
            body='{"status": 200, "request_time": "2016-02-02T22:35:09Z", "messages": [], "meta": { "total": 12345 }, "request_id": "abc2fb59-adb5-45b2-9ebc-be7b211b4bd9", "payload": []}',
            status=200,
            content_type='application/json')

        order.uc_make_request(self.route)
        assert mock_api_request_error.called == False

class Test_uc_make_post_request(unittest.TestCase):
    route = 'v1/ordering/orders'
    ordering_url = UC_API_HOST + route

    # 201 - Created should not throw an error
    @patch('sys.exit')
    @patch('order.api_request_error')
    @responses.activate
    def test_make_request_201(self, mock_api_request_error, mock_sys_exit):
        responses.add(responses.POST, self.ordering_url,
            body='{"status": 201, "request_time": "2016-02-02T22:35:09Z", "messages": [], "meta": null, "request_id": "abc2fb59-adb5-45b2-9ebc-be7b211b4bd9", "payload": []}',
            status=201,
            content_type='application/json')

        order.uc_make_post_request(self.route)
        assert mock_api_request_error.called == False


if __name__ == '__main__':
    unittest.main()
