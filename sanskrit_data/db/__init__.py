"""
This package aims to achieve database neutrality - we abstract database-client operations and database operations using interfaces so as to enable one to easily switch the database one uses.

"""

# Sphinx uses the all list to check every module is loaded, but in some cases it is not and a warning is generated:
#   missing attribute mentioned in :members: or __all__: module
"""Allows users to do ``from xyz import *`` """
__all__ = ["ClientInterface", "DbInterface", "couchdb", "mongodb"]


class ClientInterface(object):
  """A common interface to a database server or system.

  Accessing databases through implementations of this interface enables one to switch databases more easily down the line.
  """

  def get_database(self, db_name):
    """Create or get a database, with which one can instantiate a suitable DbInterface subclass.

    While it is better to use :meth:`get_database_interface` generally, we expose this in order to support :class:`DbInterface` subclasses which may be defined outside this module.
    :param str db_name: Name of the database which needs to be accessed (The database is created if it does not already exist).
    :returns DbInterface db: A database interface implementation for accessing this database.
    """
    pass

  def get_database_interface(self, db_name):
    """Create or get a suitable :class:`DbInterface` subclass.

    :param str db_name: Name of the database which needs to be accessed (The database is created if it does not already exist).
    :returns DbInterface db: A database interface implementation for accessing this database.
    """
    pass

  def delete_database(self, db_name):
    """Delete a database, with which one can instantiate a suitable DbInterface subclass.

    :param str db_name: Name of the database which needs to be deleted.
    """
    pass


class DbInterface(object):
  """A common interface to a database.

  Accessing databases through implementations of this interface enables one to switch databases more easily down the line.
  """

  def update_doc(self, doc):
    """ Update or insert a json object, represented as a dict.
    
    :param dict doc: _id parameter determines the key. One will be created if it does not exist. This argument could be modified.
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

  # noinspection PyShadowingBuiltins
  def find_by_id(self, id):
    """
    
    :param id: 
    :return: Returns None if nothing is found. Else a python dict representing a JSON object.
    """
    pass

  def find(self, find_filter):
    """ Find matching objects from the database.
    
    Should be a generator and return an iterator: ie it should use the yield keyword.

    :param dict find_filter: A mango or mongo query.
    :return: Returns None if nothing is found. Else a python dict representing a JSON object.
    """
    pass

  def find_one(self, find_filter):
    """ Fine one matching object from the database.
    
    :param find_filter: A mango or mongo query.
    :return: Returns None if nothing is found. Else a python dict representing a JSON object.
    """
    return next(self.find(find_filter=find_filter), None)

  def update_index(self, name, fields, upsert=False):
    """Create or update (if upsert=True) an index over certain fields, with a given name."""
    pass

  def add_index(self, keys_json, index_name):
    """Index the database using certain fields.

    :param index_name:
    :param keys_json: A document that contains the field and value pairs where the field is the index key and the value describes the type of index for that field. For an ascending index on a field, specify a value of 1; for descending index, specify a value of -1.
    """
    pass
