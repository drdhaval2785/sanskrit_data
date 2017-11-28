# -*- coding: utf-8 -*-
"""
Tests for the ullekhanam_db interface and the associated schema classes.
"""

from __future__ import absolute_import

import logging
import os
import pytest
import jsonschema
import tests
from sanskrit_data.schema import ullekhanam, common, books, users

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


@pytest.fixture(scope='module')
def db_fixture(request):
  return tests.ullekhanam_db_fixture(request=request)


def test_ImageAnnotation_source_auto_set(db_fixture):
  db = db_fixture
  book_portion = books.BookPortion.from_details(
    title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha")
  updated_book = book_portion.update_collection(db)
  target_page_id = updated_book._id
  annotation = ullekhanam.ImageAnnotation()
  annotation.targets=[
    ullekhanam.ImageTarget.from_details(container_id=str(target_page_id),
                                        rectangle=ullekhanam.Rectangle.from_details())]

  # logging.debug(annotation.to_json_map())

  updated_annotation = annotation.update_collection(db_interface=db)
  # logging.debug("update result is " + str(updated_annotation))
  assert(updated_annotation.source.jsonClass == "AnnotationSource")


def test_ImageAnnotation_take_over_while_editing(db_fixture):
  db = db_fixture
  book_portion = books.BookPortion.from_details(
    title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha")
  updated_book = book_portion.update_collection(db)
  target_page_id = updated_book._id
  annotation = ullekhanam.ImageAnnotation.from_details(targets=[
    ullekhanam.ImageTarget.from_details(container_id=str(target_page_id),
                                        rectangle=ullekhanam.Rectangle.from_details())],
    source=ullekhanam.AnnotationSource.from_details("user_supplied", "vingo____rAma"))

  logging.debug(annotation.to_json_map())

  # Write as admin program impersonating rAma
  updated_annotation_1 = annotation.update_collection(db_interface=db)

  with pytest.raises(jsonschema.ValidationError) as exception_info:
    updated_annotation_1.source.id = "vingo____sItA"
    non_admin_user = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="sItA")])
    updated_annotation_2 = updated_annotation_1.update_collection(db_interface=db, user=non_admin_user)
  assert exception_info.value.message.startswith("vingo____sItA cannot take over vingo____rAma's annotation for editing or deleting under a non-admin user")
