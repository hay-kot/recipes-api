# Trim extruct's unused heavy extractors (mf2py / rdflib) before any submodule
# imports recipe_scrapers. Must be the first thing that runs in the package.
from ._slim_extruct import slim_extruct

slim_extruct()

__version__ = "dev"
