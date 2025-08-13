JSON_SCHEMA_STR = """
{
    "$schema": "http://json-schema.org/schema#",
    "additionalProperties": false,
    "type": "object",
    "properties": {
        "processing_info": {
            "type": "object",
            "properties": {
                "search_column": {
                    "type": "string"
                },
                "tags_column": {
                    "type": "string"
                },
                "overwrite_tags_column": {
                    "type": "string"
                },
                "process_logging": {
                    "type": "string"
                }
            },
            "required": [
                "overwrite_tags_column",
                "process_logging",
                "search_column",
                "tags_column"
            ]
        },
        "tag_terms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string"
                    },
                    "terms": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": [
                    "tag",
                    "terms"
                ]
            }
        }
    },
    "required": [
        "processing_info",
        "tag_terms"
    ]
}
"""
