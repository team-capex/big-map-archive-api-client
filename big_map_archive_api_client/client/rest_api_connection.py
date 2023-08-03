import requests

class RestAPIConnection:
    """Internal auxiliary class that handles the base connection."""

    def __init__(self, domain_name, port, token):
        """
        Initializes internal fields
        """
        self._base_url = f'https://{domain_name}:{port}'
        self._token = token

    def get(self, resource_path):
        """
        Sends a GET request and returns a response
        """
        url = self._base_url + resource_path

        kwargs = {}

        request_headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json',
            'Authorization': f'Bearer {self._token}'
        }
        kwargs['headers'] = request_headers
        kwargs['verify'] = True

        response = requests.get(url, **kwargs)
        return response

    def post(self, resource_path, payload=None):
        """
        Sends a POST request and returns a response
        """
        url = self._base_url + resource_path

        kwargs = {}

        if payload is not None:
            kwargs['data'] = payload

        request_headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json',
            'Authorization': f'Bearer {self._token}'
        }
        kwargs['headers'] = request_headers
        kwargs['verify'] = True

        response = requests.post(url, **kwargs)
        return response

    def put(self, resource_path, payload=None, content_type='application/json'):
        """
        Sends a PUT request and returns a response
        """
        url = self._base_url + resource_path

        kwargs = {}

        if payload is not None:
            kwargs['data'] = payload

        request_headers = {
            'Accept': 'application/json',
            'Content-type': f'{content_type}',
            'Authorization': f'Bearer {self._token}'
        }
        kwargs['headers'] = request_headers
        kwargs['verify'] = True

        response = requests.put(url, **kwargs)
        return response