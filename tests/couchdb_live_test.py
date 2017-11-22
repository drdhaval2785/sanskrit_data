from __future__ import absolute_import

import logging
import unittest

import tests
from sanskrit_data.db.implementations.couchdb import CloudantApiClient

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class TestLiveDB(unittest.TestCase):
  TEST_DB_NAME = 'vedavaapi_ullekhanam_db'

  def setUp(self):
    tests.set_configuration()
    self.server = CloudantApiClient(tests.server_config["couchdb_host"])
    self.live_db_interface = self.server.get_database_interface(db_name_backend=self.TEST_DB_NAME)
    self.db = self.live_db_interface.db

  def test_update_doc(self):
    doc = self.live_db_interface.find_by_id(id="37c1d704a01a462c8a77d9d4e53d4b11")
    logging.debug(id in self.db)
    logging.debug(doc)
