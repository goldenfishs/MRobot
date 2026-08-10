"""Cloud-first part library services with an offline ZIP fallback.

The desktop UI loads a small HTTPS catalogue and downloads selected files on
demand.  A cached catalogue and a user-selected ZIP keep browsing available
when the service is unreachable.  This package deliberately has no Qt
dependency so the same catalogue and download rules can be reused by the CLI.
"""

from .catalog import (
    ArchiveEntry,
    PartCatalog,
    PartLibraryError,
    download_entries,
    extract_entries,
    format_size,
)

__all__ = [
    "ArchiveEntry",
    "PartCatalog",
    "PartLibraryError",
    "download_entries",
    "extract_entries",
    "format_size",
]
