INTENT_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "entity": {
            "type": "STRING",
            "nullable": True,
        },
        "filters": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "column": {
                        "type": "STRING",
                    },
                    "operator": {
                        "type": "STRING",
                    },
                    "value": {
                        "type": "STRING",
                    },
                },
                "required": [
                    "column",
                    "operator",
                    "value",
                ],
            },
        },
        "metric": {
            "type": "STRING",
            "nullable": True,
        },
        "aggregation": {
            "type": "STRING",
            "nullable": True,
        },
        "sort_direction": {
            "type": "STRING",
            "nullable": True,
        },
        "limit": {
            "type": "INTEGER",
            "nullable": True,
        },
    },
    "required": [
        "entity",
        "filters",
        "metric",
        "aggregation",
        "sort_direction",
        "limit",
    ],
}