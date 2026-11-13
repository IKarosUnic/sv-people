"""Accidents, Disasters and Misfortunes module."""

from saltbor.accidents.engine import MisfortuneEngine
from saltbor.accidents.models import AccidentEvent, DisasterEvent

__all__ = ["MisfortuneEngine", "AccidentEvent", "DisasterEvent"]
