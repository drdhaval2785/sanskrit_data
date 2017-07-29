# -*- coding: utf-8 -*-
import logging
import sys

import common
from sanskrit_data.schema.books import BookPortion
from sanskrit_data.schema.common import JsonObject, JsonObjectWithTarget, Target, TextContent

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class AnnotationSource(JsonObject):
  schema = common.recursively_merge(JsonObject.schema, ({
    "type": "object",
    "description": "Source of the annotation which contains this node.",
    common.TYPE_FIELD: {
      "enum": ["AnnotationSource"]
    },
    "properties": {
      "source_type": {
        "type": "string",
        "enum": ["system_inferred", "user_supplied"],
        "description": "Does this annotation come from a machine, or a human? source_ prefix avoids keyword conflicts in some languages.",
      },
      "id": {
        "type": "string",
        "description": "Something to identify the particular annotation source.",
      }
    },
    "required": ["source_type"]
  }))

  @classmethod
  def from_details(cls, source_type, id):
    source = AnnotationSource()
    source.source_type = source_type
    source.id = id
    source.validate_schema()
    return source


class Annotation(JsonObjectWithTarget):
  schema = common.recursively_merge(JsonObjectWithTarget.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["Annotation"]
      },
      "source": AnnotationSource.schema,
      "targets": {
        "type": "array",
        "description": "The entity being annotated.",
        "minLength": 1,
        "items": Target.schema
      }
    },
    "required": ["targets", "source"]
  }))

  def validate(self, db_interface=None):
    if "user" in self.source.source_type:
      from flask import session
      # logging.debug(session.get('user', None))
      user = JsonObject.make_from_dict(session.get('user', None))
      # logging.debug(user)
      self.source.id = user.get_user_ids()[0]
    super(Annotation, self).validate(db_interface=db_interface)

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, Annotation]

  def set_base_details(self, targets, source):
    self.targets = targets
    self.source = source


class Rectangle(JsonObject):
  schema = common.recursively_merge(JsonObject.schema, ({
    "type": "object",
    "description": "A rectangle within an image.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["Rectangle"]
      },
      "x1": {
        "type": "integer"
      },
      "y1": {
        "type": "integer"
      },
      "w": {
        "type": "integer"
      },
      "h": {
        "type": "integer"
      },
    },
    "required": ["x1", "y1", "w", "h"]
  }))

  @classmethod
  def from_details(cls, x=-1, y=-1, w=-1, h=-1, score=0.0):
    rectangle = Rectangle()
    rectangle.x1 = x
    rectangle.y1 = y
    rectangle.w = w
    rectangle.h = h
    rectangle.score = score
    rectangle.validate()
    return rectangle

    # Two (segments are 'equal' if they overlap
    def __eq__(self, other):
      xmax = max(self.x, other.x)
      ymax = max(self.y, other.y)
      w = min(self.x + self.w, other.x + other.w) - xmax
      h = min(self.y + self.h, other.y + other.h) - ymax
      return w > 0 and h > 0

    def __ne__(self, other):
      return not self.__eq__(other)

    def __cmp__(self, other):
      if self == other:
        logging.info(str(self) + " overlaps " + str(other))
        return 0
      elif (self.y < other.y) or ((self.y == other.y) and (self.x < other.x)):
        return -1
      else:
        return 1


class ImageTarget(Target):
  schema = common.recursively_merge(Target.schema, ({
    "type": "object",
    "description": "The rectangle within the image being targetted.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["ImageTarget"]
      },
      "rectangle": Rectangle.schema
    },
    "required": ["rectangle"]
  }))

  # TODO use w, h instead.
  @classmethod
  def from_details(cls, container_id, rectangle):
    target = ImageTarget()
    target.container_id = container_id
    target.rectangle = rectangle
    target.validate()
    return target


class ImageAnnotation(Annotation):
  schema = common.recursively_merge(Annotation.schema, ({
    "type": "object",
    "description": "A rectangle within an image, picked by a particular annotation source.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["ImageAnnotation"]
      },
      "targets": {
        "type": "array",
        "items": ImageTarget.schema
      }
    },
  }))

  target_class = ImageTarget

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, ImageAnnotation]

  @classmethod
  def from_details(cls, targets, source):
    annotation = ImageAnnotation()
    annotation.set_base_details(targets, source)
    annotation.validate()
    return annotation


