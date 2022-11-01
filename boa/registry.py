import pathlib

from ax.storage.json_store.registry import CORE_DECODER_REGISTRY, CORE_ENCODER_REGISTRY


class _ConstructPathlib:
    """
    Stupid way to hack a function because Ax decoder requires it to be a class
    and only passes keyword arguments only. Pathlib only takes positional arguments,
    so this class converts the encoded dictionary from encode and decodes it as
    positional arguments and returns a Path object (like a function, but hacky)
    """

    def __new__(cls, pathsegments):
        return pathlib.Path(*pathsegments)


def _add_common_encodes_and_decodes():
    """Add common encodes and decodes all at once when function is ran"""
    for obj in [
        pathlib.Path,
        pathlib.PurePath,
        pathlib.PosixPath,
        pathlib.WindowsPath,
        pathlib.PurePosixPath,
        pathlib.PureWindowsPath,
    ]:
        CORE_ENCODER_REGISTRY[obj] = lambda p: dict(__type=obj.__name__, pathsegments=[str(p)])
    CORE_DECODER_REGISTRY[obj.__name__] = _ConstructPathlib