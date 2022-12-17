"""Provides basic client to the Render API."""
import os
from typing import Any, Optional


import requests
from requests import HTTPError


RENDER_API_BASE_URL: str = "https://api.render.com/v1/services"

APPLICATION_JSON: str = "application/json"


def get_bearer_token() -> Optional[str]:
    """Fetch Render api token from environment variable.

    Returns:
        returns the Render api token stored in the environment
        variable named RENDER_TOKEN.
    """
    return os.getenv("RENDER_TOKEN")


def create_headers(is_post: bool = False) -> dict[str, str]:
    """Helper function to create headers for api call.

    Args:
        is_post: indicator if call is going to be a POST.

    Returns:
        A set of headers for a Render api call.

    """
    bearer = f"Bearer {get_bearer_token()}"
    headers = {"Accept": APPLICATION_JSON, "Authorization": bearer}
    if is_post:
        headers["Content-Type"] = APPLICATION_JSON
    return headers


def retrieve_env_from_render(service_name) -> Any:
    """Gets environment variables for the specified service.

    Args:
        service_name: name of service to fetch the environment variables for.

    Returns:
        A list of environment variables for a given service.

    """
    url = f"{RENDER_API_BASE_URL}/{service_name}/env-vars?limit=20"
    with requests.get(url, headers=create_headers()) as response:
        try:
            response.raise_for_status()
            return response.json()
        except HTTPError as exc:
            return handle_errors(exc.response.status_code)


def set_env_variables_for_service(service_name: str, env_vars) -> Any:
    """Sets the environment variables for the specified service.

    Args:
        service_name: name of service to set env vars for.
        env_vars: list of environment variables

    Returns:
        nothing

    """
    service_id = find_service_by_name(service_name)["service"]["id"]
    url = f"{RENDER_API_BASE_URL}/{service_id}/env-vars"
    payload = env_vars
    with requests.put(url, headers=create_headers(True), json=payload) as response:
        try:
            response.raise_for_status()
            return response.json()
        except HTTPError as exc:
            return handle_errors(exc.response.status_code)


def fetch_services(limit=20, cursor=None) -> Any:
    """Gets services associated with Render account.

    This function will fetch all services, upto specified limit
    for the associated Render account.

    Args:
        limit: number of services to fetch. Defaults to 20.
        cursor: indicator passed to Render to fetch next page of results.

    Returns:
        All services associated with a Render account.

    """
    cursor_query_param = f"&cursor={cursor}" if cursor is not None else ""
    url = f"{RENDER_API_BASE_URL}?limit={limit}{cursor_query_param}"
    with requests.get(url, headers=create_headers()) as response:
        try:
            response.raise_for_status()
            return response.json()
        except HTTPError as exc:
            return handle_errors(exc.response.status_code)


def find_service_by_name(service_name: str) -> Any:
    """Finds service by name associated with Render account.

    This function will fetch services from Redner and return the
    service that matches the specified name.

    Args:
        service_name: name of service to search for.

    Returns:
        Service information for specified service if it exists.

    """
    data = fetch_services(limit=50)
    found = False
    resulting_service = None
    cursor = None
    while True:
        for svc_listing in data:
            service = svc_listing["service"]
            cursor = svc_listing["cursor"]
            if service["name"] == service_name:
                resulting_service = svc_listing
                found = True
                break
        if found:
            break
        data = fetch_services(cursor=cursor)
        if len(data) == 0:
            break
    return resulting_service


def handle_errors(status_code) -> dict[str, str]:
    """Helper function to handle errors from the api."""
    if status_code == 401:
        return {"error": "401 - Unauthorized"}
    elif status_code == 406:
        return {"error": "406 - request error"}
    elif status_code == 429:
        return {"error": "429 - Exceeded service limit"}
    elif status_code == 500 or status_code == 503:
        return {"error": f"{status_code} - Render service unavailable"}
    else:
        return {"error": f"{status_code} - unexpected error"}
