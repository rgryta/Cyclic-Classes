"""
Cyclic Classes - __init__
"""

import logging

from .context import CyclicClassesImports as cyclic_imports
from .decorators import register

logger = logging.getLogger(__name__)

ch = logging.StreamHandler()
# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
# add the handlers to the logger
logger.handlers.clear()
logger.addHandler(ch)