# Targets: ImageAnnotation(s) or  TextAnnotation or BookPortion
class TextAnnotation(Annotation):
  schema = common.recursively_merge(Annotation.schema, ({
    "type": "object",
    "description": "Annotation of some (sub)text from within the object (image or another text) being annotated.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["TextAnnotation"]
      },
      "content": TextContent.schema,
    },
    "required": ["content"]
  }))

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, ImageAnnotation]

  @classmethod
  def from_details(cls, targets, source, content):
    annotation = TextAnnotation()
    annotation.set_base_details(targets, source)
    annotation.content = content
    annotation.validate()
    return annotation


class CommentAnnotation(TextAnnotation):
  schema = common.recursively_merge(TextAnnotation.schema, ({
    "description": "A comment that can be associated with nearly any Annotation or BookPortion.",
  }))

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, Annotation]


class TextOffsetAddress(JsonObject):
  schema = common.recursively_merge(JsonObject.schema, {
    "type": "object",
    "description": "A way to specify a substring.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["TextOffsetAddress"]
      },
      "start": {
        "type": "integer"
      },
      "end": {
        "type": "integer"
      }
    }})

  @classmethod
  def from_details(cls, start, end):
    obj = TextOffsetAddress()
    obj.start = start
    obj.end = end
    obj.validate()
    return obj


class TextTarget(Target):
  schema = common.recursively_merge(Target.schema, ({
    "type": "object",
    "description": "A way to specify a particular substring within a string.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["TextTarget"]
      },
      "shabda_id": {
        "type": "string",
        "description": "Format: pada_index.shabda_index or just pada_index."
                       "Suppose that some shabda in 'rāgādirogān satatānuṣaktān' is being targetted. "
                       "This has the following pada-vigraha: rāga [comp.]-ādi [comp.]-roga [ac.p.m.]  satata [comp.]-anuṣañj [ac.p.m.]."
                       "Then, rāga has the id 1.1. roga has id 1.3. satata has the id 2.1."
      },
      "offset_address": TextOffsetAddress.schema
    },
  }))

  @classmethod
  def from_details(cls, container_id, shabda_id=None, offset_address=None):
    target = TextTarget()
    target.container_id = container_id
    if shabda_id != None:
      target.shabda_id = shabda_id
    if offset_address != None:
      target.offset_address = offset_address
    target.validate()
    return target


class PadaAnnotation(Annotation):
  schema = common.recursively_merge(Annotation.schema, ({
    "type": "object",
    "description": "A grammatical pada - subanta or tiNanta.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["PadaAnnotation"]
      },
      "targets": {
        "type": "array",
        "items": TextTarget.schema
      },
      "word": {
        "type": "string"
      },
      "root": {
        "type": "string"
      }
    },
  }))

  target_class = TextTarget

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, TextAnnotation]

  def set_base_details(self, targets, source, word, root):
    super(PadaAnnotation, self).set_base_details(targets, source)
    self.word = word
    self.root = root

  @classmethod
  def from_details(cls, targets, source, word, root):
    annotation = PadaAnnotation()
    annotation.set_base_details(targets, source, word, root)
    annotation.validate()
    return annotation


# Targets: TextTarget pointing to TextAnnotation
class SubantaAnnotation(PadaAnnotation):
  schema = common.recursively_merge(PadaAnnotation.schema, ({
    "type": "object",
    "description": "Anything ending with a sup affix. Includes avyaya-s.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["SubantaAnnotation"]
      },
      "linga": {
        "type": "string",
        "enum": ["strii", "pum", "napum", "avyaya"]
      },
      "vibhakti": {
        "type": "string",
        "enum": ["1", "2", "3", "4", "5", "6", "7", "1.sambodhana"]
      },
      "vachana": {
        "type": "integer",
        "enum": [1, 2, 3]
      }
    },
  }))

  @classmethod
  def from_details(cls, targets, source, word, root, linga, vibhakti, vachana):
    obj = SubantaAnnotation()
    obj.set_base_details(targets, source, word, root)
    obj.linga = linga
    obj.vibhakti = vibhakti
    obj.vachana = vachana
    obj.validate()
    return obj


