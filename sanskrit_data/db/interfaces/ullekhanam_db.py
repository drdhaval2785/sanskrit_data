import re
import logging
import os

from sanskrit_data.schema import books
from sanskrit_data.schema import common
from sanskrit_data.db.interfaces import DbInterface

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def run_command(cmd):
  try:
    # shellswitch = isinstance(cmd, collections.Sequence)
    # print "cmd:",cmd
    # print "type:",shellswitch
    shellval = False if (type(cmd) == type([])) else True
    result = subprocess.Popen(cmd, shell=shellval,
                              stderr=subprocess.PIPE,
                              stdout=subprocess.PIPE).communicate()
    if result[1] != "" and result[1] != b"":
      logging.error(cmd)
      logging.error(result)
      raise Exception(result[1])
    return result[0].decode("utf-8")  # Returns the STDOUT
  except Exception as e:
    logging.error("Error in " + str(cmd) + ": " + str(e))
    raise e


class BookPortionsInterface(DbInterface):
  """Operations on BookPortion objects in an Db"""

  def import_all(self, rootdir, pattern=None):
    logging.info("Importing books into database from " + rootdir)
    cmd = "find " + rootdir + r" \( \( -path '*/.??*' \) -prune \) , \( -path '*book_v2.json' \) -follow -print; true"
    logging.info(cmd)
    try:
      from sanskrit_data.file_helper import run_command
      results = run_command(cmd)
    except Exception as e:
      logging.error("Error in find: " + str(e))
      return 0

    nbooks = 0

    for f in results.split("\n"):
      if not f:
        continue
      bpath, fname = os.path.split(f.replace(rootdir + "/", ""))
      logging.info("    " + bpath)
      if pattern and not re.search(pattern, bpath, re.IGNORECASE):
        continue
      book = books.BookPortion.from_path(path=bpath, db_interface=self)
      if book is not None:
        logging.info("Book already present %s" % bpath)
      else:
        book_portion_node = common.JsonObject.read_from_file(f)
        book_portion_node.setup_source(source=common.DataSource.from_details(source_type="system_inferred", id="book_importer"))
        logging.info("Importing afresh! %s " % book_portion_node)
        from jsonschema import ValidationError
        try:
          book_portion_node.update_collection(self)
        except ValidationError as e:
          import traceback
          logging.error(e)
          logging.error(traceback.format_exc())
        logging.debug(str(book_portion_node))
        nbooks = nbooks + 1
    return nbooks

  def list_books(self):
    """ List book objects (not chapters or pages).

    :return:
    """
    return self.find(find_filter={"portion_class": "book"})

  def get(self, path):
    book = books.BookPortion.from_path(path=path, db_interface=self)
    book_node = common.JsonObjectNode.from_details(content=book)
    book_node.fill_descendents(self)
    return book_node

  def update_image_annotations(self, page, page_image):
    """return the page annotation with id = anno_id"""
    from os import path
    known_annotations = page.get_targetting_entities(db_interface=self,
                                                     entity_type=ullekhanam.ImageAnnotation.get_wire_typeid())
    if len(known_annotations):
      logging.warning("Annotations exist. Not detecting and merging.")
      return known_annotations
      # # TODO: fix the below and get segments.
      # #
      # # # Give me all the non-overlapping user-touched segments in this page.
      # for annotation in known_annotations:
      #   target = annotation.targets[0]
      #   if annotation.source.source_type == 'human':
      #     target['score'] = float(1.0)  # Set the max score for user-identified segments
      #   # Prevent image matcher from changing user-identified segments
      #   known_annotation_targets.insert(target)

    # Create segments taking into account known_segments
    detected_regions = page_image.find_text_regions()
    logging.info("Matches = " + str(detected_regions))

    new_annotations = []
    for region in detected_regions:
      del region.score
      # noinspection PyProtectedMember
      target = ullekhanam.ImageTarget.from_details(container_id=page._id, rectangle=region)
      annotation = ullekhanam.ImageAnnotation.from_details(
        targets=[target], source=ullekhanam.DataSource.from_details(source_type='system_inferred', id="pyCV2"))
      annotation = annotation.update_collection(self)
      new_annotations.append(annotation)
    return new_annotations
