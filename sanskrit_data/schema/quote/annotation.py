import logging
import sys

from sanskrit_data.schema import common
from sanskrit_data.schema.common import TYPE_FIELD, JsonObject, Text, recursively_merge


class Rating(JsonObject):
  schema = recursively_merge(JsonObject.schema, ({
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "enum": ["Language"]
      },
      "rating": {
        "type": "integer",
      }
    },
    "required": ["rating"]
  }))

  @classmethod
  def from_details(cls, rating):
    obj = Rating()
    obj.rating = rating
    return obj


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)
