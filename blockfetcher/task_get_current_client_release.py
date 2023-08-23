from django.utils import timezone
from dateutil.parser import parse
from ethstakersclub.settings import eth_clients, BLOCKPRINT_API_URL
from blockfetcher.models import EthClient
from blockfetcher.cache import *
import requests
import logging

logger = logging.getLogger(__name__)


def get_latest_release_info(owner, repo):
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        version = data.get("tag_name")
        release_date_str = data.get("published_at")
        release_date = parse(release_date_str).astimezone(timezone.get_current_timezone())
        return version, release_date
    else:
        print(f"Failed to retrieve release information. Status code: {response.status_code}")
        return None, None


def get_consensus_client_diversity():
    current_epoch = get_current_epoch_from_cache()
    begin_epoch = current_epoch - 1000 if current_epoch > 1000 else 0
    
    api_url = f"{BLOCKPRINT_API_URL}/blocks_per_client/{begin_epoch}/{current_epoch}"
    
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()

        total_blocks = sum(data.values())
        percentages = {client: (blocks / total_blocks) * 100 for client, blocks in data.items()}

        return percentages
    else:
        print(f"Failed to retrieve client diversity. Status code: {response.status_code}")
        return []


def get_execution_client_diversity():
    response = requests.get("https://ethernodes.org/api/clients")
    
    if response.status_code == 200:
        data = response.json()

        total_nodes = sum(entry['value'] for entry in data)
        percentages = {entry['client']: (entry['value'] / total_nodes) * 100 for entry in data}

        return percentages
    else:
        print(f"Failed to retrieve client diversity. Status code: {response.status_code}")
        return []


def get_current_client_release():
    clients = EthClient.objects.all().values("client_name", "repository_owner", "repo_name", "type", "version")
    clients_dict = {str(c['client_name']): c for c in clients}

    for eth_client in eth_clients:
        repo = eth_client["repo_name"]
        owner = eth_client["repository_owner"]

        latest_version, release_date = get_latest_release_info(owner, repo)
    
        if latest_version:
            logger.info(f"The latest version of {repo} is: {latest_version} Released on: {release_date}")

            if eth_client["client_name"] not in clients_dict or clients_dict[eth_client["client_name"]]["version"] != latest_version:
                logger.info(f"New Version: {repo} {latest_version}")

                obj, created = EthClient.objects.update_or_create(
                    client_name=eth_client["client_name"],
                    defaults={
                              'version': latest_version,
                              'release_timestamp': release_date,
                              'repository_owner': owner,
                              'repo_name': repo,
                              'type': eth_client["type"]},
                )
        else:
            logger.warning(f"Error getting current client version for {eth_client}")

    consensus_percentage_list = get_consensus_client_diversity()
    for client_name in consensus_percentage_list:
        usage_percentage = consensus_percentage_list[client_name]
        try:
            client = EthClient.objects.get(client_name__iexact=client_name)
            client.usage_percentage = usage_percentage
            client.save()
        except EthClient.DoesNotExist:
            pass
    
    execution_percentage_list = get_execution_client_diversity()
    for client_name in execution_percentage_list:
        usage_percentage = execution_percentage_list[client_name]
        try:
            client = EthClient.objects.get(client_name__iexact=client_name)
            client.usage_percentage = usage_percentage
            client.save()
        except EthClient.DoesNotExist:
            pass
    