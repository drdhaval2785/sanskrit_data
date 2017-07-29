from __future__ import absolute_import

import json
import logging
import sys
from copy import deepcopy

import jsonpickle
import jsonschema

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

JSONPICKLE_TYPE_FIELD = "py/object"
TYPE_FIELD = "jsonClass"

# Updated using update_json_class_index() calls at the end of each submodule file (such as this one) in the parent module.
json_class_index = {}


def update_json_class_index(module_in):
  import inspect
  schemas = {}
  for name, obj in inspect.getmembers(module_in):
    if inspect.isclass(obj):
      json_class_index[name] = obj.__module__


def check_class(obj, allowed_types):
  results = [isinstance(obj, some_type) for some_type in allowed_types]
  # logging.debug(results)
  return (True in results)


def check_list_item_types(some_list, allowed_types):
  check_class_results = [check_class(item, allowed_types=allowed_types) for item in some_list]
  # logging.debug(check_class_results)
  return not (False in check_class_results)


def recursively_merge(a, b):
  assert a.__class__ == b.__class__, str(a.__class__) + " vs " + str(b.__class__)

  if isinstance(b, dict) and isinstance(a, dict):
    a_and_b = a.viewkeys() & b.viewkeys()
    every_key = a.viewkeys() | b.viewkeys()
    return {k: recursively_merge(a[k], b[k]) if k in a_and_b else
    deepcopy(a[k] if k in a else b[k]) for k in every_key}
  elif isinstance(b, list) and isinstance(a, list):
    return list(set(a + b))
  else:
    return b
  return deepcopy(b)


