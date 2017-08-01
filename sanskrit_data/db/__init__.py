"""
This package aims to achieve database neutrality - we abstract database-client operations and database operations using interfaces so as to enable one to easily switch the database one uses.
"""

__all__ = ["couchdb", "mongodb"]

class ClientInterface(object):
  def get_database(self):
    """Create or get a database."""
    pass

  def delete_database(self):
    pass


class DbInterface(object):
  def update_doc(self, doc):
    """ Update or insert a JsonObject.
    
    :param doc: A dict. _id parameter determines the key. One will be created if it does not exist. This argument could be modified.
    :return: updated dict with _id set.
    """
    assert isinstance(doc, dict)
    pass

  def delete_doc(self, doc_id):
    """
    
    :param doc_id:
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
