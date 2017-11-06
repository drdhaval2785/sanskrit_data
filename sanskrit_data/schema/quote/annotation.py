import logging
import sys

from sanskrit_data.schema import common
from sanskrit_data.schema.common import TYPE_FIELD, JsonObject, Text, recursively_merge_json_schemas



# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)
