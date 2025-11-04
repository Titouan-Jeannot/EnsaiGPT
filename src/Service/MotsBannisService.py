"""Service de gestion des mots bannis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Set


@dataclass(slots=True)
class MotsBannisService:
    """Maintient une liste en mémoire de mots bannis."""

    _words: Set[str] = field(default_factory=set)

    def verify_mot_ban(self, text: str) -> bool:
        lower = text.lower()
        return any(word in lower for word in self._words)

    def add_banned_word(self, word: str) -> None:
        self._words.add(word.lower())

    def remove_banned_word(self, word: str) -> None:
        self._words.discard(word.lower())

    def list_banned_words(self) -> Iterable[str]:
        return sorted(self._words)
