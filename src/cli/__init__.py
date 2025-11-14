# src/cli/__init__.py
"""
Composants CLI pour EnsaiGPT.
On ré-exporte page_home depuis le sous-package pages.
"""

from .pages import page_home  # pages.__init__ re-exporte déjà page_home

__all__ = ["page_home"]
