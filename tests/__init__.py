
server_config = {}

def set_configuration():
  import os
  global server_config
  CODE_ROOT = os.path.dirname(__file__)
  config_file_name = os.path.join(CODE_ROOT, 'server_config_local.json')
  with open(config_file_name) as fhandle:
    import json
    server_config = json.loads(fhandle.read())