class TinantaAnnotation(PadaAnnotation):
  schema = common.recursively_merge(PadaAnnotation.schema, ({
    "type": "object",
    "description": "Anything ending with a tiN affix.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["TinantaAnnotation"]
      },
      "lakAra": {
        "type": "string",
        "enum": ["laT", "laN", "vidhi-liN", "AshIr-liN", "loT", "liT", "luT", "LT", "luN", "LN", "leT"]
      },
      "puruSha": {
        "type": "string",
        "enum": ["prathama", "madhyama", "uttama"]
      },
      "vachana": {
        "type": "integer",
        "enum": [1, 2, 3]
      }
    },
  }))

  @classmethod
  def from_details(cls, targets, source, word, root, lakAra, puruSha, vachana):
    obj = TinantaAnnotation()
    obj.set_base_details(targets, source, word, root)
    obj.lakAra = lakAra
    obj.puruSha = puruSha
    obj.vachana = vachana
    obj.validate()
    return obj


# Targets: a pair of textAnnotation or BookPortion objects
class TextSambandhaAnnotation(Annotation):
  schema = common.recursively_merge(Annotation.schema, ({
    "type": "object",
    "description": "Describes connection between two text portions. Such connection is directional (ie it connects words in a source sentence to words in a target sentence.)",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["TextSambandhaAnnotation"]
      },
      "targets": {
        "description": "A pair of texts being connected. First text is the 'source text', second is the 'target text'",
      },
      "category": {
        "type": "string"
      },
      "source_text_padas": {
        "type": "array",
        "description": "The entity being annotated.",
        "items": Target.schema
      },
      "target_text_padas": {
        "type": "array",
        "description": "The entity being annotated.",
        "items": Target.schema
      }
    },
    "required": ["combined_string"]
  }))
  
  def validate(self, db_interface=None):
    super(TextSambandhaAnnotation, self).validate(db_interface=db_interface)
    self.validate_targets(targets=self.source_text_padas, allowed_types=[PadaAnnotation], db_interface=db_interface)
    self.validate_targets(targets=self.target_text_padas, allowed_types=[PadaAnnotation], db_interface=db_interface)

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, TextAnnotation]



# Targets: two or more PadaAnnotations
class SandhiAnnotation(Annotation):
  schema = common.recursively_merge(Annotation.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["SandhiAnnotation"]
      },
      "combined_string": {
        "type": "string"
      },
      "sandhi_type": {
        "type": "string"
      }
    },
    "required": ["combined_string"]
  }))

  @classmethod
  def get_allowed_target_classes(cls):
    return [PadaAnnotation]

  @classmethod
  def from_details(cls, targets, source, combined_string, type="UNK"):
    annotation = SandhiAnnotation()
    annotation.set_base_details(targets, source)
    annotation.combined_string = combined_string
    annotation.sandhi_type = type
    annotation.validate()
    return annotation


# Targets: one PadaAnnotation (the samasta-pada)
class SamaasaAnnotation(Annotation):
  schema = common.recursively_merge(Target.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["SamaasaAnnotation"]
      },
      "component_padas": {
        "type": "array",
        "description": "Pointers to PadaAnnotation objects corresponding to components of the samasta-pada",
        "items": Target.schema
      },
      "type": {
        "type": "string"
      }
    },
  }))

  @classmethod
  def get_allowed_target_classes(cls):
    return [PadaAnnotation]

  def validate(self, db_interface=None):
    super(SamaasaAnnotation, self).validate(db_interface=db_interface)
    self.validate_targets(targets=self.component_padas, allowed_types=[PadaAnnotation], db_interface=db_interface)

  @classmethod
  def from_details(cls, targets, source, combined_string, type="UNK"):
    annotation = SamaasaAnnotation()
    annotation.set_base_details(targets, source)
    annotation.combined_string = combined_string
    annotation.type = type
    annotation.validate()
    return annotation


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)
