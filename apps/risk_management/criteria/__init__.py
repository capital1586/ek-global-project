import uuid
import typing
import cattrs
import numpy as np
from helpers.attrs import type_cast as type_cast_factory, cast_on_set_factory


_T = typing.TypeVar("_T", bound=type)

# Create the default converter (can still be overridden)
converter = cattrs.Converter()
type_cast = type_cast_factory(converter)
cast_on_set = cast_on_set_factory(converter)


def UUID_to_string(uuid_obj: uuid.UUID) -> str:
    """Stringify a UUID object."""
    if callable(uuid_obj):
        uuid_obj = uuid_obj()
    return str(uuid_obj)


def string_to_UUID(uuid_str: str, _) -> uuid.UUID:
    """Converts a stringified UUID to a UUID object."""
    return uuid.UUID(uuid_str)


# Register a unstructure hook to convert UUIDs to strings
converter.register_unstructure_hook(uuid.UUID, UUID_to_string)
# Register a structure hook to convert strings to UUIDs
converter.register_structure_hook(uuid.UUID, string_to_UUID)


def ndarray_to_list(ndarray_obj: np.ndarray):
    """Converts a numpy ndarray to a list."""
    if callable(ndarray_obj):
        ndarray_obj = ndarray_obj()
    return list(ndarray_obj)


def list_to_ndarray(ndarray_list: list, _) -> np.ndarray:
    """Converts a list to a numpy ndarray."""
    return np.array(ndarray_list)


# Register a unstructure hook to convert numpy ndarrays to lists
converter.register_unstructure_hook(np.ndarray, ndarray_to_list)
# Register a structure hook to convert lists to numpy ndarrays since talib expects numpy ndarrays
converter.register_structure_hook(list, list_to_ndarray)
