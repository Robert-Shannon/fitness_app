from __future__ import annotations

import json
from datetime import datetime, time, timedelta
from typing import Any, Optional

from authlib.common.urls import extract_params
from authlib.integrations.requests_client import OAuth2Session

AUTH_URL = "https://api-7.whoop.com"
REQUEST_URL = "https://api.prod.whoop.com/developer"


def _auth_password_json(_client, _method, uri, headers, body):
    body = json.dumps(dict(extract_params(body)))
    headers["Content-Type"] = "application/json"
    return uri, headers, body


class WhoopClient:
    """Make requests to the WHOOP API.

    This client now supports both legacy username/password authentication and OAuth token–based
    authentication. If an access token (and optionally a refresh token) is provided, it will be
    used instead of performing a password-based login.

    Examples:
        Legacy:
            client = WhoopClient(username, password)
            with client as c:
                profile = c.get_profile()

        OAuth token based:
            client = WhoopClient(access_token="...", refresh_token="...")
            with client as c:
                profile = c.get_profile()
    """

    TOKEN_ENDPOINT_AUTH_METHOD = "password_json"  # noqa

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        authenticate: bool = True,
    ):
        """
        Initialize an OAuth2 session for making API requests.

        Args:
            username (str, optional): WHOOP account email for legacy auth.
            password (str, optional): WHOOP account password for legacy auth.
            access_token (str, optional): OAuth access token.
            refresh_token (str, optional): OAuth refresh token.
            authenticate (bool): Whether to fetch a token from the API upon session creation.
                Defaults to True. (Ignored if access_token is provided.)
        """
        self._username = username
        self._password = password
        self._access_token = access_token
        self._refresh_token = refresh_token

        self.session = OAuth2Session(
            token_endpoint=f"{AUTH_URL}/oauth/token",
            token_endpoint_auth_method=self.TOKEN_ENDPOINT_AUTH_METHOD,
        )

        self.session.register_client_auth_method(
            (self.TOKEN_ENDPOINT_AUTH_METHOD, _auth_password_json)
        )

        self.user_id = ""

        # If an access token is provided, use it
        if self._access_token:
            self.session.token = {
                "access_token": self._access_token,
                "refresh_token": self._refresh_token,
                "token_type": "Bearer",
            }
            # Optionally, if your token payload includes user info, extract the user id:
            self.user_id = str(self.session.token.get("user", {}).get("id", ""))
        elif authenticate:
            self.authenticate()

    def __enter__(self) -> WhoopClient:
        """Enter a context manager."""
        return self

    def __exit__(self, *_) -> None:
        """Exit a context manager by closing the OAuth2 session."""
        self.close()

    def __str__(self) -> str:
        """Return a string representation of the client."""
        return f"WhoopClient({self.user_id if self.user_id else '<Unauthenticated>'})"

    def close(self) -> None:
        """Close the OAuth2 session."""
        self.session.close()

    ####################################################################################
    # API ENDPOINTS

    def get_profile(self) -> dict[str, Any]:
        """Get the user's basic profile."""
        return self._make_request(method="GET", url_slug="v1/user/profile/basic")

    def get_body_measurement(self) -> dict[str, Any]:
        """Get the user's body measurements."""
        return self._make_request(method="GET", url_slug="v1/user/measurement/body")

    def get_cycle_by_id(self, cycle_id: str) -> dict[str, Any]:
        """Get the cycle for the specified ID."""
        return self._make_request(method="GET", url_slug=f"v1/cycle/{cycle_id}")

    def get_cycle_collection(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        start, end = self._format_dates(start_date, end_date)
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/cycle",
            params={"start": start, "end": end},
        )

    def get_recovery_for_cycle(self, cycle_id: str) -> dict[str, Any]:
        return self._make_request(method="GET", url_slug=f"v1/cycle/{cycle_id}/recovery")

    def get_recovery_collection(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        start, end = self._format_dates(start_date, end_date)
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/recovery",
            params={"start": start, "end": end},
        )

    def get_sleep_by_id(self, sleep_id: str) -> dict[str, Any]:
        return self._make_request(method="GET", url_slug=f"v1/activity/sleep/{sleep_id}")

    def get_sleep_collection(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        start, end = self._format_dates(start_date, end_date)
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/activity/sleep",
            params={"start": start, "end": end},
        )

    def get_workout_by_id(self, workout_id: str) -> dict[str, Any]:
        return self._make_request(method="GET", url_slug=f"v1/activity/workout/{workout_id}")

    def get_workout_collection(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        start, end = self._format_dates(start_date, end_date)
        return self._make_paginated_request(
            method="GET",
            url_slug="v1/activity/workout",
            params={"start": start, "end": end},
        )

    ####################################################################################
    # API HELPER METHODS

    def authenticate(self, **kwargs) -> None:
        """Authenticate OAuth2Session by fetching token."""
        self.session.fetch_token(
            url=f"{AUTH_URL}/oauth/token",
            username=self._username,
            password=self._password,
            grant_type="password",
            **kwargs,
        )
        if not self.user_id:
            self.user_id = str(self.session.token.get("user", {}).get("id", ""))

    def is_authenticated(self) -> bool:
        """Check if the OAuth2Session is authenticated."""
        return self.session.token is not None

    def _make_paginated_request(
        self, method, url_slug, **kwargs
    ) -> list[dict[str, Any]]:
        params = kwargs.pop("params", {})
        response_data: list[dict[str, Any]] = []
        while True:
            response = self._make_request(
                method=method,
                url_slug=url_slug,
                params=params,
                **kwargs,
            )
            response_data += response["records"]
            if next_token := response["next_token"]:
                params["nextToken"] = next_token
            else:
                break
        return response_data

    def _make_request(
        self, method: str, url_slug: str, **kwargs: Any
    ) -> dict[str, Any]:
        response = self.session.request(
            method=method,
            url=f"{REQUEST_URL}/{url_slug}",
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def _format_dates(
        self, start_date: str | None, end_date: str | None
    ) -> tuple[str | None, str | None]:
        if not start_date and not end_date:
            return None, None
        if start_date:
            start = datetime.fromisoformat(start_date).isoformat() + "Z"
        else:
            start = None
        if end_date:
            end = datetime.fromisoformat(end_date).isoformat(timespec="seconds") + "Z"
        else:
            end = None
        return start, end
