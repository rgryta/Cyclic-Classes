import ast
import importlib
import inspect
import logging
import sys
import types
from inspect import currentframe, getframeinfo

from .classes import create_registered_class, create_registered_module
from .constants import REGISTERED_MODULE
from .exceptions import CyclicNonImportError

logger = logging.getLogger(__name__)


class _SkippableContext(object):

    class SkippableContextException(Exception):
        pass

    depth: int = 1

    def __enter__(self):
        sys.settrace(lambda *args, **keys: None)
        frame = sys._getframe(self.depth)
        frame.f_trace = self.trace
        return self

    def trace(self, frame, event, arg):
        raise _SkippableContext.SkippableContextException

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type == _SkippableContext.SkippableContextException:
            return True
        return False


class CyclicClassesImports(_SkippableContext):

    depth: int = 2

    filename: str
    first_line: int

    def __enter__(self):
        cf = currentframe()
        prev_frame = cf.f_back
        self.first_line = prev_frame.f_lineno
        self.filename = getframeinfo(prev_frame).filename

        # after block

        super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        ret = super().__exit__(exc_type, exc_val, exc_tb)
        if not ret:
            return False

        with open(self.filename) as f:
            lines = f.readlines()

        i = self.first_line
        while i < len(lines) and lines[i].isspace():
            i = i + 1
        leading_spaces = len(lines[i]) - len(lines[i].lstrip())
        slines = []
        while i < len(lines):
            f_line = lines[i]

            if f_line.isspace():
                i = i + 1
                slines.append("")
                continue

            nl = len(f_line) - len(f_line.lstrip())
            if nl < leading_spaces:
                break
            slines.append(f_line[leading_spaces:].rstrip())
            i = i + 1

        code = "\n".join(slines)

        cxt_m = [i for i in ast.walk(ast.parse(code)) if isinstance(i, (ast.ImportFrom, ast.Import))]
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
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
        for cxt in cxt_m:
            for name in cxt.names:

                package, level = (
                    (
                        mod.__name__,
                        cxt.level,
                    )
                    if isinstance(cxt, ast.ImportFrom)
                    else (
                        name.name,
                        0,
                    )
                )
                self_spec = importlib.util.find_spec(name=package)
                cc_spec = importlib.util.find_spec(name="cyclic_classes", package=package)
                same_package = self_spec.name.split(".")[0] == cc_spec.name.split(".")[0] or level > 0

                if same_package and not getattr(self_spec, "submodule_search_locations", None):
                    level = level + 1

                _from = ("." * level if level else "") + cxt.module if level else ""

                spec = importlib.util.find_spec(_from, package=package) if _from else importlib.util.find_spec(package)
                module_name = spec.name
                class_name = name.name.split(".")[-1]

                fullname = ".".join([module_name, class_name]) if isinstance(cxt, ast.ImportFrom) else module_name
                asname = name.asname if name.asname else name.name

                logger.debug(f"Import {fullname} as {asname} => {mod.__name__}")

                registered_name = REGISTERED_MODULE + "." + fullname
                try:
                    rgz_clz = importlib.import_module(registered_name)
                except (ModuleNotFoundError, ImportError):
                    rgz_clz = (
                        create_registered_class(name=fullname)
                        if isinstance(cxt, ast.ImportFrom)
                        else create_registered_module(module_name)
                    )

                old_mod = mod
                for mod_name in asname.split(".")[:-1]:
                    new_mod = types.ModuleType(mod_name)
                    old_mod.__setattr__(mod_name, new_mod)
                    old_mod = new_mod
                old_mod.__setattr__(asname.rsplit(".", maxsplit=1)[-1], rgz_clz)
        return True