class JsonObject(object):
  schema = {
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "type": "string",
      },
    },
    "required": [TYPE_FIELD]
  }

  def __init__(self):
    self.set_type()

  @classmethod
  def make_from_dict(cls, input_dict):
    """Defines *our* canonical way of constructing a JSON object from a dict.
    
    All other deserialization methods should use this.
    Note that this assumes that json_class_index is populated properly!
    from sanskrit_data.schema import * before using this should take care of it.
    :param input_dict: 
    :return: 
    """
    if input_dict == None:
      return None
    assert input_dict.has_key(TYPE_FIELD), "no type field: " + str(input_dict)
    dict_without_id = deepcopy(input_dict)
    _id = dict_without_id.pop("_id", None)

    def recursively_set_jsonpickle_type(some_dict):
      wire_type = some_dict.pop(TYPE_FIELD, None)
      if wire_type:
        some_dict[JSONPICKLE_TYPE_FIELD] = json_class_index[wire_type] + "." + wire_type
      for key, value in some_dict.iteritems():
        if isinstance(value, dict):
          recursively_set_jsonpickle_type(value)
        elif isinstance(value, list):
          for item in value:
            if isinstance(item, dict):
              recursively_set_jsonpickle_type(item)

    recursively_set_jsonpickle_type(dict_without_id)

    new_obj = jsonpickle.decode(json.dumps(dict_without_id))
    # logging.debug(new_obj.__class__)
    if _id:
      new_obj._id = str(_id)
    new_obj.set_type_recursively()
    return new_obj

  @classmethod
  def make_from_dict_list(cls, input_dict_list):
    return [cls.make_from_dict(input_dict=input_dict) for input_dict in input_dict_list]

  @classmethod
  def make_from_pickledstring(cls, pickle):
    obj = cls.make_from_dict(jsonpickle.decode(pickle))
    return obj

  @classmethod
  def read_from_file(cls, filename):
    try:
      with open(filename) as fhandle:
        obj = cls.make_from_dict(jsonpickle.decode(fhandle.read()))
        return obj
    except Exception as e:
      raise e
      return logging.error("Error reading " + filename + " : ".format(e))

  def dump_to_file(self, filename):
    try:
      with open(filename, "w") as f:
        f.write(str(self))
    except Exception as e:
      return logging.error("Error writing " + filename + " : ".format(e))
      raise e

  @classmethod
  def get_wire_typeid(cls):
    return cls.__name__

  @classmethod
  def get_jsonpickle_typeid(cls):
    return cls.__module__ + "." + cls.__name__

  @classmethod
  def get_json_map_list(cls, some_list):
    return [item.to_json_map() for item in some_list]

  def set_type(self):
    # self.class_type = str(self.__class__.__name__)
    setattr(self, TYPE_FIELD, self.__class__.get_wire_typeid())
    # setattr(self, TYPE_FIELD, self.__class__.__name__)

  def set_type_recursively(self):
    self.set_type()
    for key, value in self.__dict__.iteritems():
      if isinstance(value, JsonObject):
        value.set_type_recursively()
      elif isinstance(value, list):
        for item in value:
          if isinstance(item, JsonObject):
            item.set_type_recursively()

  def set_jsonpickle_type_recursively(self):
    self.set_type()
    for key, value in self.__dict__.iteritems():
      if isinstance(value, JsonObject):
        value.set_type_recursively()
      elif isinstance(value, list):
        for item in value:
          if isinstance(item, JsonObject):
            item.set_jsonpickle_type_recursively()

  def __str__(self):
    return json.dumps(self.to_json_map())

  def set_from_dict(self, input_dict):
    if input_dict:
      for key, value in input_dict.iteritems():
        if isinstance(value, list):
          setattr(self, key, [JsonObject.make_from_dict(item) if isinstance(item, dict) else item for item in value])
        elif isinstance(value, dict):
          setattr(self, key, JsonObject.make_from_dict(value))
        else:
          setattr(self, key, value)

  def set_from_id(self, db_interface, id):
    return self.set_from_dict(db_interface.find_by_id(id=id))

  def to_json_map(self):
    """One convenient way of 'serializing' the object.
    
    So, the type must be properly set.
    Many functions accept such json maps, just as they accept strings.
    """
    self.set_type_recursively()
    jsonMap = {}
    for key, value in self.__dict__.iteritems():
      # logging.debug("%s %s", key, value)
      if isinstance(value, JsonObject):
        jsonMap[key] = value.to_json_map()
      elif isinstance(value, list):
        jsonMap[key] = [item.to_json_map() if isinstance(item, JsonObject) else item for item in value]
      else:
        jsonMap[key] = value
    return jsonMap

  def equals_ignore_id(self, other):
    # Makes a unicode copy.
    def to_unicode(input):
      if isinstance(input, dict):
        return {key: to_unicode(value) for key, value in input.iteritems()}
      elif isinstance(input, list):
        return [to_unicode(element) for element in input]
      elif check_class(input, [str, unicode]):
        return input.encode('utf-8')
      else:
        return input

    dict1 = to_unicode(self.to_json_map())
    dict1.pop("_id", None)
    # logging.debug(self.__dict__)
    # logging.debug(dict1)
    dict2 = to_unicode(other.to_json_map())
    dict2.pop("_id", None)
    # logging.debug(other.__dict__)
    # logging.debug(dict2)
    return dict1 == dict2

  def update_collection(self, db_interface):
    if hasattr(self, "schema"):
      self.validate(db_interface)
    return db_interface.update_doc(self)

  # To delete referrent items also, use appropriate method in JsonObjectNode.
  def delete_in_collection(self, db_interface):
    return db_interface.delete_doc(self)

  def validate(self, db_interface=None):
    """
    
    :param db_interface: Potentially useful in subclasses to perfrom validations (eg. is the target_id valid).
    This value may not be availabe: for example when called from the from_details methods.
    :return: 
    """
    self.validate_schema()

  # Override and call this method to add extra validations.
  def validate_schema(self):
    json_map = self.to_json_map()
    json_map.pop("_id", None)
    # logging.debug(str(self))
    from jsonschema import ValidationError
    from jsonschema import SchemaError
    try:
      jsonschema.validate(json_map, self.schema)
    except SchemaError as e:
      logging.error(jsonpickle.dumps(self.schema))
      raise e
    except ValidationError as e:
      logging.error(self)
      logging.error(self.schema)
      logging.error(json_map)
      raise e

  @classmethod
  def from_id(cls, id, db_interface):
    """Returns None if nothing is found."""
    item_dict = db_interface.find_by_id(id=id)
    item = None
    if item_dict != None:
      item = cls.make_from_dict(item_dict)
    return item

  def get_targetting_entities(self, db_interface, entity_type=None):
    return db_interface.get_targetting_entities(self, entity_type=entity_type)


class TargetValidationError(Exception):
  def __init__(self, allowed_types, target_obj, targetting_obj):
    self.allowed_types = allowed_types
    self.target_obj = target_obj
    self.targetting_obj = targetting_obj

  def __str__(self):
    return "%s\n targets object \n" \
           "%s,\n" \
           "which does not belong to \n" \
           "%s" % (self.targetting_obj, self.target_obj, str(self.allowed_types))


class Target(JsonObject):
  schema = recursively_merge(JsonObject.schema, {
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "enum": ["Target"]
      },
      "container_id": {
        "type": "string"
      }
    },
    "required": ["container_id"]
  })

  def get_target_entity(self, db_interface):
    """Returns null if db_interface doesnt have any such entity."""
    return JsonObject.from_id(id=self.container_id, db_interface=db_interface)

  @classmethod
  def from_details(cls, container_id):
    target = Target()
    target.container_id = container_id
    target.validate()
    return target

  @classmethod
  def from_ids(cls, container_ids):
    return [Target.from_details(str(container_id)) for container_id in container_ids]

  @classmethod
  def from_containers(cls, containers):
    return Target.from_ids(container_ids=[container._id for container in containers])


