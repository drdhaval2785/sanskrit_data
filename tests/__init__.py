import logging
from sanskrit_data.db.implementations import mongodb

server_config = {}


TEST_DB_NAME = 'vedavaapi_test'


def set_configuration():
  import os
  global server_config
  CODE_ROOT = os.path.dirname(__file__)
  config_file_name = os.path.join(CODE_ROOT, 'server_config_local.json')
  with open(config_file_name) as fhandle:
    import json
    server_config = json.loads(fhandle.read())


def ullekhanam_db_fixture(request):
  set_configuration()
  server = mongodb.Client(url=server_config["mongo_host"])
  test_db = server.get_database_interface(db_name_backend=TEST_DB_NAME, db_type="ullekhanam_db")

  def db_teardown():
    server.delete_database(TEST_DB_NAME)
    logging.info("deleting " + TEST_DB_NAME)
  request.addfinalizer(db_teardown)
  return test_db

