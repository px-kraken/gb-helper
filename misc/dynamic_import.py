import os
import importlib


def modules(package):
    package_name = package.__name__
    package_path = package.__path__[0]

    print(f"Package name: {package_name}")
    print(f"Package path: {package_path}")

    py_files = [f for f in os.listdir(package_path) if f.endswith('.py') and f != '__init__.py']

    imported_modules = {}

    for py_file in py_files:
        module_name = py_file[:-3]  # Strip .py extension
        full_module_name = f"{package_name}.{module_name}"
        print(f"Importing module: {full_module_name}")

        try:
            imported_modules[module_name] = importlib.import_module(full_module_name)
            print(f"Successfully imported {full_module_name}")
        except ImportError as e:
            print(f"Failed to import {full_module_name}: {e}")
        except Exception as e:
            print(f"Unexpected error importing {full_module_name}: {e}")

    return imported_modules
