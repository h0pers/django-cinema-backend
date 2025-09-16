from abc import ABC
from typing import Generic, TypeVar

from django.core.exceptions import ImproperlyConfigured

Client = TypeVar("Client")


class BaseClient(ABC, Generic[Client]):
    _client: Client

    def __init__(self, client: Client = None) -> None:
        self.client = client

    @property
    def client(self) -> Client:
        return self._client

    @client.setter
    def client(self, client: Client | None) -> None:
        if client is None:
            raise ImproperlyConfigured("A client must be set")
        self._client = client
