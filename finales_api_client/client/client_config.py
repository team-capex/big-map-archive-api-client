from pydantic import BaseModel
import yaml
from finales_api_client.client.api_client import FinalesAPIClient

class FinalesClientConfig(BaseModel):
    """Configuration data for Finales API's client."""

    ip_address: str
    port: int
    username: str
    password: str
    database_endpoint_access_key: str

    @classmethod
    def load_from_config_file(cls, file_path):
        """
        Creates a class instance
        Initializes internal fields from configuration file
        """
        with open(file_path) as f:
            # Get data from config.yaml file
            client_config = yaml.load(f, Loader=yaml.FullLoader)

        return FinalesClientConfig(**client_config)

    def create_client(self):
        """
        Creates a client to interact with Finales' API
        Initializes internal fields
        """
        return FinalesAPIClient(self.ip_address, self.port, self.username, self.password, self.database_endpoint_access_key)