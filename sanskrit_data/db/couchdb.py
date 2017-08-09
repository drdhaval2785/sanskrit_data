""".. note:: For undocumented classes and methods, please see superclass documentation in :mod:`sanskrit_data.db`.
"""

from __future__ import absolute_import

import copy
import logging

from sanskrit_data.db import DbInterface, ClientInterface

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

def strip_revision_in_copy(doc_map):
  """ Strip the _rev field in a deep copy of doc_map and return it.
  
  :param dict doc_map: A dict representation of a JSON document.
  :return:  doc_map itself without _rev
  """
  new_doc = copy.deepcopy(doc_map)
  new_doc.pop("_rev", None)
  return new_doc


class CloudantApiClient(ClientInterface):
  def __init__(self, url):
    # logging.debug(url)
    import yurl
    parse_result = yurl.URL(url=url)
    import re
    url_without_credentials = re.sub(parse_result.username + ":" + parse_result.authorization, "", url)
    from cloudant.client import CouchDB
    self.client = CouchDB(user=parse_result.username, auth_token=parse_result.authorization, url=url_without_credentials, connect=True, auto_renew=True)
    # logging.debug(self.client)
    assert self.client != None, logging.error(self.client)

  def get_database(self, db_name):
    db = self.client.get(db_name, default=None)
    if db != None:
      return db
    else:
      return self.client.create_database(db_name)

  def get_database_interface(self, db_name):
    return CloudantApiDatabase(db=self.get_database(db_name=db_name))

  def delete_database(self, db_name):
    self.client.delete_database(db_name)


class CloudantApiDatabase(DbInterface):

  def __init__(self, db):
    logging.info("Initializing db :" + str(db))
    self.db = db

  def update_doc(self, doc):
    super(CloudantApiDatabase, self).update_doc(doc=doc)
    if not "_id" in doc:
      from uuid import uuid4
      doc["_id"] = uuid4().hex

    if self.exists(doc_id=doc["_id"]):
      db_doc = self.db[doc["_id"]]
      db_doc.fetch()

      new_doc = doc
      new_doc["_rev"] = db_doc["_rev"]

      db_doc.clear()
      db_doc.update(new_doc)
      db_doc.save()
      return copy.deepcopy(strip_revision_in_copy(db_doc))
    else:
      new_doc = self.db.create_document(data=doc, throw_on_exists=False)
      return strip_revision_in_copy(new_doc)

  def exists(self, doc_id):
    try:
      db_doc = self.db[doc_id]
      return db_doc.exists()
    except KeyError:
      return False


  def delete_doc(self, doc_id):
    """Beware: This leaves the document in the local cache! But other methods in this class should compensate."""
    if self.exists(doc_id=doc_id):
      db_doc = self.db[doc_id]
      db_doc.fetch()
      db_doc.delete()
    else:
      logging.warn("Trying to delete non-existant doc " + doc_id)
      pass

  def find_by_id(self, id):
    try:
      db_doc = self.db[id]
      if db_doc.exists():
        db_doc.fetch()
        return strip_revision_in_copy(doc_map=db_doc)
      else:
        return None
    except KeyError:
      return None

  def find(self, filter):
    from cloudant.query import Query
    query = Query(self.db, selector=filter)
    for doc in query.result:
      yield strip_revision_in_copy(doc_map=doc)

  def find_by_indexed_key(self, index_name, key):
    raise Exception("Not implemented")


class CouchdbApiClient(ClientInterface):
  """.. note:: Prefer :class:`CloudantApiClient`."""
  def __init__(self, url):
    from couchdb import Server
    self.server = Server(url=url)

  def get_database(self, db_name):
    try:
      return self.server[db_name]
    except:
      return self.server.create(db_name)

  def get_database_interface(self, db_name):
    return CouchdbApiDatabase(db=self.get_database(db_name=db_name))

  def delete_database(self, db_name):
    self.server.delete(db_name)

class CouchdbApiDatabase(DbInterface):
  """.. note:: Prefer :class:`CloudantApiDatabase`."""
  def __init__(self, db):
    logging.info("Initializing db :" + str(db))
    self.db = db

  def set_revision(self, doc_map):
    from couchdb import ResourceNotFound
    try:
      doc_map["_rev"] = self.db[doc_map["_id"]]["_rev"]
    except ResourceNotFound:
      pass

  def update_doc(self, doc):
    super(CouchdbApiDatabase, self).update_doc(doc=doc)
    if not hasattr(doc, "_id"):
      from uuid import uuid4
      doc._id = uuid4().hex
    self.set_revision(doc_map=doc)
    # logging.debug(doc)
    result_tuple = self.db.save(doc)
    assert result_tuple[0] == doc._id, logging.error(str(result_tuple[0]) + " vs " + doc._id)
    return doc

  def delete_doc(self, doc_id):
    from couchdb import ResourceNotFound
    try:
      map_to_delete = self.db[doc_id]
      self.db.delete(map_to_delete)
    except ResourceNotFound:
      pass

  def find_by_id(self, id):
    from couchdb import ResourceNotFound
    try:
      return strip_revision_in_copy(self.db[id])
    except ResourceNotFound:
      return None

  def find_by_indexed_key(self, index_name, key):
    raise Exception("not implemented")

  def find(self, filter):
    for row in self.db.find(query=filter):
      yield strip_revision_in_copy(row.doc)