class JsonObjectWithTarget(JsonObject):
  """A JsonObject with a target field."""

  schema = recursively_merge(JsonObject.schema, ({
    "type": "object",
    "description": "A JsonObject with a target field.",
    "properties": {
      "targets": {
        "type": "array",
        "items": Target.schema,
        "description": "This field lets us define a directed graph involving JsonObjects stored in a database."
      }
    }
  }))

  target_class = Target

  @classmethod
  def get_allowed_target_classes(cls):
    return []

  def validate_targets(self, targets, allowed_types, db_interface):
    if targets and len(targets) > 0 and db_interface != None:
      for target in targets:
        target_entity = target.get_target_entity(db_interface=db_interface)
        if not check_class(target_entity, allowed_types):
          raise TargetValidationError(allowed_types=allowed_types, targetting_obj=self, target_obj=target_entity)

  def validate(self, db_interface=None):
    super(JsonObjectWithTarget, self).validate(db_interface=db_interface)
    if hasattr(self, "targets"):
      self.validate_targets(targets=self.targets, allowed_types=self.get_allowed_target_classes(),
                            db_interface=db_interface)


class JsonObjectNode(JsonObject):
  """Represents a tree (not a general Directed Acyclic Graph) of JsonObjectWithTargets."""
  schema = recursively_merge(
    JsonObject.schema, {
      "properties": {
        TYPE_FIELD: {
          "enum": ["JsonObjectNode"]
        },
        "content": JsonObject.schema,
        "children": {
          "type": "array",
          "items": JsonObjectWithTarget.schema
        }
      },
      "required": [TYPE_FIELD]
    }
  )

  def validate(self, db_interface=None):
    super(JsonObjectNode, self).validate(db_interface=None)
    for child in self.children:
      if not check_class(self.content, child.content.get_allowed_target_classes()):
        raise TargetValidationError(targetting_obj=child, target_obj=self.content)

    for child in self.children:
      child.validate(db_interface=None)

  @classmethod
  def from_details(cls, content, children=None):
    if children is None:
      children = []
    node = JsonObjectNode()
    # logging.debug(content)
    # Strangely, without the backend.data_containers, the below test failed on 20170501
    node.content = content
    # logging.debug(check_list_item_types(children, [JsonObjectNode]))
    node.children = children
    node.validate(db_interface=None)
    return node

  def update_collection(self, db_interface):
    self.validate(db_interface=db_interface)
    self.content = self.content.update_collection(db_interface)
    for child in self.children:
      if (not hasattr(child.content, "targets")) or child.content.targets == None or len(child.content.targets) == 0:
        child.content.targets = [child.content.target_class()]
      assert len(child.content.targets) == 1
      child.content.targets[0].container_id = str(self.content._id)
      child.update_collection(db_interface)

  def delete_in_collection(self, db_interface):
    self.fill_descendents(db_interface=db_interface, depth=100)
    for child in self.children:
      child.delete_in_collection(db_interface)
    # Delete or disconnect children before deleting oneself.
    self.content.delete_in_collection(db_interface)

  def fill_descendents(self, db_interface, depth=10):
    targetting_objs = self.content.get_targetting_entities(db_interface=db_interface)
    self.children = []
    if depth > 0:
      for targetting_obj in targetting_objs:
        child = JsonObjectNode.from_details(content=targetting_obj)
        child.fill_descendents(db_interface=db_interface, depth=depth - 1)
        self.children.append(child)


class TextContent(JsonObject):
  schema = recursively_merge(JsonObject.schema, ({
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "enum": ["TextContent"]
      },
      "text": {
        "type": "string",
      },
      "language": {
        "type": "string",
      },
      "encoding": {
        "type": "string",
      },
    },
    "required": ["text"]
  }))

  @classmethod
  def from_details(cls, text, language="UNK", encoding="UNK"):
    text_content = TextContent()
    text_content.text = text
    text_content.language = language
    text_content.encoding = encoding
    text_content.validate()
    return text_content


def get_schemas(module_in):
  import inspect
  schemas = {}
  for name, obj in inspect.getmembers(module_in):
    if inspect.isclass(obj) and hasattr(obj, "schema"):
      schemas[name] = obj.schema
  return schemas


# Essential for depickling to work.
update_json_class_index(sys.modules[__name__])
logging.debug(json_class_index)
