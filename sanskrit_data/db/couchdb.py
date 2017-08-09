""".. note:: For undocumented classes and methods, please see superclass documentation in :mod:`sanskrit_data.db`.
"""

from __future__ import absolute_import

import logging


from sanskrit_data.db import DbInterface, ClientInterface

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

def strip_revision(doc_map):
  """ Strip the _rev field.
  
  :param dict doc_map: A dict representation of a JSON document.
  :return:  doc_map itself without _rev
  """
  doc_map.pop("_rev", None)
  return doc_map


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

    from cloudant.document import Document
    with Document(self.db, doc["_id"]) as db_doc:
      logging.debug(db_doc)
      db_doc.clear()
      db_doc.update(doc)
    new_doc = self.db[doc["_id"]]
    strip_revision(new_doc)
    return new_doc

  def delete_doc(self, doc_id):
    """Beware: This leaves the document in the local cache! But other methods in this class should compensate."""
    from cloudant.document import Document
    with Document(self.db, doc_id) as db_doc:
      return db_doc.delete()

  def find_by_id(self, id):
    if id in self.db:
      new_doc = self.db[id]

      # A document could be in the local cache but not in the remote db.
      if new_doc.exists() and "_rev" in new_doc:
        return strip_revision(new_doc)
      else:
        return None
    else:
      return None

  def find(self, filter):
    from cloudant.query import Query
    query = Query(self.db, selector=filter)
    for doc in query.result:
      yield strip_revision(doc_map=doc)

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
    logging.debug(doc)
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
      return strip_revision(self.db[id])
    except ResourceNotFound:
      return None

  def find_by_indexed_key(self, index_name, key):
    raise Exception("not implemented")

  def find(self, filter):
    for row in self.db.find(query=filter):
      yield strip_revision(row.doc)
