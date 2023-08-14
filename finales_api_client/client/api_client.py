import json
import os
from datetime import date

from big_map_archive_api_client.client.rest_api_connection import RestAPIConnection
from big_map_archive_api_client.utils import (generate_full_metadata,
                                              change_metadata,
                                              get_name_to_checksum_for_input_folder_files)
from finales_api_client.client.rest_api_connection import FinalesRestAPIConnection


class FinalesAPIClient:
    """
    Class to interact with BMA's API
    """

    def __init__(self, ip_address, port):
        """
        Initialize internal variables
        """
        self._connection = FinalesRestAPIConnection(ip_address, port)

    def post_authenticate(self, username, password):
        """
        Gets a personal access token from the Finales server
        Raises an HTTPError exception if the request fails
        """
        resource_path = '/user_management/authenticate'

        payload = {
                'username': username,
                'password': password,
                'grant_type': 'password'}

        response = self._connection.post(resource_path=resource_path,
                                         payload=payload,
                                         content_type='application/x-www-form-urlencoded')
        return response.json()

    def get_capabilities(self, token, query_string):
        """
        Gets the capabilities (JSON schemas used for request bodies and response bodies) from the Finales server
        Raises an HTTPError exception if the request fails
        """
        resource_path = '/capabilities'
        response = self._connection.get(resource_path, token, query_string=query_string)
        response.raise_for_status()
        return response.json()

    def get_results_requested(self, token):
        """
        Gets the calculation/measurement results posted by the tenants to Finales
        Raises an HTTPError exception if the request fails
        """
        resource_path = '/results_requested'
        response = self._connection.get(resource_path, token)
        response.raise_for_status()
        return response.json()