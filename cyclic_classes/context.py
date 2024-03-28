"""
Cyclic Classes - Context
"""

from __future__ import annotations

import re
import ast
import sys
import types
import inspect
import logging
import importlib
from inspect import currentframe, getframeinfo

from .classes import get_registered_class, get_registered_module
from .constants import ENCODING_CAPTURE
from .exceptions import CyclicNonImportError

logger = logging.getLogger(__name__)


class _SkippableContext:
    """
    Skippable Context... skips context content
    """

    class SkippableContextException(Exception):
        """
        Exception to be raised by the trace function to skip the context execution
        """

    # Depth that describes which frame we should go back to, ctx managers inheriting from _SkippableContext should
    # increase depth by 1 by each level of inheritance
    depth: int = 1

    def __enter__(self):
        sys.settrace(lambda *args, **keys: None)
        frame = sys._getframe(self.depth)
        frame.f_trace = self.trace
        return self

    def trace(self, frame, event, arg):
        """
        Trace function that skips the context execution
        """
        raise _SkippableContext.SkippableContextException

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If something unpredictable has happened - throw exception, otherwise not
        if exc_type == _SkippableContext.SkippableContextException:
            return True
        return False


class CyclicClassesImports(_SkippableContext):
    """
    Special context - skips code within it, and instead parses it to inject custom imports (this context disallows
    non-import statements).
    """

    depth: int = 2  # For _SkippableContext

    filename: str  # File where the CCI is executed in for later read
    first_line: int  # First line number of executed CCI

    mod: types.ModuleType  # Module where CCI is executed
    encoding: str = "utf-8"

    def _file_encoding(self):
        """
        Get file encoding
        """
        with open(self.filename, "r", encoding="utf-8") as file:
            for _ in range(2):  # Check 1st two lines
                try:
                    found = re.search(ENCODING_CAPTURE, file.readline())
                # pylint: disable=broad-exception-caught
                except Exception as exc:  # pragma: no cover
                    logger.critical(exc.args[0])
                if found:
                    self.encoding = found.group(1)
                    break

    def __enter__(self):
        cf = currentframe()
        prev_frame = cf.f_back

        self.first_line = prev_frame.f_lineno
        self.filename = getframeinfo(prev_frame).filename
        self._file_encoding()

        self.mod = inspect.getmodule(inspect.stack()[1][0])
        super().__enter__()

    def _get_code(self) -> str:
        """
        Get ctx manager code from file
        """
        with open(self.filename, encoding=self.encoding) as f:
            lines = f.readlines()

        i = self.first_line
        # Skip empty lines at the beginning
        while i < len(lines) and lines[i].isspace():
            i = i + 1
        leading_spaces = len(lines[i]) - len(lines[i].lstrip())  # Leading spaces length for ctx manager

        slines = []
        while i < len(lines):
            f_line = lines[i]

            if f_line.isspace():  # If line's empty then add it
                i = i + 1
                slines.append("")
                continue

            # If there's less leading spaces than what was detected before, it means we're exiting CCI
            nl = len(f_line) - len(f_line.lstrip())
            if nl < leading_spaces:
                break
            slines.append(f_line[leading_spaces:].rstrip())
            i = i + 1

        code = "\n".join(slines)  # Code to analyze
        return code

    def _check_non_imports(self, code: str):
        """
        Check if there are any non-import statements in the code
        """
        cxt_o = [
            i
            for i in ast.walk(ast.parse(code))
            if not isinstance(i, (ast.ImportFrom, ast.Import, ast.Module, ast.alias))
        ]
        if cxt_o:
            lines = {self.first_line + cxt.lineno for cxt in cxt_o if hasattr(cxt, "lineno")}
            raise CyclicNonImportError(
                f"Detected non-import statement(s) in registration clause, e.g.: {self.filename}:"
                f"{','.join([str(line) for line in sorted(lines)])}"
            )

    def _get_spec(self, name: str, within: str, with_log: bool = True) -> importlib.util.ModuleSpec:
        """
        If import is happening in a module that is a directory with __init__.py file,
        then we only specify one <dot>, otherwise two
        """
        mod_spec = importlib.util.find_spec(name=within)
        with_submodules = bool(getattr(mod_spec, "submodule_search_locations", None))

        same_module = mod_spec.name.split(".")[0] == self.mod.__name__.split(".")[0]

        # IMPORTANT: same_module checks are made for weird behaviour that IDE sees import as correct, but it shouldn't
        # IMPORTANT: so it actually still does work correctly with cyclic_classes even though it wouldn't without
        # IMPORTANT: same_module check is to handle from imports between packages as well (though it's not recommended)
        prefix = "." if with_submodules or not same_module else ".."
        imp_name = prefix + name
        logger.debug(f"Looking for [{imp_name}] under [{within}]")
        spec = importlib.util.find_spec(name=imp_name, package=within)
        if spec:
            if with_log:
                logger.warning(
                    f"Your import of [{name}] within [{within}] is written as absolute even though "
                    f"it's relative, resolving it as such, but it is advised to fix the imports "
                    f"with preceding prefix [{prefix}]"
                )
            return spec
        raise CyclicNonImportError(f"Could not find spec for [{name}] within [{within}]")

    def _get_spec_class(self, cxt: ast, name: ast.alias) -> tuple[importlib.util.ModuleSpec, bool]:
        """
        Get spec for imported module (or imported class)
        """
        import_class = False
        if isinstance(cxt, ast.ImportFrom):
            # Find spec for the import `from <imp_name>`
            prefix = "." * cxt.level
            imp_name = prefix + cxt.module

            try:
                spec = importlib.util.find_spec(name=imp_name, package=self.mod.__name__)
            except ModuleNotFoundError:
                spec = None
            if spec is None:
                spec = self._get_spec(name=cxt.module, within=self.mod.__name__, with_log=not bool(prefix))

            # Now find spec for the import `from <imp_name> import <name.name>`
            try:
                _spec = importlib.util.find_spec(name=name.name, package=spec.name)
                spec = _spec or self._get_spec(name=name.name, within=spec.name, with_log=False)
            except (ImportError, CyclicNonImportError) as exc:
                # This is a class - as such there's an exception due to not fully initialized module
                logger.debug(exc, exc_info=True)
                import_class = True
        else:
            assert isinstance(cxt, ast.Import)
            try:
                spec = importlib.util.find_spec(name=name.name, package=self.mod.__name__)
            except ModuleNotFoundError:
                spec = None
            if spec is None:
                spec = self._get_spec(name=name.name, within=self.mod.__name__)
        return spec, import_class

    def _get_registered_object(
        self, spec: importlib.util.ModuleSpec, name: ast.alias, import_class: bool
    ) -> tuple[types.ModuleType | type, str]:
        """
        Get registered object
        """
        module_name = spec.name
        if import_class:
            class_name = name.name
            if "." in class_name:
                raise CyclicNonImportError(
                    f"There's an unexpected dot in import statement for [{name.name}] in {self.mod.__name__}"
                )
            fullname = ".".join([module_name, class_name])
            rgz_obj = get_registered_class(name=fullname, qualname=class_name)
        else:
            fullname = module_name
            rgz_obj = get_registered_module(name=module_name)
        return rgz_obj, fullname

    def _import_object(self, rgz_obj: object, asname: str):
        """
        Import object to the module
        """
        old_mod = self.mod
        for mod_name in asname.split(".")[:-1]:
            new_mod = types.ModuleType(mod_name)
            setattr(old_mod, mod_name, new_mod)
            old_mod = new_mod
        setattr(old_mod, asname.rsplit(".", maxsplit=1)[-1], rgz_obj)

    def __exit__(self, exc_type, exc_val, exc_tb):
        ret = super().__exit__(exc_type, exc_val, exc_tb)
        if not ret:
            return False  # If there was some exception from _SkippableContext, reraise it

        # Load CCI code content
        code = self._get_code()

        # Detect if there are any statements that aren't imports - we cannot handle such
        self._check_non_imports(code=code)

        # Detect imports
        cxt_m = [i for i in ast.walk(ast.parse(code)) if isinstance(i, (ast.ImportFrom, ast.Import))]

        for cxt in cxt_m:
            for name in cxt.names:
                spec, import_class = self._get_spec_class(cxt, name)
                rgz_obj, fullname = self._get_registered_object(spec, name, import_class)

                # Module, class (if we import the class) and alias which we register and pretend we get our classes from
                asname = name.asname if name.asname else name.name

                logger.debug(f"Importing {fullname} as {asname} => {self.mod.__name__}")

                self._import_object(rgz_obj=rgz_obj, asname=asname)
        return True
