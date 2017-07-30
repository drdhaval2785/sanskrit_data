
class DbInterface(object):

  def update_doc(self, doc):
    """ Update or insert a JsonObject.
    
    :param doc: JsonObject. _id parameter determines the key. One will be created if it does not exist.
    :return: updated JsonObject with _id set. 
    """
    doc.set_type_recursively()
    pass

  def delete_doc(self, doc):
    """
    
    :param doc: 
    :return: Not used.
    """
    pass

  def find_by_indexed_key(self, index_name, key):
    pass

  def find_by_id(self, id):
    """
    
    :param id: 
    :return: Returns None if nothing is found. Else a python dict representing a JSON object.
    """
    pass

  def find(self, filter):
    """ Fine matching objects from the database.
    
    Should be a generator and return an iterator: ie it should use the yield keyword.
    :param filter: A mango or mongo query.
    :return: Returns None if nothing is found. Else a python dict representing a JSON object.
    """
    pass

  def find_one(self, filter):
    """ Fine one matching object from the database.
    
    :param filter: A mango or mongo query.
    :return: Returns None if nothing is found. Else a python dict representing a JSON object.
    """
    iterator = self.find(filter=filter)
    try:
      return iterator.next()
    except StopIteration:
      return None

  def get_targetting_entities(self, json_obj, entity_type=None):
    """ Find entities targeting a JsonObjectWithTarget (Refer to sanskrit_data package.)
    
    :param json_obj: JsonObject
    :param entity_type: 
    :return: A list of JsonObjectWithTarget objects. 
    """
    pass

  def get_no_target_entities(self):
    pass