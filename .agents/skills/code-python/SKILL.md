---
name: code-python
description: Provides directives for generating and modifying Python code.
---

# Code Python

## Goal

Produce correct, secure, and maintainable Python solutions that match the user's constraints. This includes coding style, documentation style, coding practices, and tool usage, as described in the following sections.

---

## When to use this skill

Use this when writing, modifying, and reviewing Python code. Do not use this skill for other programming languages, unless the user makes reference to some Python guideline.

---

## How to use this skill

Consistently apply the same code style across all modifications. All code is expected to be enterprise-level, so no "hacky" solutions, no "quick fixes", no "workarounds", no "temporary scripts", and naming conventions must be consistent with the existing codebase. Once a task is finished, update the CHANGELOG accordingly.

---

## Code style

- Modules must always start with a line containing `# -*- coding: utf-8 -*-` and be written with Unix-style `LF` line endings.

- Use PEP8 for style guidelines, unless the user explicitly requests otherwise or manually modifies the code for readability. Code line should be wrapped in an 80–character limit. What follows in this skill overrides PEP8 when in conflict.

- Prefer classes over functions in modules. Keep function usage limited to simple wrappers or "glue" code between classes. Sometimes functions can be useful for workflow (setup of complex classes or group of classes). Functions are required when their intent is to be the entrypoint of an application.

- Whenever the context allows for (including the whole project use cases), type hints must be used for all exposed functions.

- Never use type hints for private class methods. Module private functions should follow the general rule if they are complex functions, but simple wrappers can ommit type hints if their intent is obvious.

    ```python
    def some_function(arg1: Any, arg2: Any, arg3: Any) -> Any:
        ...


    def _module_private_function1(arg1, arg2):
        ...


    def _module_private_function2(arg1: Any, arg2: Any) - Any:
        ...


    class SomeClass:
        def __init__(self, arg1: Any, arg2: Any) -> None:
            ...

        def _private_method(self, arg1, arg2):
            ...

        def some_method(self, arg1: Any, arg2: Any) -> Any:
            ...
    ```

- If arguments list (typed) and return type hint fit on one line, the function definition must be on one line, as follows:

    ```python
    def some_function(arg1: Any, arg2: Any, arg3: Any) -> Any:
        ...

    class SomeClass:
        def __init__(self, arg1: Any, arg2: Any) -> None:
            ...

        def some_method(self, arg1: Any, arg2: Any) -> Any:
            ...

        @classmethod
        def some_method(cls, arg1: Any, arg2: Any) -> Any:
            ...

        @staticmethod
        def some_static_method(arg1: Any, arg2: Any) -> Any:
            ...

        @property
        def some_property(self) -> Any:
            ...
    ```

- If arguments list (typed) and return type hint do not fit on one line, the function definition must be on multiple lines, as follows. Please notice that the arguments have one extra indentation level than the closing parenthesis:

    ```python
    def some_function(
            arg1: Any,
            arg2: Any,
            arg3: Any,
            arg4: Any,
            arg5: Any,
            arg6: Any,
            arg7: Any
        ) -> Self:
        ...

    class SomeClass:
        def __init__(
            self,
            arg1: Any,
            arg2: Any,
            arg3: Any,
            arg4: Any,
            arg5: Any,
            arg6: Any,
            arg7: Any
        ) -> None:
            ...
    ```

- There must be a blanck line before flow control statements like `if`, `match`, `for`, `while`, except when they are nested inside another flow control statement, as for example:

    ```python
    a = 1

    if a == 2:
        print("a is 2")

    list_y = []

    for x in [1, 2, 3]:
        if x > 1:
            list_y.append(x + 1)

        match x:
            case 1:
                print("1")
            case _:
                print("Not 1")

    list_z = [x + 1 for x in [1, 2, 3] if x > 1]
    ```

---

## Documentation style

- Docstring lines must be wrapped in an 68–character limit.

- Functions and methods must be documented using docstrings. The summary line in the docstring should be on the same line as `"""` and there must be at one whitespace character between the `"""` and the summary text. Summary text must be a one line description of the function or method, in imperative mood.

    ```python
    def example_function() -> None:
        """ One-line summary of the function. """
        ...
    ```

- Docstrings should be in Numpydoc format with a few overrides:
    - The summary is mandatory and must be formatted as described above.
    - The extended summary is never written by the agent, it is up to the user to add it if needed.
    - Parameters are mandatory but do not follow strict Numpydoc style, with default values being shown in the annotation, as illustrated below.
    - Returns section is mandatory and must be formatted as described below.
    - Any other section is optional and must be added only if explicitly requested by the user.

    ```python
    def example_function(a: float, b: bool = True) -> str:
        """ One-line summary of the function.

        Extended summary...

        Parameters
        ----------
        a : float
            Description of a.
        b : bool = True
            Description of b.

        Returns
        -------
        str
            Description of the return value.
        """
        ...
    ```

- Class initialization `__init__` docstring must be included in the class docstring as usually done (not inside the function itself). The docstring of the methods must be in the methods themselves.

    ```python
    class ExampleClass:
        """ One-line summary of the class.

        Extended summary...

        Parameters
        ----------
        a : float
            Description of a.
        b : bool = True
            Description of b.

        Returns
        -------
        str
            Description of the return value.
        """
        def __init__(self, a: float, b: bool = True) -> None:
            # XXX no documentation here, this is intentional
            ...
    ```

- No *dunder* method must be directly documented (e.g. `__str__`, `__repr__`, `__eq__`, `__ne__`, `__lt__`, `__le__`, `__gt__`, `__ge__`, ...) except for the function object `__call__`.

## Coding practices

- Classes use `__slots__` to reduce memory usage and make sure no attribute is missing or created on the fly.
- Only use `pathlib` for path management, never `os.path`.

- Always use `tomlib` to read pyproject.toml or any TOML file.

- Do not implement tests, unless the user explicitly asks for it.

- Do not try to keep things backward compatible, unless the user explicitly asks for it.

---

## Tool usage

- Packages are managed with `uv`. `uv` will be used to manage dependencies, install packages, and create virtual environments. No other tools are allowed unless explicitly requested by the user.

---

## Scripts guidelines

Scripts outside packages (e.g. example code, auxiliary scripts) are not meant to be type-annotated. Also, documentation of scripts is limited to the summary line of a docstring.