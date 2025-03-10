import hashlib
import hmac
import json
from typing import Any, Dict


class AlpacaAuth():
    """
    Auth class required by Alpaca API
    """
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key

    def get_headers(
        self,
        timestamp: int = None,
        params: Dict[str, Any] = None,
        auth_type: str = None
    ):
        """
        Generates context appropriate headers({SIGNED, KEYED, None}) for the request.
        :return: a dictionary of auth headers
        """

        if auth_type == "SIGNED":

            params = json.dumps(params)
            payload = f'{str(timestamp)}#{params}'

            sign = hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return {
                # "Content-Type": 'application/json',
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
                # "X-BM-TIMESTAMP": str(timestamp),
            }

        elif auth_type == "KEYED":
            return {
                # "Content-Type": 'application/json',
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
            }

        else:
            return {
                # "Content-Type": 'application/json',
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
            }

    def get_ws_auth_payload(self, timestamp: int = None):
        """
        Generates websocket payload.
        :return: a dictionary of auth headers with api_key, timestamp, signature
        """

        # payload = f'{str(timestamp)}#{self.memo}#alpaca.WebSocket'
        #
        # sign = hmac.new(
        #     self.secret_key.encode('utf-8'),
        #     payload.encode('utf-8'),
        #     hashlib.sha256
        # ).hexdigest()

        return {
            {"action": "auth", "key": self.api_key, "secret": self.secret_key}
        }
