"""Keep extruct from importing its microformat (mf2py) and RDFa (pyRdfa ->
rdflib) extractors.

extruct eagerly imports every extractor at module load, but recipe_scrapers only
ever asks for the ``json-ld`` and ``microdata`` syntaxes (see
``recipe_scrapers._schemaorg.SYNTAXES``). The microformat and RDFa extractors —
and their heavy, otherwise-unreachable dependencies mf2py, pyRdfa and rdflib — are
therefore never called. We register lightweight stand-ins under their module names
before extruct is first imported, so the real modules (and their deps) never load.
Measured saving: ~16 MiB off the resident floor, with no behaviour change (the
disabled syntaxes were never requested).

This must run before anything imports ``recipe_scrapers`` / ``extruct``; it is
invoked from ``pkg/__init__.py`` so it happens before any ``pkg`` submodule loads.
"""

from __future__ import annotations

import sys
import types

# extruct submodule -> the extractor class name it must expose
_STUBBED = {
    "extruct.microformat": "MicroformatExtractor",
    "extruct.rdfa": "RDFaExtractor",
}


class _DisabledExtractor:
    """Stand-in for an extractor we never invoke. If a caller ever does request
    the disabled syntax, it yields no items rather than raising."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    def extract_items(self, *args, **kwargs) -> list:
        return []


def slim_extruct() -> bool:
    """Register stubs for extruct's unused heavy extractors.

    Returns False (a no-op) if extruct is already imported — too late to slim.
    """
    if "extruct" in sys.modules:
        return False

    for name, attr in _STUBBED.items():
        if name in sys.modules:
            continue
        module = types.ModuleType(name)
        setattr(module, attr, _DisabledExtractor)
        module.__extruct_stub__ = True  # marker for tests/introspection
        sys.modules[name] = module

    return True
