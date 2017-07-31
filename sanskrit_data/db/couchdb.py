from __future__ import absolute_import

import logging


from sanskrit_data.db import DbInterface, ClientInterface

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

  def delete_database(self, db_name):
    self.client.delete_database(db_name)


class CloudantApiDatabase(DbInterface):

  def __init__(self, db):
    logging.info("Initializing db :" + str(db))
    self.db = db

  def update_doc(self, doc):
    super(CouchdbApiDatabase, self).update_doc(doc=doc)
    if not hasattr(doc, "_id"):
      from uuid import uuid4
      doc._id = uuid4().hex
    # self.set_revision(doc_map=map_to_write)
    logging.debug(doc)
    result_tuple = self.db.save(doc)
    assert result_tuple[0] == doc._id, logging.error(str(result_tuple[0]) + " vs " + doc._id)
    return doc


class CouchdbApiClient(ClientInterface):
  def __init__(self):
    from couchdb import Server
    self.server = Server(url=self.server_config["couchdb_host"])

  def get_database(self, db_name):
    try:
      return self.server[self.TEST_DB_NAME]
    except:
      return self.server.create(self.TEST_DB_NAME)

  def delete_database(self, db_name):
    self.server.delete_database(db_name)

class CouchdbApiDatabase(DbInterface):

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
    self.set_revision(doc=doc)
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
