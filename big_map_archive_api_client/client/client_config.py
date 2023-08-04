from pydantic import BaseModel
import yaml
from big_map_archive_api_client.client.api_client import APIClient

class ClientConfig(BaseModel):
    """Configuration data for a BMA API's client."""

    domain_name: str
    port: int
    token: str
    input_dir: str
    metadata_filename: str
    publish: bool
    requested_record_id: str
    export: bool
    output_dir: str
    output_filename: str
    all_versions: bool
    response_size: int
    same_version: bool
    published_record_id: str
    delete_missing: bool

    @classmethod
    def load_from_config_file(cls, file_path):
        """
        Creates a class instance
        Initializes internal fields from configuration file
        """
        with open(file_path) as f:
            # Get data from config.yaml file
            client_config = yaml.load(f, Loader=yaml.FullLoader)

        return ClientConfig(**client_config)

    def create_client(self):
        """
        Creates a client to interact with BMA's API
        Initializes internal fields
        """
        return APIClient(self.domain_name, self.port, self.token)
