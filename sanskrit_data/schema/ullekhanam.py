# -*- coding: utf-8 -*-
"""
Intro
-----------

-  Annotations are stored in a directed acyclic graph, for example - a book portion having a TextAnnotation having PadaAnnotations having SamaasaAnnotations.

    -  Some Annotations (eg. SandhiAnnotation, TextAnnotation) can
       have multiple "targets" (ie. other objects being annotated).
    -  Rather than a simple tree, we end up with a Directed Acyclic
       Graph (DAG) of Annotation objects.

-  JSON schema mindmap
   `here <https://drive.mindmup.com/map?state=%7B%22ids%22:%5B%220B1_QBT-hoqqVbHc4QTV3Q2hjdTQ%22%5D,%22action%22:%22open%22,%22userId%22:%22109000762913288837175%22%7D>`__
   (Updated as needed).
- For general context and class diagram, refer to :mod:`~sanskrit_data.schema`.

"""
import logging
import sys

from sanskrit_data.schema import common
from sanskrit_data.schema.books import BookPortion, CreationDetails
from sanskrit_data.schema.common import JsonObject, UllekhanamJsonObject, Target, DataSource, ScriptRendering, Text, NamedEntity
from jsonschema import ValidationError
from jsonschema import SchemaError

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class Annotation(UllekhanamJsonObject):
  schema = common.recursively_merge_json_schemas(UllekhanamJsonObject.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["Annotation"]
      },
      "targets": {
        "type": "array",
        "description": "The entity being annotated.",
        "minItems": 1,
        "items": Target.schema
      },
    },
    "required": ["targets", "source"]
  }))

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, Annotation]

  def set_base_details(self, targets, source):
    # noinspection PyAttributeOutsideInit
    self.targets = targets
    # noinspection PyAttributeOutsideInit
    self.source = source


class Rectangle(JsonObject):
  schema = common.recursively_merge_json_schemas(JsonObject.schema, ({
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
    overalap_w = min(self.x + self.w, other.x + other.w) - xmax
    overalap_h = min(self.y + self.h, other.y + other.h) - ymax
    return overalap_w > 0 and overalap_h > 0

  def __ne__(self, other):
    return not self.__eq__(other)

  # noinspection PyTypeChecker
  def __cmp__(self, other):
    if self == other:
      logging.info(str(self) + " overlaps " + str(other))
      return 0
    elif (self.y < other.y) or ((self.y == other.y) and (self.x < other.x)):
      return -1
    else:
      return 1


# noinspection PyMethodOverriding
class ImageTarget(Target):
  schema = common.recursively_merge_json_schemas(Target.schema, ({
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
  # noinspection PyMethodOverriding
  @classmethod
  def from_details(cls, container_id, rectangle):
    target = ImageTarget()
    target.container_id = container_id
    target.rectangle = rectangle
    target.validate()
    return target


class ValidationAnnotationSource(DataSource):
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
    "type": "object",
    "description": "Any user or system script can validate a certain annotation (or other object). But it is up to various systems whether such 'validation' has any effect.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["ValidationAnnotationSource"]
      },
      "by_admin": {
        "type": "boolean",
        "description": "Was the creator of this annotation an admin at the time it was created or updated?"
      }
    },
  }))

  def infer_by_admin(self, db_interface=None, user=None):
    if not hasattr(self, "by_admin"):
      # source_type is a compulsory attribute, because that validation is done separately and a suitable error is thrown.
      if hasattr(self, "source_type") and self.source_type == "user_supplied":
        if user is not None and db_interface is not None:
          if not hasattr(self, "id") or self.id in user.get_user_ids():
            self.by_admin = user.is_admin(service=db_interface.db_name_frontend)

  def setup_source(self, db_interface=None, user=None):
    self.infer_by_admin(db_interface=db_interface, user=user)
    super(ValidationAnnotationSource, self).setup_source(db_interface=db_interface, user=user)

  def validate(self, db_interface=None, user=None):
    super(ValidationAnnotationSource, self).validate(db_interface=db_interface, user=user)
    # Only if the writer user is an admin or None, allow by_admin to be set to true (even when the admin is impersonating another user).
    if hasattr(self, "by_admin") and self.by_admin:
      if user is not None and db_interface is not None and not user.is_admin(service=db_interface.db_name_frontend):
        raise ValidationError("Impersonation by %(id_1)s of %(id_2)s not allowed for this user." % dict(id_1=user.get_first_user_id_or_none(), id_2=self.id))

      # source_type is a compulsory attribute, because that validation is done separately and a suitable error is thrown.
      if hasattr(self, "source_type") and self.source_type != "user_supplied":
        if user is not None and db_interface is not None:
          raise ValidationError("non user_supplied source_type cannot be an admin.")


class ValidationAnnotation(Annotation):
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
    "type": "object",
    "description": "Any user can validate a certain annotation (or other object). But it is up to various systems whether such 'validation' has any effect.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["ValidationAnnotation"]
      },
      "source": ValidationAnnotationSource.schema
    },
  }))

  def __init__(self):
    super(ValidationAnnotation, self).__init__()
    self.source = ValidationAnnotationSource()

  def get_source_type(self):
    return ValidationAnnotationSource

class ImageAnnotation(Annotation):
  """ Mark a certain fragment of an image.

  `An introductory video <https://www.youtube.com/watch?v=SHzD3f5nPt0&t=29s>`_
  """
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
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
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
    "type": "object",
    "description": "Annotation of some (sub)text from within the object (image or another text) being annotated. Tells: 'what is written in this image? or text portion?",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["TextAnnotation"]
      },
      "content": Text.schema,
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

  @classmethod
  def add_indexes(cls, db_interface):
    super(TextAnnotation, cls).add_indexes(db_interface=db_interface)
    db_interface.add_index(keys_dict={
      "content.search_strings": 1
    }, index_name="content_search_strings")


