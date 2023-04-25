#!/usr/bin/env python

"""
Convert .heimdall yaml files to Backstage catalog yaml
"""

import importlib
import logging
import sys
import os
import unicodedata
from os.path import exists
import pathlib
import subprocess
import re

logging.basicConfig(format="[backstage] %(levelname)s[%(asctime)s] %(message)s", level=logging.INFO, datefmt='%Y-%m-%dT%H:%M:%S%Z:00')

def error_handler(tp, exception, tb):
    logging.exception(exception)
    exit(-1)

def import_lib(pkg):
    try:
        importlib.import_module(pkg)
    except ImportError:
        logging.exception("pip intall %s", pkg)
        import pip
        pip.main(["install", pkg])
    finally:
        logging.debug("import %s", pkg)
        return importlib.import_module(pkg)

def main():
    yaml = import_lib("yaml")
    requests = import_lib("requests")

    repository = os.path.splitext(os.path.basename(subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).decode('ascii').strip()))[0]
    catalog = "catalog-info.yaml"
    heimdall = ".heimdall"

    logging.info("Workdir %s", pathlib.Path().resolve())

    catalog_exists = exists("catalog-info.yaml")
    if catalog_exists:
        logging.info("catalog already exists")
        exit(0)

    heimdall_exists = exists(".heimdall")
    if not heimdall_exists:
        logging.info(".heimdall not exists")
        exit(0)

    with open(heimdall, "r") as stream:
        heimdall_yaml = yaml.safe_load(stream)

        product = heimdall_yaml["products"][0]
        name = build_name(product)
        try:
            url = f"https://backstage.buildstaging.com/api/catalog/entities/by-name/system/default/{name}"
            response = requests.get(url = url)
            response.raise_for_status()
            system = response.json()
        except requests.exceptions.RequestException:
            logging.error("System not found: %s", name)
            owner = "hotmart"

        catalog_yaml = build_component(
            repository, 
            heimdall_yaml["description"],
            system["spec"]["owner"],
            system["metadata"]["name"],
            heimdall_yaml["reportable"],
            heimdall_yaml["pci"],
            heimdall_yaml["impact"],
            heimdall_yaml["products"],
            heimdall_yaml["squads"]
        )

        with open(catalog, 'w') as stream:
            yaml.dump(catalog_yaml, stream, sort_keys=False)

        with open('/Users/diego.ribeiro/hotmart/devops/heimdall-org/dist/all-hotmart-components.yaml', 'a') as all_components:
            all_components.write(yaml.dump(catalog_yaml, sort_keys=False))
            all_components.write('\n---\n')


def strip_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if unicodedata.category(c) != 'Mn')

def build_name(name):
    return strip_accents(name).strip().lower().translate({ord(c): "_" for c in "!@#$%^*()[]{};:,./<>?\|`~-=+ "}).translate({ord(c): "and" for c in "&"})

def build_component(name, description, owner, system, reportable, pci, impact, products, squads):
    type = "service"
    app = "^(app-.*|.*-app|.*-web|wp-.*)$"
    lib = "^(.*-starter|.*-lib|lib-.*|.*-util[s]?|.*-vo|.*-entity|ingest-.*|datahub-event-agent.*|cosmos|hot-integration|hot-observability)$"

    if re.match(app, name):
        type = "website"
    elif re.match(lib, name):
        type = "library"

    return {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "Component",
        "metadata": {
            "name": name,
            "description": description or "",
            "tags": [],
            "annotations": {
                "github.com/project-slug": f"Hotmart-Org/{name}"
            }
        },
        "spec": {
            "type": type,
            "lifecycle": "production",
            "owner": owner,
            "system": system,
            "heimdall": {
                "reportable": reportable,
                "pci": pci,
                "products": products,
                "squads": squads,
                "impact": impact or ""
            }
        }
    }

sys.excepthook = error_handler

if __name__ == "__main__":
    main()
    exit(0)
