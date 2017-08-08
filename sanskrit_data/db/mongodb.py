""".. note:: For undocumented classes and methods, please see superclass documentation in :mod:`sanskrit_data.db`."""

import logging
from bson import ObjectId

from sanskrit_data.db import DbInterface, ClientInterface

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class Client(ClientInterface):
  def __init__(self, url):
    try:
      from pymongo import MongoClient
      self.client = MongoClient(host=url)
    except Exception as e:
      logging.error("Error initializing MongoDB database; aborting.")
      raise e

  def get_db_collection_names(self, db_collection_string):
    """

    :param db_collection_string: A string like someDb.someCollection or just someCollection, which is interpreted as someCollection.someCollection.
    :return: An object with db and collection names.
    """
    name_parts = db_collection_string.split(".")
    assert len(name_parts) > 0
    obj = {"db": name_parts[0],
           "collection": name_parts[0],
           }
    if len(name_parts) == 2:
      obj["collection"] = name_parts[1]
    return obj


  def get_database(self, db_name):
    db_details = self.get_db_collection_names(db_collection_string=db_name)
    return self.client[db_details["db"]][db_details["collection"]]

  def get_database_interface(self, db_name):
    return Collection(some_collection=self.get_database(db_name=db_name))

  def delete_database(self, db_name):
    """Deletes a collection, does not bother with the database."""
    db_details = self.get_db_collection_names(db_collection_string=db_name)
    self.client[db_details["db"]].drop_collection(db_details["collection"])


class Collection(DbInterface):
  def __init__(self, some_collection):
    logging.info("Initializing collection :" + str(some_collection))
    self.mongo_collection = some_collection

  def find_by_id(self, id):
    return self.find_one(filter={"_id": id})

  def find_one(self, filter):
    _fix_id_filter(filter=filter)
    result = self.mongo_collection.find_one(filter=filter)
    _fix_id(doc=result)
    return result

  def find(self, filter):
    results = self.mongo_collection.find(filter)
    for result in results:
      _fix_id(doc=result)
      yield result

  def update_doc(self, doc):
    from pymongo import ReturnDocument
    if "_id" in doc:
      filter = {"_id": ObjectId(doc["_id"])}
      doc.pop("_id", None)
    else:
      filter = doc
    updated_doc = self.mongo_collection.find_one_and_update(filter, {"$set": doc}, upsert=True, return_document=ReturnDocument.AFTER)
    _fix_id(doc=updated_doc)
    return updated_doc

  def delete_doc(self, doc_id):
    self.mongo_collection.delete_one({"_id": ObjectId(doc_id)})

def _fix_id(doc):
  if doc != None and "_id" in doc:
    doc["_id"] = str(doc["_id"])

def _fix_id_filter(filter):
  if "_id" in filter:
    filter["_id"] = ObjectId(filter["_id"])
