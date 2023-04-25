import yaml
import json
import requests
import jsonschema
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from jsonschema import RefResolver, Draft7Validator


class SchemaMeta(ABC):
    @abstractmethod
    def schema(self):
        ...


class SchemaBase(SchemaMeta):
    def __init__(self, url: str = ""):
        self.url = url

    def schema(self):
        src = requests.get(self.url).text
        return json.loads(src)


class UserV1alpha1(SchemaMeta):
    _url = "https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/kinds/User.v1alpha1.schema.json"

    def schema(self):
        src = requests.get(self._url).text
        data = json.loads(src)
        data["allOf"][1]["properties"]["spec"]["required"].append("profile")
        data["allOf"][1]["properties"]["spec"]["properties"]["profile"]["required"] = [
            "displayName",
            "email"
        ]
        return data


@lru_cache()
def get_schemas():
    schemas = {}
    schemas["EntityMeta"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/EntityMeta.schema.json"
    ).schema()
    schemas["EntityEnvelope"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/EntityEnvelope.schema.json"
    ).schema()
    schemas["Entity"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/Entity.schema.json"
    ).schema()
    schemas["common"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/shared/common.schema.json"
    ).schema()
    schemas["ApiV1alpha1"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/kinds/API.v1alpha1.schema.json"
    ).schema()
    schemas["SystemV1alpha1"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/kinds/System.v1alpha1.schema.json"
    ).schema()
    schemas["ResourceV1alpha1"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/kinds/Resource.v1alpha1.schema.json"
    ).schema()
    schemas["LocationV1alpha1"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/kinds/Location.v1alpha1.schema.json"
    ).schema()
    schemas["GroupV1alpha1"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/kinds/Group.v1alpha1.schema.json"
    ).schema()
    schemas["DomainV1alpha1"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/kinds/Domain.v1alpha1.schema.json"
    ).schema()
    schemas["ComponentV1alpha1"] = SchemaBase(
        url="https://raw.githubusercontent.com/backstage/backstage/master/packages/catalog-model/src/schema/kinds/Component.v1alpha1.schema.json"
    ).schema()
    schemas["UserV1alpha1"] = UserV1alpha1().schema()

    return schemas


@lru_cache()
def get_resolver(id_object, id_schema="EntityMeta"):
    schemas = get_schemas()
    resolver = RefResolver.from_schema(schemas[id_schema], store=schemas)

    return Draft7Validator(schemas[id_object], resolver=resolver)


def validate_object(id_object, object, id_schema="EntityMeta"):
    schemas_id = {
        "Envelope": "EntityEnvelope",
        "Entity": "Entity",
        "common": "common",
        "Api": "ApiV1alpha1",
        "System": "SystemV1alpha1",
        "Resource": "ResourceV1alpha1",
        "Location": "LocationV1alpha1",
        "Group": "GroupV1alpha1",
        "Domain": "DomainV1alpha1",
        "Component": "ComponentV1alpha1",
        "User": "UserV1alpha1",
    }
    validator = get_resolver(id_object=schemas_id[id_object])
    validator.validate(object)


if __name__ == "__main__":
    errs = []

    for unit_path in Path(__file__).parent.parent.glob("unit=*/**/*.yaml"):
        with unit_path.open(mode="r") as fp:
            json_output = yaml.safe_load_all(fp)
            for i in json_output:
                if i is not None:
                    kind = i.get("kind")
                    if kind:
                        try:
                            validate_object(id_object=kind, object=i)
                        except jsonschema.exceptions.ValidationError as err:
                            errs.append({"file": str(unit_path), "errs": str(err)})

    for i in errs:
        print(f"::error::Parsing schema {i['file']} {i['errs']}")

    if errs:
        exit(1)

    exit(0)
