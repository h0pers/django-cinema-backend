from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from django.core.exceptions import ImproperlyConfigured

from library.aws.client import BaseClient

Storage = TypeVar("Storage")
Client = TypeVar("Client")


class StorageClientBase(BaseClient[Client], ABC, Generic[Storage, Client]):
    _storage: Storage

    def __init__(self, client: Client = None, storage: Storage = None) -> None:
        self.storage = storage
        super().__init__(client)

    @abstractmethod
    def _get_default_storage(self) -> Storage:
        pass

    @abstractmethod
    def _expected_storage_type(self) -> type[Storage]:
        pass

    @abstractmethod
    def _client_from_storage(self, storage: Storage) -> Client:
        pass

    @property
    def storage(self) -> Storage:
        return self._storage

    @storage.setter
    def storage(self, storage: Storage | None) -> None:
        if storage is None:
            storage = self._get_default_storage()
        if not isinstance(storage, self._expected_storage_type()):
            exp = self._expected_storage_type().__name__
            raise ImproperlyConfigured(f"storage must be an instance of {exp}")
        self._storage = storage

    @BaseClient.client.setter
    def client(self, client: Client | None) -> Client:
        if client is None:
            client = self._client_from_storage(self.storage)
        super(StorageClientBase, type(self)).client.fset(self, client)
