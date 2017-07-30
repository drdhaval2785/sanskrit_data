from __future__ import absolute_import

import logging

from couchdb import ResourceNotFound

from sanskrit_data.db import DbInterface

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

def strip_revision(doc_map):
  """
  
  :param doc_map: 
  :return:  doc_map itself without _rev
  """
  doc_map.pop("_rev", None)
  return doc_map

class Database(DbInterface):
  def __init__(self, db):
    logging.info("Initializing db :" + str(db))
    self.db = db

  def set_revision(self, doc_map):
    try:
      doc_map["_rev"] = self.db[doc_map["_id"]]["_rev"]
    except ResourceNotFound:
      pass

  def update_doc(self, doc):
    super(Database, self).update_doc(doc=doc)
    if not hasattr(doc, "_id"):
      from uuid import uuid4
      doc._id = uuid4().hex
    map_to_write = doc.to_json_map()
    self.set_revision(doc_map=map_to_write)
    logging.debug(map_to_write)
    result_tuple = self.db.save(map_to_write)
    assert result_tuple[0] == doc._id, logging.error(str(result_tuple[0]) + " vs " + doc._id)
    return doc

  def delete_doc(self, doc):
    assert hasattr(doc, "_id")
    try:
      map_to_delete = self.db[doc._id]
      self.db.delete(map_to_delete)
    except ResourceNotFound:
      pass

  def find_by_id(self, id):
    try:
      return strip_revision(self.db[id])
    except ResourceNotFound:
      return None

  def find_by_indexed_key(self, index_name, key):
    raise Exception("not implemented")
    pass

  def find(self, filter):
    for row in self.db.find(query=filter):
      yield strip_revision(row.doc)

  def get_targetting_entities(self, json_obj, entity_type=None):
    raise Exception("not implemented")
    pass
