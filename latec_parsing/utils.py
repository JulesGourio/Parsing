"""Compatibility layer.

This module now re-exports the parsing toolkit implemented under
`parsing_core/` to preserve backward compatibility with existing notebook
imports (`from utils import *`).
"""

from parsing_core import *
