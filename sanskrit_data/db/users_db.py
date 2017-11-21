import logging
from sanskrit_data.db import DbInterface, mongodb
from sanskrit_data.schema.users import User
from sanskrit_data.db.couchdb import CloudantApiDatabase

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class UsersInterface(DbInterface):
  """Operations on User objects in an Db"""

  def get_user_from_auth_info(self, auth_info):
    """Get a user object matching details in a certain AuthenticationInfo object."""
    user_dict = self.find_one(find_filter={"authentication_infos.auth_user_id": auth_info.auth_user_id,
                                           "authentication_infos.auth_provider": auth_info.auth_provider,
                                           })
    if user_dict is None:
      return None
    else:
      user = User.make_from_dict(user_dict)
      return user

  def get_matching_users_by_auth_infos(self, user):
    # Check to see if there are other entries in the database with identical authentication info.
    matching_users = []
    for auth_info in user.authentication_infos:
      matching_user = self.get_user_from_auth_info(auth_info=auth_info)
      if matching_user is not None:
        matching_users.append(matching_user)
    return matching_users


class UsersMongodb(mongodb.Collection, UsersInterface):
  def __init__(self, some_collection):
    super(UsersMongodb, self).__init__(some_collection=some_collection, db_name_frontend="users")


class UsersCouchdb(CloudantApiDatabase, UsersInterface):
  def __init__(self, some_collection):
    super(UsersCouchdb, self).__init__(db=some_collection)
