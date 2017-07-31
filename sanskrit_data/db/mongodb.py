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

  def find(self, filter):
    return self.mongo_collection.find(filter)

  def update_doc(self, doc):
    from pymongo import ReturnDocument
    if "_id" in doc:
      filter = {"_id": ObjectId(doc._id)}
      doc.pop("_id", None)
    else:
      filter = doc
    updated_doc = self.mongo_collection.find_one_and_update(filter, {"$set": doc}, upsert=True, return_document=ReturnDocument.AFTER)
    return updated_doc

  def delete_doc(self, doc_id):
    self.mongo_collection.delete_one({"_id": ObjectId(doc_id)})
