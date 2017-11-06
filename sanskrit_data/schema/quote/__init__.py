import logging
import sys

from sanskrit_data.schema import common
from sanskrit_data.schema.common import TYPE_FIELD, JsonObject, Text


class QuoteText(JsonObject):
  schema = common.recursively_merge_json_schemas(JsonObject.schema, ({
    "type": "object",
    "description": "Quote details.",
    "properties": {
      TYPE_FIELD: {
        "enum": ["QuoteText"]
      },
      "text": {
        "type": Text.schema
      },
      "metre": {
        "type": "string"
      }
    }
  }))


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)
