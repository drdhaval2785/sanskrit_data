# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import logging
import unittest

import sanskrit_data.schema.books
from sanskrit_data.schema import common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class SchemaTest(unittest.TestCase):
  def test_getSchemas(self):
    logging.info(common.get_schemas(common))
    from sanskrit_data.schema import books
    logging.info(common.get_schemas(books))

  def test_PickleDepickle(self):
    book_portion = sanskrit_data.schema.books.BookPortion.from_details(
      title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha",
      targets=[common.Target.from_details(container_id="xyz")])
    json_str = str(book_portion)
    logging.info("json_str pickle is " + json_str)
    obj = common.JsonObject.make_from_pickledstring(json_str)
    logging.info(obj.__class__)
    logging.info(obj)

    jsonMap = {u'jsonClass': u'BookPortion', u'title': u'halAyudhakoshaH', u'path': u'myrepo/halAyudha',
               u'targets': [{u'jsonClass': u'Target', u'container_id': u'xyz'}]}
    json_str = json.dumps(jsonMap)
    logging.info("json_str pickle is " + json_str)
    obj = common.JsonObject.make_from_pickledstring(json_str)
    logging.info(obj.__class__)
    logging.info(obj)

