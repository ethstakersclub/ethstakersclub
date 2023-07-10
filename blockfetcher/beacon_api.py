import requests


class BeaconAPI:
    def __init__(self, beacon_api_endpoint):
        self.endpoint = beacon_api_endpoint
        self.session = requests.Session()

    def _make_request(self, endpoint):
        url = f"{self.endpoint}{endpoint}"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def get_validators(self, state_id):
        endpoint = f"/eth/v1/beacon/states/{state_id}/validators"
        return self._make_request(endpoint)
    
    def get_proposer_duties(self, epoch):
        endpoint = f"/eth/v1/validator/duties/proposer/{epoch}"
        return self._make_request(endpoint)
    
    def get_attestation_committees(self, state_id, epoch):
        endpoint = f"/eth/v1/beacon/states/{state_id}/committees?epoch={epoch}"
        return self._make_request(endpoint)
