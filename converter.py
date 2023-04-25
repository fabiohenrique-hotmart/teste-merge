#!/usr/bin/env python

"""
Convert Heimdall-Org yaml files to json

run: 
    # go to "Heimdall-Org repository"
    docker run --rm --name converter$(date +"%Y_%m_%d_%H_%M_%S") \
        --mount type=bind,src="$(pwd)",dst=/tmp/converter -w /tmp/converter \
            -it public.ecr.aws/hotmart/pipeline-utils \
                python /tmp/converter/scripts/converter.py
output example: 
    dist/unit=Hotmart/division=Technology/vertical=Infrastructure & Cloud/team=DevOps/IAC.json
"""

import importlib
import logging
import sys
from json import dumps as json_dumps
from pathlib import Path
from datetime import date

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)


def error_handler(tp, exception, tb):
    logging.exception(exception)
    exit(-1)


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

    for unit_path in Path(".").glob("unit=*/**/[!(system_|team_|vertical_|division_|unit_)]*.yaml"):
        dist_dir = Path(f"dist/window={date.today().isoformat()}", unit_path.parent)
        dist_dir.mkdir(parents=True, exist_ok=True)
        dist_dir = dist_dir.joinpath(f"{unit_path.stem}.json")
        with unit_path.open(mode="r") as fp:
            json_output = yaml.safe_load(fp)
        with dist_dir.open(mode="w+"):
            dist_dir.write_text(json_dumps(json_output))
            logging.info(dist_dir)


sys.excepthook = error_handler

if __name__ == "__main__":
    main()
    exit(0)