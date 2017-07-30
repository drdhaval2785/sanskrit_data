import logging
from bson import ObjectId

from sanskrit_data.db import DbInterface

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

def get_mongo_client(host):
  try:
    from pymongo import MongoClient
    return MongoClient(host=host)
  except Exception as e:
    print("Error initializing MongoDB database; aborting.", e)
    import sys
    sys.exit(1)

class Collection(DbInterface):
  def __init__(self, some_collection):
    logging.info("Initializing collection :" + str(some_collection))
    self.mongo_collection = some_collection

  def find_by_id(self, id):
    return self.mongo_collection.find_one({"_id": ObjectId(id)})

  def find_one(self, filter):
    return self.mongo_collection.find_one(filter=filter)

  def get_targetting_entities(self, json_obj, entity_type=None):
    filter = {
      "targets": {
        "$elemMatch": {
          "container_id": str(json_obj._id)
        }
      }
    }
    if entity_type:
      import sanskrit_data.schema.common
      filter[sanskrit_data.schema.common.TYPE_FIELD] = entity_type
    targetting_objs = [json_obj.make_from_dict(item) for item in self.mongo_collection.find(filter)]
    return targetting_objs

  def update_doc(self, doc):
    from pymongo import ReturnDocument
    super(Collection, self).update_doc(doc=doc)
    map_to_write = doc.to_json_map()
    if hasattr(doc, "_id"):
      filter = {"_id": ObjectId(doc._id)}
      map_to_write.pop("_id", None)
    else:
      filter = doc.to_json_map()

    updated_doc = self.mongo_collection.find_one_and_update(filter, {"$set": map_to_write}, upsert=True, return_document=ReturnDocument.AFTER)
    doc.set_type()
    from sanskrit_data.schema.common import TYPE_FIELD
    updated_doc[TYPE_FIELD] = getattr(doc, TYPE_FIELD)
    from sanskrit_data.schema.common import JsonObject
    updated_obj = JsonObject.make_from_dict(updated_doc)
    return updated_obj

  def delete_doc(self, doc):
    assert hasattr(doc, "_id"), "_id not present!"
    self.mongo_collection.delete_one({"_id": ObjectId(doc._id)})

  def get_no_target_entities(self):
    iter = self.mongo_collection.find(
      filter={"$or":
                [{"targets" : {"$exists" : False}},
                 {"targets" : {"$size" : 0}}]
              })
    from sanskrit_data.schema.common import JsonObject
    return [JsonObject.make_from_dict(x) for x in iter]


