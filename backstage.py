#!/usr/bin/env python

"""
Convert Heimdall-Org yaml files to json
"""

import importlib
import logging
import sys
import os
import fnmatch
import random
import unicodedata
from json import dumps as json_dumps
from pathlib import Path
from datetime import date

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)

def error_handler(tp, exception, tb):
    logging.exception(exception)
    exit(-1)

includes = ['unit=*', 'division=*', 'vertical=*', 'team=*']
excludes = ['dist']

def main():
    pkg = "yaml"
    yaml = None
    try:
        importlib.import_module(pkg)
    except ImportError:
        logging.exception("pip intall %s", pkg)
        import pip

        pip.main(["install", pkg])
    finally:
        logging.info("import %s", pkg)

        yaml = importlib.import_module(pkg)

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in excludes]

        parent = ""
        if root != "." and os.path.dirname(root) != ".":
            basename = os.path.basename(os.path.dirname(root))
            parent = build_name(remove_all_prefix(basename)) + "_" + get_prefix(basename)


        path = os.path.basename(root)
        name = remove_all_prefix(path)

        locations = build_location(name)
        if path.startswith("unit="):
            entity = build_org(name)
        elif path.startswith("division="):
            entity = build_department(name, parent)
        elif path.startswith("vertical="):
            entity = build_sub_department(name, parent)
        elif path.startswith("team="):
            entity = build_team(name, parent)
        else:
            continue

        dist_dir = Path(f"dist/window={date.today().isoformat()}", root)
        dist_dir.mkdir(parents=True, exist_ok=True)

        for pattern in includes:
            for dir in fnmatch.filter(dirs, pattern):
                n = build_name(dir)
                locations["spec"]["targets"].append(f"./{dir}/{n}.yaml")

        if path.startswith("team="):
            locations["spec"]["targets"] = []

        for f in files:
            fname = build_name(os.path.splitext(f)[0])
            locations["spec"]["targets"].append(f"./system_{build_name(fname)}.yaml")
            with open(root + "/" + f, "r") as stream:
                old_yml = yaml.safe_load(stream)
                system = build_system(old_yml["name"], old_yml["description"], old_yml["auditable"], old_yml["coreBusiness"], entity["metadata"]["name"])
                system_dir = dist_dir.joinpath(f"system_{fname}.yaml")
                with open(system_dir, 'w') as stream:
                    yaml.dump(system, stream)

        entity_dir = dist_dir.joinpath(f"{build_name(path)}.yaml")
        logging.info(entity_dir)
        with open(entity_dir, 'w') as stream:
            yaml.dump_all([entity, locations], stream)

def remove_all_prefix(text):
    prefix = ['unit=', 'division=', 'vertical=', 'team=']
    final_text = text
    for p in prefix:
        final_text = remove_prefix(final_text, p)

    return final_text

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def get_prefix(text):
    if text.find("=") >= 0:
        return text[0:text.find("=")]
    return text

def strip_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if unicodedata.category(c) != 'Mn')

def build_name(name):
    return strip_accents(name).strip().lower().translate({ord(c): "_" for c in "!@#$%^*()[]{};:,./<>?\|`~-=+ "}).translate({ord(c): "and" for c in "&"})

def build_org(name):
    return {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "Group",
        "metadata": {
            "name": f"{build_name(name)}_unit"
        },
        "spec": {
            "type": "organization",
            "profile": {
                "displayName": name
            },
            "children": []
        }
    }

def build_department(name, parent):
    return {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "Group",
        "metadata": {
            "name": f"{build_name(name)}_division"
        },
        "spec": {
            "type": "department",
            "profile": {
                "displayName": name
            },
            "parent": parent,
            "children": []
        }
    }

def build_sub_department(name, parent):
    return {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "Group",
        "metadata": {
            "name": f"{build_name(name)}_vertical"
        },
        "spec": {
            "type": "sub-department",
            "profile": {
                "displayName": name
            },
            "parent": parent,
            "children": []
        }
    }

def build_team(name, parent):
    return {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "Group",
        "metadata": {
            "name": f"{build_name(name)}_team"
        },
        "spec": {
            "type": "team",
            "profile": {
                "displayName": name
            },
            "parent": parent,
            "children": []
        }
    }

def build_location(name):
    return {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "Location",
        "metadata": {
            "name": f"{build_name(name)}-{random.randint(0, 100)}-locations",
            "description": f"A collection of all {name} sub-groups"
        },
        "spec": {
            "targets": []
        }
    }

def build_system(name, description, auditable, core_business, owner):
    return {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "System",
        "metadata": {
            "name": build_name(name),
            "title": name,
            "description": description or ""
        },
        "spec": {
            "owner": owner,
            "domain": "hotmart",
            "auditable": auditable,
            "coreBusiness": core_business
        }
    }

sys.excepthook = error_handler

if __name__ == "__main__":
    main()
    exit(0)
