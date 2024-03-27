"""
Cyclic Classes - Exceptions
"""


class CyclicError(Exception):
    """Error from cyclic-classes package"""


class CyclicNonImportError(CyclicError):
    """RegisteredImport detected non-import clause"""


class CyclicRegisteredClassError(CyclicError):
    """RegisteredClass exception"""
