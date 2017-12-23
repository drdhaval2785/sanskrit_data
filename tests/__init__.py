import logging
from sanskrit_data.db.implementations import mongodb
import os

server_config = {}


TEST_DB_NAME = 'vedavaapi_test'
TEST_CODE_ROOT = os.path.dirname(__file__)


def set_configuration():
  global server_config
  config_file_name = os.path.join(TEST_CODE_ROOT, 'server_config_local.json')
  with open(config_file_name) as fhandle:
    import json
    server_config = json.loads(fhandle.read())


def ullekhanam_db_fixture(request):
  set_configuration()
  server = mongodb.Client(url=server_config["mongo_host"])
  test_db = server.get_database_interface(db_name_backend=TEST_DB_NAME, db_type="ullekhanam_db", external_file_store=os.path.join(TEST_CODE_ROOT, "textract-example-repo/books"))

  def db_teardown():
    server.delete_database(TEST_DB_NAME)
    logging.info("deleting " + TEST_DB_NAME)
  request.addfinalizer(db_teardown)
  return test_db

