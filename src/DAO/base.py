"""Infrastructure DAO en mémoire pour les tests."""
from __future__ import annotations

from copy import deepcopy
from typing import Dict, Generic, Iterable, Iterator, Optional, TypeVar


T = TypeVar("T")


class BaseInMemoryDAO(Generic[T]):
    """DAO générique stockant les entités en mémoire.

    Chaque entité est identifiée par une clé numérique. Les classes concrètes doivent
    indiquer le nom de l'attribut primaire (``pk_attr``).
    """

    def __init__(self, pk_attr: str) -> None:
        self._pk_attr = pk_attr
        self._items: Dict[int, T] = {}
        self._counter: int = 1

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------
    def _get_pk_value(self, entity: T) -> Optional[int]:
        return getattr(entity, self._pk_attr)

    def _ensure_identifier(self, entity: T) -> int:
        pk_value = self._get_pk_value(entity)
        if pk_value is None:
            pk_value = self._counter
            setattr(entity, self._pk_attr, pk_value)
            self._counter += 1
        else:
            self._counter = max(self._counter, pk_value + 1)
        return pk_value

    def _clone(self, entity: T) -> T:
        return deepcopy(entity)

    # ------------------------------------------------------------------
    # Opérations CRUD de base
    # ------------------------------------------------------------------
    def create(self, entity: T) -> T:
        pk_value = self._ensure_identifier(entity)
        self._items[pk_value] = self._clone(entity)
        return self._clone(entity)

    def read(self, entity_id: int) -> Optional[T]:
        entity = self._items.get(entity_id)
        return self._clone(entity) if entity is not None else None

    def update(self, entity: T) -> bool:
        pk_value = self._get_pk_value(entity)
        if pk_value is None or pk_value not in self._items:
            return False
        self._items[pk_value] = self._clone(entity)
        return True

    def delete(self, entity_id: int) -> bool:
        return self._items.pop(entity_id, None) is not None

    def list_all(self) -> Iterable[T]:
        for entity in self._items.values():
            yield self._clone(entity)

    # ------------------------------------------------------------------
    # Utilitaires tests
    # ------------------------------------------------------------------
    def __len__(self) -> int:  # pragma: no cover - utilisé seulement en debug
        return len(self._items)

    def clear(self) -> None:  # pragma: no cover - utilisé seulement en debug
        self._items.clear()
        self._counter = 1
