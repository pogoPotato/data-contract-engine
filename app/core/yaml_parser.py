import yaml
import re
import logging
from typing import Dict, Any
from app.models.schemas import ContractSchema, FieldDefinition


logger = logging.getLogger(__name__)


class YAMLParserError(Exception):
    pass


class YAMLSyntaxError(YAMLParserError):
    pass


class MissingRequiredKeyError(YAMLParserError):
    pass


class InvalidSchemaError(YAMLParserError):
    pass


class YAMLParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_yaml(self, yaml_content: str) -> ContractSchema:
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise YAMLSyntaxError(f"Invalid YAML syntax: {str(e)}")

        if not isinstance(data, dict):
            raise YAMLSyntaxError("YAML must be a dictionary/object")

        required_keys = ["contract_version", "schema"]
        for key in required_keys:
            if key not in data:
                raise MissingRequiredKeyError(
                    f"Missing required key: '{key}'. "
                    f"Contract must include: {', '.join(required_keys)}"
                )

        try:
            schema_fields = self._parse_schema(data["schema"])
        except Exception as e:
            raise InvalidSchemaError(f"Invalid schema definition: {str(e)}")

        quality_rules = None
        if "quality_rules" in data:
            try:
                quality_rules = self.validate_quality_rules(data["quality_rules"])
            except Exception as e:
                self.logger.warning(f"Invalid quality rules: {str(e)}")
                quality_rules = None

        try:
            contract_schema = ContractSchema(
                contract_version=data["contract_version"],
                domain=data.get("domain", "default"),
                description=data.get("description"),
                schema=schema_fields,
                quality_rules=quality_rules,
            )
        except Exception as e:
            raise InvalidSchemaError(f"Failed to create contract schema: {str(e)}")

        self.logger.info(
            f"Successfully parsed contract with {len(schema_fields)} fields"
        )
        return contract_schema

    def _parse_schema(self, schema_dict: Dict[str, Any]) -> Dict[str, FieldDefinition]:
        if not isinstance(schema_dict, dict):
            raise InvalidSchemaError("Schema must be a dictionary")

        if not schema_dict:
            raise InvalidSchemaError("Schema must contain at least one field")

        parsed_fields = {}

        for field_name, field_spec in schema_dict.items():
            if not isinstance(field_spec, dict):
                raise InvalidSchemaError(
                    f"Field '{field_name}' specification must be a dictionary"
                )

            try:
                field_def = self.validate_field_definition(field_name, field_spec)
                parsed_fields[field_name] = field_def
            except Exception as e:
                raise InvalidSchemaError(
                    f"Invalid field definition for '{field_name}': {str(e)}"
                )

        return parsed_fields

    def validate_field_definition(
        self, field_name: str, field_def: Dict[str, Any]
    ) -> FieldDefinition:
        if "type" not in field_def:
            raise InvalidSchemaError(f"Field '{field_name}' must specify 'type'")

        field_type = field_def["type"]

        allowed_types = [
            "string",
            "integer",
            "float",
            "boolean",
            "timestamp",
            "date",
            "array",
            "object",
        ]
        if field_type not in allowed_types:
            raise InvalidSchemaError(
                f"Invalid type '{field_type}' for field '{field_name}'. "
                f"Must be one of: {', '.join(allowed_types)}"
            )

        pattern = field_def.get("pattern")
        if pattern:
            try:
                re.compile(pattern)
            except re.error as e:
                raise InvalidSchemaError(
                    f"Invalid regex pattern for field '{field_name}': {str(e)}"
                )

        format_type = field_def.get("format")
        if format_type:
            allowed_formats = ["email", "url", "uuid", "ipv4"]
            if format_type not in allowed_formats:
                raise InvalidSchemaError(
                    f"Invalid format '{format_type}' for field '{field_name}'. "
                    f"Must be one of: {', '.join(allowed_formats)}"
                )

        min_val = field_def.get("min")
        max_val = field_def.get("max")
        if min_val is not None and max_val is not None:
            if min_val > max_val:
                raise InvalidSchemaError(
                    f"Field '{field_name}': min ({min_val}) must be <= max ({max_val})"
                )

        min_length = field_def.get("min_length")
        max_length = field_def.get("max_length")
        if min_length is not None and max_length is not None:
            if min_length > max_length:
                raise InvalidSchemaError(
                    f"Field '{field_name}': min_length must be <= max_length"
                )

        items = None
        if field_type == "array":
            if "items" not in field_def:
                raise InvalidSchemaError(
                    f"Array field '{field_name}' must specify 'items'"
                )
            items = self.validate_field_definition(
                f"{field_name}[]", field_def["items"]
            )

        properties = None
        if field_type == "object":
            if "properties" not in field_def:
                raise InvalidSchemaError(
                    f"Object field '{field_name}' must specify 'properties'"
                )
            properties = {}
            for prop_name, prop_def in field_def["properties"].items():
                properties[prop_name] = self.validate_field_definition(
                    f"{field_name}.{prop_name}", prop_def
                )

        field_definition = FieldDefinition(
            type=field_type,
            required=field_def.get("required", True),
            pattern=pattern,
            format=format_type,
            min=min_val,
            max=max_val,
            min_length=min_length,
            max_length=max_length,
            description=field_def.get("description"),
            enum=field_def.get("enum"),
            items=items,
            properties=properties,
        )

        return field_definition

    def validate_quality_rules(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(rules, dict):
            raise InvalidSchemaError("Quality rules must be a dictionary")

        validated_rules = {}

        if "freshness" in rules:
            freshness = rules["freshness"]
            if not isinstance(freshness, dict):
                raise InvalidSchemaError("Freshness rule must be a dictionary")

            if "max_latency_hours" not in freshness:
                raise InvalidSchemaError(
                    "Freshness rule must specify 'max_latency_hours'"
                )

            max_hours = freshness["max_latency_hours"]
            if not isinstance(max_hours, (int, float)) or max_hours <= 0:
                raise InvalidSchemaError("max_latency_hours must be a positive number")

            validated_rules["freshness"] = freshness

        if "completeness" in rules:
            completeness = rules["completeness"]
            if not isinstance(completeness, dict):
                raise InvalidSchemaError("Completeness rule must be a dictionary")

            if "min_row_count" in completeness:
                min_rows = completeness["min_row_count"]
                if not isinstance(min_rows, int) or min_rows < 0:
                    raise InvalidSchemaError(
                        "min_row_count must be a non-negative integer"
                    )

            if "max_null_percentage" in completeness:
                max_null = completeness["max_null_percentage"]
                if not isinstance(max_null, (int, float)) or not (0 <= max_null <= 100):
                    raise InvalidSchemaError(
                        "max_null_percentage must be between 0 and 100"
                    )

            validated_rules["completeness"] = completeness

        if "uniqueness" in rules:
            uniqueness = rules["uniqueness"]
            if not isinstance(uniqueness, dict):
                raise InvalidSchemaError("Uniqueness rule must be a dictionary")

            if "fields" not in uniqueness:
                raise InvalidSchemaError("Uniqueness rule must specify 'fields'")

            fields = uniqueness["fields"]
            if not isinstance(fields, list) or not fields:
                raise InvalidSchemaError("Uniqueness fields must be a non-empty list")

            validated_rules["uniqueness"] = uniqueness

        if "statistics" in rules:
            statistics = rules["statistics"]
            if not isinstance(statistics, dict):
                raise InvalidSchemaError("Statistics rule must be a dictionary")

            for field_name, constraints in statistics.items():
                if not isinstance(constraints, dict):
                    raise InvalidSchemaError(
                        f"Statistics for field '{field_name}' must be a dictionary"
                    )

            validated_rules["statistics"] = statistics

        return validated_rules

    def serialize_to_yaml(self, contract_schema: ContractSchema) -> str:
        data = {
            "contract_version": contract_schema.contract_version,
            "domain": contract_schema.domain,
        }

        if contract_schema.description:
            data["description"] = contract_schema.description

        schema_dict = {}
        for field_name, field_def in contract_schema.schema.items():
            schema_dict[field_name] = self._field_definition_to_dict(field_def)

        data["schema"] = schema_dict

        if contract_schema.quality_rules:
            data["quality_rules"] = contract_schema.quality_rules

        yaml_str = yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
            allow_unicode=True,
        )

        return yaml_str

    def _field_definition_to_dict(self, field_def: FieldDefinition) -> Dict[str, Any]:
        result = {"type": field_def.type, "required": field_def.required}

        if field_def.pattern:
            result["pattern"] = field_def.pattern

        if field_def.format:
            result["format"] = field_def.format

        if field_def.min is not None:
            result["min"] = field_def.min

        if field_def.max is not None:
            result["max"] = field_def.max

        if field_def.min_length is not None:
            result["min_length"] = field_def.min_length

        if field_def.max_length is not None:
            result["max_length"] = field_def.max_length

        if field_def.description:
            result["description"] = field_def.description

        if field_def.enum:
            result["enum"] = field_def.enum

        if field_def.items:
            result["items"] = self._field_definition_to_dict(field_def.items)

        if field_def.properties:
            properties = {}
            for prop_name, prop_def in field_def.properties.items():
                properties[prop_name] = self._field_definition_to_dict(prop_def)
            result["properties"] = properties

        return result
