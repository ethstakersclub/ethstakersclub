import requests


class BeaconAPI:
    def __init__(self, beacon_api_endpoint):
        self.endpoint = beacon_api_endpoint
        self.session = requests.Session()

    def _make_request(self, endpoint):
        url = f"{self.endpoint}{endpoint}"
        response = self.session.get(url, timeout=30)
        return response.json()
        
    def _make_post_request(self, endpoint, data):
        url = f"{self.endpoint}{endpoint}"
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=data)
        return response.json()

    def get_validators(self, state_id):
        endpoint = f"/eth/v1/beacon/states/{state_id}/validators"
        return self._make_request(endpoint)
    
    def get_proposer_duties(self, epoch):
        endpoint = f"/eth/v1/validator/duties/proposer/{epoch}"
        return self._make_request(endpoint)
    
    def get_attestation_committees(self, state_id, epoch):
        endpoint = f"/eth/v1/beacon/states/{state_id}/committees?epoch={epoch}"
        return self._make_request(endpoint)
    
    def get_finality_checkpoints(self, state_id):
        endpoint = f"/eth/v1/beacon/states/{state_id}/finality_checkpoints"
        return self._make_request(endpoint)
    
    def get_rewards_attestations(self, epoch, validators):
        endpoint = f"/eth/v1/beacon/rewards/attestations/{epoch}"
        return self._make_post_request(endpoint, validators)

    def get_rewards_sync(self, slot, validators):
        endpoint = f"/eth/v1/beacon/rewards/sync_committee/{slot}"
        return self._make_post_request(endpoint, validators)
