from pathlib import Path
import os
import ast
import subprocess
import argparse

raise NotImplementedError("This script is not yet ready for use")

# Globals
TUDATPY_ROOT = Path(__file__).parent / "src/tudatpy"
STUBS_ROOT = Path(__file__).parent / "src/tudatpy-stubs"
PREFIX = Path(os.environ["CONDA_PREFIX"]).resolve()


class BuildParser(argparse.ArgumentParser):
    """Argument parser for stub generation script"""

    def __init__(self) -> None:

        super().__init__(prog="stubs.py", description="Generate tudatpy stubs")

        self.add_argument(
            "--clean",
            action="store_true",
            help="Regenerate stubs from scratch",
        )

        self.add_argument(
            "--module",
            metavar="<module>",
            type=str,
            help="Generate stubs for a specific module",
        )

        return None


class StubGenerator:
    """Stub generation"""

    def __init__(self, clean: bool = False) -> None:
        self.clean = clean
        return None

    def generate_stubs(self, source_dir: Path) -> None:
        """Generates stubs for a package.

        :param source_dir: Path to base directory of the package
        """

        # Generate stub for main init file
        StubGenerator._generate_init_stub(source_dir)

        # Generate stubs for C++ extensions
        for extension in source_dir.rglob("*.so"):

            # Skip extension if stub exists and clean flag is not set
            extension_stub_path = STUBS_ROOT / extension.relative_to(
                TUDATPY_ROOT
            ).with_suffix("").with_suffix(".pyi")
            if extension_stub_path.exists() and not self.clean:
                continue

            # Generate stub
            extension_import_path = f"tudatpy.{str(extension.relative_to(TUDATPY_ROOT).with_suffix('').with_suffix('')).replace('/', '.')}"
            print(f"Generating stubs for {extension_import_path}...")
            outcome = subprocess.run(
                [
                    "pybind11-stubgen",
                    extension_import_path,
                    "-o",
                    ".",
                    "--root-suffix=-stubs",
                    "--numpy-array-remove-parameters",
                ]
            )
            if outcome.returncode:
                exit(outcome.returncode)

            # Clean autogenerated stub
            self._clean_autogenerated_stub(extension_import_path)

        # Loop over submodules
        for submodule in source_dir.iterdir():
            if submodule.is_dir() and (submodule / "__init__.py").exists():
                self._generate_module_stubs(submodule)

        return None

    def _generate_module_stubs(self, module_path: Path) -> None:
        """Generates stubs for a module

        :param module_path: Path to module directory
        """

        # Loop over submodules
        for submodule in module_path.iterdir():
            if submodule.is_dir() and (submodule / "__init__.py").exists():
                self._generate_module_stubs(submodule)

        # Define import path and display info
        import_path = (
            f'tudatpy.{str(module_path.relative_to(TUDATPY_ROOT)).replace("/", ".")}'
        )

        # Generate __init__ stub
        StubGenerator._generate_init_stub(module_path)

        # Find python scripts included in __init__
        with open(module_path / "__init__.py") as _f:
            _content = ast.parse(_f.read())

        _python_modules = []
        for _statement in _content.body:
            if isinstance(_statement, ast.ImportFrom):
                if "expose" in str(_statement.module) or _statement.module is None:
                    continue
                _python_modules.append(_statement.module)

        # Generate stubs for python scripts
        for _python_module in _python_modules:

            # Skip extension if stub exists and clean flag is not set
            script_import_path = f"{import_path}.{_python_module}"
            script_stub_path = STUBS_ROOT / Path(
                "/".join(script_import_path.split(".")[1:])
            ).with_suffix(".pyi")
            if script_stub_path.exists() and not self.clean:
                continue
            print(f"Generating stub for {script_import_path}...")
            outcome = subprocess.run(
                [
                    "pybind11-stubgen",
                    script_import_path,
                    "-o",
                    ".",
                    "--root-suffix=-stubs",
                    "--numpy-array-remove-parameters",
                ]
            )
            if outcome.returncode:
                exit(outcome.returncode)

            # Clean autogenerated stub
            self._clean_autogenerated_stub(script_import_path)

        return None

    @staticmethod
    def _adjust_docstring_indentation(text):

        # Replace tabs with character not affected by strip
        text = text.replace("    ", "¿")

        # Split input into lines and remove leading/trailing whitespace
        lines = [line.strip() for line in text.splitlines()]
        while lines[0] == "":
            lines.pop(0)

        # Find indentation level of first line
        lev0 = len(lines[0].split("¿"))
        lev1 = lev0
        for line in lines[1:]:
            if line != "":
                lev1 = len(line.split("¿"))
                break
        diff = lev1 - lev0

        # Adjust indentation for all lines
        newlines = [lines[0].replace("¿", "")]
        for line in lines[1:]:
            terms = line.split("¿")[diff:]
            line = "\t".join(terms)
            newlines.append(("\t" * lev0) + line)

        return "\n".join(newlines) + "\n" + ("\t" * lev0)

    @staticmethod
    def _generate_init_stub(module_path: Path) -> None:
        """Generates stub for __init__ file

        :param module_path: Path to module directory
        """
        # Define path to stub file
        stub_path = module_path.relative_to(TUDATPY_ROOT)
        stub_path = STUBS_ROOT / f"{stub_path}/__init__.pyi"

        # Parse __init__ file
        with open(module_path / "__init__.py") as src:
            content = ast.parse(src.read())

        import_statements = []
        other_statements = []
        for statement in content.body:

            if isinstance(statement, ast.Import):
                raise NotImplementedError("Import statement not supported yet")
            elif isinstance(statement, ast.ImportFrom):
                if statement.names[0].name == "*":
                    assert statement.module is not None
                    with (
                        stub_path.parent / f"{statement.module.replace('.', '/')}.pyi"
                    ).open() as f:
                        _data = ast.parse(f.read())
                        for _statement in _data.body:
                            if (
                                isinstance(_statement, ast.Assign)
                                and len(_statement.targets) == 1
                                and isinstance(_statement.targets[0], ast.Name)
                                and _statement.targets[0].id == "__all__"
                            ):
                                assert isinstance(_statement.value, ast.List)
                                _equivalent_import = ast.ImportFrom(
                                    module=statement.module,
                                    level=statement.level,
                                    names=[
                                        ast.alias(name=elt.value)  # type: ignore
                                        for elt in _statement.value.elts
                                    ],
                                )
                                import_statements.append(_equivalent_import)
                else:
                    import_statements.append(statement)

            elif isinstance(statement, ast.Assign):
                if statement.targets[0].id == "__all__":  # type: ignore
                    continue
                other_statements.append(statement)

        # Generate import statement for submodules
        submodule_list = []
        for submodule in module_path.iterdir():
            if submodule.is_dir() and (submodule / "__init__.py").exists():
                submodule_list.append(submodule)

        if len(submodule_list) > 0:
            import_submodules_statement = ast.ImportFrom(
                module="",
                level=1,
                names=[ast.alias(name=submodule.name) for submodule in submodule_list],
            )
            import_statements.append(import_submodules_statement)

        # Generate __all__ statement
        if len(import_statements) == 0:
            all_statement = ast.parse("__all__ = []").body[0]
        else:
            all_statement = ast.parse(
                "__all__ = ["
                + ", ".join(
                    [
                        f"'{alias.name}'"
                        for statement in import_statements
                        for alias in statement.names
                    ]
                )
                + "]"
            ).body[0]

        # Generate __init__.pyi
        init_contents = import_statements + other_statements + [all_statement]
        init_module = ast.Module(body=init_contents, type_ignores=[])
        stub_path.parent.mkdir(parents=True, exist_ok=True)
        with open(stub_path, "w") as f:
            f.write(ast.unparse(init_module))

        return None

    @staticmethod
    def _clean_autogenerated_stub(import_path: str) -> None:
        """Cleans autogenerated stub

        :param import_path: Import path to module
        """

        stub_path = STUBS_ROOT / Path("/".join(import_path.split(".")[1:])).with_suffix(
            ".pyi"
        )

        with open(stub_path) as f:
            content = ast.parse(f.read())

        includes_typing = False
        for idx, statement in enumerate(content.body):

            if isinstance(statement, ast.ImportFrom):
                if statement.module == "__future__":
                    content.body.remove(statement)

            if isinstance(statement, ast.Import):
                for alias in statement.names:
                    if alias.name == "typing":
                        includes_typing = True
                        break

            if isinstance(
                statement,
                (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Module),
            ):
                _docstring = ast.get_docstring(statement, clean=True)
                if _docstring is not None:
                    _docstring = StubGenerator._adjust_docstring_indentation(_docstring)
                    statement.body.pop(0)
                    statement.body.insert(0, ast.Expr(ast.Constant(_docstring)))

        if not includes_typing:
            content.body.insert(0, ast.Import([ast.alias("typing")]))

        with open(stub_path, "w") as f:
            f.write(ast.unparse(content))

        return None


if __name__ == "__main__":

    args = BuildParser().parse_args()

    os.chdir("src")

    root = TUDATPY_ROOT
    # if args.module is not None:
    #     root = TUDATPY_ROOT / args.module.replace(".", "/")

    StubGenerator(clean=args.clean).generate_stubs(root)
