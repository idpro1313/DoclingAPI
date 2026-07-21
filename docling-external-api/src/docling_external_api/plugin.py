"""Pluggy entry point module for docling-external-api plugin.

This module provides the entry point for the docling pluggy system.
Registration is done via pyproject.toml:
    [project.entry-points."docling"]
    docling_external_api = "docling_external_api.plugin:plugin"
"""

from docling_external_api.integration import register_plugin, plugin

__all__ = ["register_plugin", "plugin"]