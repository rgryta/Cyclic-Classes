import ast
import importlib
import inspect
import logging
import sys
import types
from inspect import currentframe, getframeinfo

from .classes import get_registered_class, get_registered_module
from .constants import REGISTERED_MODULE
from .exceptions import CyclicNonImportError

logger = logging.getLogger(__name__)


class _SkippableContext(object):
    """
    Skippable Context... skips context content
    """

    class SkippableContextException(Exception):
        pass

    # Depth that describes which frame we should go back to, ctx managers inheriting from _SkippableContext should
    # increase depth by 1 by each level of inheritance
    depth: int = 1

    def __enter__(self):
        sys.settrace(lambda *args, **keys: None)
        frame = sys._getframe(self.depth)
        frame.f_trace = self.trace
        return self

    def trace(self, frame, event, arg):
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

    def __enter__(self):
        cf = currentframe()
        prev_frame = cf.f_back
        self.first_line = prev_frame.f_lineno
        self.filename = getframeinfo(prev_frame).filename

        super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        ret = super().__exit__(exc_type, exc_val, exc_tb)
        if not ret:
            return False  # If there was some exception from _SkippableContext, reraise it

        # Load CCI code content
        with open(self.filename) as f:
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

        # Detect if there are any statements that aren't imports - we cannot handle such
        cxt_o = [
            i
            for i in ast.walk(ast.parse(code))
            if not isinstance(i, (ast.ImportFrom, ast.Import, ast.Module, ast.alias))
        ]
        if cxt_o:
            lines = {self.first_line + cxt.lineno for cxt in cxt_o if hasattr(cxt, "lineno")}
            raise CyclicNonImportError(
                f"Detected non-import statement(s) in registration clause, e.g.: {self.filename}:{','.join([str(line) for line in sorted(lines)])}"
            )

        # Detect imports
        cxt_m = [i for i in ast.walk(ast.parse(code)) if isinstance(i, (ast.ImportFrom, ast.Import))]

        mod = inspect.getmodule(inspect.stack()[1][0])  # This is the module were we're executing CCI

        for cxt in cxt_m:
            for name in cxt.names:

                def _get_spec(name: str, within: str, with_log: bool = True):
                    """
                    If import is happening in a module that is a directory with __init__.py file, then we only specify one <dot>, otherwise two
                    """
                    mod_spec = importlib.util.find_spec(name=within)
                    with_submodules = bool(getattr(mod_spec, "submodule_search_locations", None))

                    same_module = mod_spec.name.split(".")[0] == mod.__name__.split(".")[0]

                    # TODO: Unsure about the same_module check :/
                    prefix = "." if with_submodules or not same_module else ".."
                    imp_name = prefix + name
                    logger.debug(f"Looking for [{imp_name}] under [{within}]")
                    spec = importlib.util.find_spec(name=imp_name, package=within)
                    if spec:
                        print(spec)
                        if with_log:
                            logger.warning(
                                f"Your import of {name} within [{within}] is written as absolute even though it's relative, resolving it as such,"
                                f" but it is advised to fix the imports with preceding prefix [{prefix}]."
                            )
                        return spec
                    raise CyclicNonImportError(f"Could not find spec for [{name}] within [{within}]")

                # Get spec for imported module (or imported class)
                import_class = False
                if isinstance(cxt, ast.ImportFrom):

                    # Find spec for the import `from <imp_name>`
                    prefix = "." * cxt.level
                    imp_name = prefix + cxt.module
                    spec = importlib.util.find_spec(name=imp_name, package=mod.__name__)

                    if spec is None and not prefix:
                        spec = _get_spec(name=cxt.module, within=mod.__name__)

                    # Now find spec for the import `from <imp_name> import <name.name>`
                    try:
                        _spec = importlib.util.find_spec(name=name.name, package=spec.name)
                        spec = _spec or _get_spec(name=name.name, within=spec.name, with_log=False)
                    except (ImportError, CyclicNonImportError) as exc:
                        # This is a class - as such there's an exception due to not fully initialized module
                        logger.debug(exc, exc_info=True)
                        import_class = True
                else:
                    assert isinstance(cxt, ast.Import)
                    spec = importlib.util.find_spec(name=name.name, package=mod.__name__)
                    if spec is None:
                        spec = _get_spec(name=name.name, within=mod.__name__)

                # Module, class (if we import the class) and alias which we register and pretend we get our classes from
                module_name = spec.name
                class_name = name.name if import_class else ""
                if "." in class_name:
                    raise CyclicNonImportError(
                        f"There's an unexpected dot in import statement for [{name.name}] in {mod.__name__}"
                    )
                fullname = ".".join([module_name, class_name]) if import_class else module_name
                asname = name.asname if name.asname else name.name

                logger.debug(f"Importing {fullname} as {asname} => {mod.__name__}")

                # Retrieve registered object (module or class)
                rgz_obj = (
                    get_registered_class(name=fullname, qualname=class_name)
                    if import_class
                    else (
                        get_registered_module(name=module_name)
                        if isinstance(cxt, ast.ImportFrom)
                        else get_registered_module(module_name)
                    )
                )

                # Import the object
                old_mod = mod
                for mod_name in asname.split(".")[:-1]:
                    new_mod = types.ModuleType(mod_name)
                    old_mod.__setattr__(mod_name, new_mod)
                    old_mod = new_mod
                old_mod.__setattr__(asname.rsplit(".", maxsplit=1)[-1], rgz_obj)
        return True
