"""Utility functions for working with types."""

from typing import TypeVar, Dict, Any, Type, Union, cast

T = TypeVar('T')

def ensure_dict(value: Union[Dict[str, Any], None], cls: Type[T]) -> T:
    """Ensure a value is a dictionary of the specified type."""
    if value is None:
        value = {}
    return cast(T, value)
