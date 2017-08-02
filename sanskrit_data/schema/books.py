"""
Intro
-----------

Here we define data-containers to store books. Books are stored or represented as a tree of BookPortion objects - book
containing many chapters containing many lines etc..

-  JSON schema mindmap
   `here <https://drive.mindmup.com/map?state=%7B%22ids%22:%5B%220B1_QBT-hoqqVbHc4QTV3Q2hjdTQ%22%5D,%22action%22:%22open%22,%22userId%22:%22109000762913288837175%22%7D>`__
   (Updated as needed).

"""
import logging
import sys

from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObjectWithTarget, TextContent, TYPE_FIELD, JsonObject, Target


class BookPositionTarget(Target):
  schema = common.recursively_merge(Target.schema, {
    "type": "object",
    "description": "A BookPortion could represent a Book or a chapter or a verse or a half-verse or a sentence or any such unit.",
    "properties": {
      TYPE_FIELD: {
        "enum": ["BookPositionTarget"]
      },
      "position": {
        "type": "number",
        "description": "Any number describing the position of one BookPortion within another."
      }
    }
    })

  @classmethod
  def from_details(cls, container_id=None, position=None):
    target = BookPositionTarget()
    if container_id:
      target.container_id = container_id
    if position:
      target.position = position
    target.validate(db_interface=None)
    return target


class BookPortion(JsonObjectWithTarget):
  schema = common.recursively_merge(JsonObject.schema, ({
    "type": "object",
    "description": "A BookPortion could represent a Book or a chapter or a verse or a half-verse or a sentence or any such unit.",
    "properties": {
      TYPE_FIELD: {
        "enum": ["BookPortion"]
      },
      "title": {
        "type": "string"
      },
      "path": {
        "type": "string"
      },
      "authors": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "base_data": {
        "type": "string",
        "enum": ["image", "text"]
      },
      "portion_class": {
        "type": "string",
        "description": "book, part, chapter, verse, line etc.."
      },
      "curated_content": TextContent.schema,
      "targets": {
        "maxLength": 1,
        "items": BookPositionTarget.schema,
        "description": "Target for BookPortion of which this BookPortion is a part. It is an array only for consistency. "
                       "For any given BookPortion, one can get the right order of contained BookPortions by seeking all "
                       "BookPortions referring to it in the targets list, and sorting them by their target position values."
      }
    },
  }))

  target_class = BookPositionTarget

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion]

  @classmethod
  def from_details(cls, title, path=None, authors=None, targets=None, base_data = None,
                   curated_content=None, portion_class=None):
    if authors is None:
      authors = []
    book_portion = BookPortion()
    book_portion.title = title
    book_portion.authors = authors
    # logging.debug(str(book_portion))
    if path:
      book_portion.path = path

    targets = targets or []
    logging.debug(str(book_portion))
    book_portion.targets = targets
    if curated_content != None:
      book_portion.curated_content = curated_content
    if base_data != None:
      book_portion.base_data = base_data
    if portion_class != None:
      book_portion.portion_class = portion_class
    book_portion.validate()
    return book_portion

  @classmethod
  def from_path(cls, path, db_interface):
    book_portion_dict = db_interface.find_one(filter={"path": path})
    if book_portion_dict == None:
      return None
    else:
      book_portion = JsonObject.make_from_dict(book_portion_dict)
      return book_portion

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)