class CommentAnnotation(TextAnnotation):
  schema = common.recursively_merge_json_schemas(TextAnnotation.schema, ({
    "description": "A comment that can be associated with nearly any Annotation or BookPortion.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["CommentAnnotation"]
      },
    }
  }))

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, Annotation]


class TranslationAnnotation(TextAnnotation):
  schema = common.recursively_merge_json_schemas(TextAnnotation.schema, ({
    "description": "A comment that can be associated with nearly any Annotation or BookPortion.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["TranslationAnnotation"]
      },
    }
  }))

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, Annotation]


class QuoteAnnotation(TextAnnotation):
  schema = common.recursively_merge_json_schemas(TextAnnotation.schema, ({
    "description": "A quote, a memorable text fragment.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["QuoteAnnotation"]
      },
    }
  }))

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, Annotation]


class Metre(NamedEntity):
  schema = common.recursively_merge_json_schemas(NamedEntity.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["Metre"]
      }
    }
  }))


class MetreAnnotation(Annotation):
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
    "description": "A metre, which may be ",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["MetreAnnotation"]
      },
      "metre": Metre.schema
    }
  }))


class TextOffsetAddress(JsonObject):
  schema = common.recursively_merge_json_schemas(JsonObject.schema, {
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
  schema = common.recursively_merge_json_schemas(Target.schema, ({
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
    if shabda_id is not None:
      target.shabda_id = shabda_id
    if offset_address is not None:
      target.offset_address = offset_address
    target.validate()
    return target


# noinspection PyMethodOverriding
class PadaAnnotation(Annotation):
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
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
      "word": Text.schema,
      "root": Text.schema,
    },
  }))

  target_class = TextTarget

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, TextAnnotation]

  def set_base_details(self, targets, source, word, root):
    super(PadaAnnotation, self).set_base_details(targets, source)
    # noinspection PyAttributeOutsideInit
    self.word = word
    # noinspection PyAttributeOutsideInit
    self.root = root

  @classmethod
  def from_details(cls, targets, source, word, root):
    annotation = PadaAnnotation()
    annotation.set_base_details(targets, source, word, root)
    annotation.validate()
    return annotation


# Targets: TextTarget pointing to TextAnnotation
# noinspection PyMethodOverriding
class SubantaAnnotation(PadaAnnotation):
  schema = common.recursively_merge_json_schemas(PadaAnnotation.schema, ({
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


# noinspection PyMethodOverriding,PyPep8Naming
class TinantaAnnotation(PadaAnnotation):
  schema = common.recursively_merge_json_schemas(PadaAnnotation.schema, ({
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
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
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

  def validate(self, db_interface=None, user=None):
    super(TextSambandhaAnnotation, self).validate(db_interface=db_interface, user=user)
    self.validate_targets(targets=self.source_text_padas, allowed_types=[PadaAnnotation], db_interface=db_interface)
    self.validate_targets(targets=self.target_text_padas, allowed_types=[PadaAnnotation], db_interface=db_interface)

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion, TextAnnotation]


# Targets: two or more PadaAnnotations
class SandhiAnnotation(Annotation):
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["SandhiAnnotation"]
      },
      "combined_string": Text.schema,
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
  def from_details(cls, targets, source, combined_string, sandhi_type="UNK"):
    annotation = SandhiAnnotation()
    annotation.set_base_details(targets, source)
    annotation.combined_string = combined_string
    annotation.sandhi_type = sandhi_type
    annotation.validate()
    return annotation


# Targets: one PadaAnnotation (the samasta-pada)
class SamaasaAnnotation(Annotation):
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
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
      "samaasa_type": {
        "type": "string"
      }
    },
  }))

  @classmethod
  def get_allowed_target_classes(cls):
    return [PadaAnnotation]

  def validate(self, db_interface=None, user=None):
    super(SamaasaAnnotation, self).validate(db_interface=db_interface, user=user)
    self.validate_targets(targets=self.component_padas, allowed_types=[PadaAnnotation], db_interface=db_interface)

  @classmethod
  def from_details(cls, targets, source, combined_string, samaasa_type="UNK"):
    annotation = SamaasaAnnotation()
    annotation.set_base_details(targets, source)
    annotation.combined_string = combined_string
    annotation.type = samaasa_type
    annotation.validate()
    return annotation


class OriginAnnotation(Annotation):
  """See schema.description."""
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
    "type": "object",
    "description": "A given text may be quoted from some other book. This annotation helps specify such origin.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["OriginAnnotation"]
      },
      "originDetails": CreationDetails.schema,
    },
  }))


class Topic(NamedEntity):
  schema = common.recursively_merge_json_schemas(NamedEntity.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["Topic"]
      }
    }
  }))


class TopicAnnotation(Annotation):
  """See schema.description."""
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
    "type": "object",
    "description": "A given text may be quoted from some other book. This annotation helps specify such origin.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["TopicAnnotation"]
      },
      "topic": Topic.schema,
    },
  }))


class RatingAnnotation(Annotation):
  """See schema.description."""
  schema = common.recursively_merge_json_schemas(Annotation.schema, ({
    "type": "object",
    "description": "A given text may be quoted from some other book. This annotation helps specify such origin.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["RatingAnnotation"]
      },
      "rating": {
        "type": "number"
      },
      "editable_by_others": {
        "type": "boolean",
        "description": "Can this annotation be taken over by others for wiki-style editing or deleting?",
        "default": False
      }
    },
  }))


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)
