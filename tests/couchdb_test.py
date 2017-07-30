from __future__ import absolute_import

import logging
import unittest

from sanskrit_data.db.couchdb import CouchdbApiDatabase, CloudantApiClient, CloudantApiDatabase
from sanskrit_data.schema.common import JsonObject

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class TestDBRoundTrip(unittest.TestCase):
  TEST_DB_NAME = 'vedavaapi_test'

  def set_configuration(self):
    import os
    CODE_ROOT = os.path.dirname(__file__)
    config_file_name = os.path.join(CODE_ROOT, 'server_config_local.json')
    with open(config_file_name) as fhandle:
      import json
      self.server_config = json.loads(fhandle.read())

  def setUp(self):
    self.set_configuration()
    self.server = CloudantApiClient(self.server_config["couchdb_host"])
    self.test_db_base = self.server.get_database(db_name=self.TEST_DB_NAME)
    self.test_db = CloudantApiDatabase(db=self.test_db_base)

  def tearDown(self):
    self.server.delete_database(self.TEST_DB_NAME)

  def test_update_doc(self):
    doc = JsonObject()
    updated_doc = self.test_db.update_doc(doc)
    logging.debug(updated_doc)
    updated_doc.xyz = "xyzvalue"
    updated_doc = self.test_db.update_doc(doc)
    logging.debug(updated_doc)
    pass

  def test_delete_doc_find_by_id(self):
    doc = JsonObject()
    updated_doc = self.test_db.update_doc(doc)
    logging.debug(updated_doc)
    self.test_db.delete_doc(doc)
    self.assertEqual(self.test_db.find_by_id(updated_doc._id), None)
    self.test_db.delete_doc(doc)

  def test_find(self):
    doc = JsonObject()
    doc.xyz = "xyzvalue"
    updated_doc = self.test_db.update_doc(doc)
    logging.debug(updated_doc)
    found_doc = self.test_db.find(filter={"xyz": "xyzvalue"}).next()
    self.assertEqual(str(updated_doc), str(found_doc))


if __name__ == '__main__':
  unittest.main()