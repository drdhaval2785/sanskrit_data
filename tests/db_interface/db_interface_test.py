from __future__ import absolute_import

import logging
import unittest

import tests
from sanskrit_data.schema.common import JsonObject

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class TestDBRoundTrip(unittest.TestCase):
  TEST_DB_NAME = 'vedavaapi_test'

  def setUp(self):
    tests.set_configuration()
    # from sanskrit_data.db.couchdb import CloudantApiClient
    # self.server = CloudantApiClient(tests.server_config["couchdb_host"])
    from sanskrit_data.db.implementations import mongodb
    self.server = mongodb.Client(url=tests.server_config["mongo_host"])
    self.test_db = self.server.get_database_interface(db_name_backend=self.TEST_DB_NAME)

  def tearDown(self):
    self.server.delete_database(self.TEST_DB_NAME)
    pass

  def test_update_doc(self):
    doc = JsonObject()
    updated_doc = self.test_db.update_doc(doc.to_json_map())
    logging.debug(updated_doc)
    updated_doc["xyz"] = "xyzvalue"
    updated_doc = self.test_db.update_doc(updated_doc)
    logging.debug(updated_doc)
    self.assertNotEqual(updated_doc, None)
    self.assertEqual("xyz" in updated_doc, True)
    updated_doc = self.test_db.find_by_id(updated_doc["_id"])
    self.assertNotEqual(updated_doc, None)


  def test_delete_doc_find_by_id(self):
    doc = JsonObject()
    updated_doc = self.test_db.update_doc(doc.to_json_map())
    logging.debug(updated_doc)
    doc_id = updated_doc["_id"]
    self.test_db.delete_doc(doc_id)
    self.assertEqual(self.test_db.find_by_id(doc_id), None)

  def test_find(self):
    doc = JsonObject()
    doc.xyz = "xyzvalue"
    updated_doc = self.test_db.update_doc(doc.to_json_map())
    logging.debug(updated_doc)
    found_doc = next(self.test_db.find(find_filter={"xyz": "xyzvalue"}))
    self.assertTrue(JsonObject.make_from_dict(updated_doc).equals_ignore_id(JsonObject.make_from_dict(found_doc)))

  def test_find_one(self):
    doc = JsonObject()
    doc.xyz = "xyzvalue"
    updated_doc = self.test_db.update_doc(doc.to_json_map())
    logging.debug(updated_doc)
    found_doc = self.test_db.find_one(find_filter={"xyz": "xyzvalue"})
    self.assertTrue(JsonObject.make_from_dict(updated_doc).equals_ignore_id(JsonObject.make_from_dict(found_doc)))


if __name__ == '__main__':
  unittest.main()