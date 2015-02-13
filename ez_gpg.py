#!/usr/bin/env python
#encoding: utf-8
import gnupg
import os
import ez_preferences as ep

###############
#  functions  #
###############


def gpg_path(systemwide=False, fname=None):
  if systemwide:
    return os.path.join(os.environ['HOME'], ".ez_gnupg")  # eventually .gnupg
  else:
    return ep.join(ep.location['gpg'], fname)


def check_keys(key_id=None, remote_check=True):
  """ Check if given `key_id` matches a database.

  If provided with a key ID, first checks locally, then remotely for the key.
  Without arguments it just return all local keys.

  @param: key_id
  @type: string
  """

  local_list = gpg.list_keys()

  if key_id is None:
    return local_list
  elif key_id in [key['keyid'] for key in local_list]:
    #return [{key_id: 'LOCAL'}]
    return key
  elif remote_check:
    remote_list = [key_id for server in gpg_params['key_server_list']
          if gpg.recv_keys(server, key_id)]
    if remote_list:
      return remote_list
  raise NameError('Key with ID \'' + key_id + '\' not found')


def generate_key(user=None, params=None, secret=True):
  """ Generates a gpg-key object and exports it to a file.

  The `params` dictionary contains various options, see gpg_params['key_params']
  for required fields.

  @param: user
  @type:  string

  @param: params
  @type:  dict

  @param: secret
  @type:  bool
  """

  if params is None:
    params = gpg.gen_key_input(**gpg_params['key_params'])

  new_key = gpg.gen_key(params)

  if user:
    if secret:
      ext = 'sec'
    else:
      ext = 'pub'
    uname = '.'.join((user, ext))
    with open(gpg_path(fname=uname), 'w') as f:
      f.write(new_key.gpg.export_keys(new_key.fingerprint, secret))
  else:
    return new_key

######################
#  Global instances  #
######################
# TODO: exchange some of them with ez_preferences variable


gpg_params = {
              'encoding': "utf-8",
              'init': {
                       'gnupghome': gpg_path()
                       },
              'key_params': {
                             'key_type': "RSA",
                             'key_length': 4096,
                             'name_real': os.environ['LOGNAME'],
                             'name_comment': "eZchat communication key",
                             #'name_email': "<your-email@here.net>"
                             },
              'key_server_list': ['keys.gnupg.net', 'pgp.mit.edu'],
              }

gpg = gnupg.GPG(**gpg_params['init'])
gpg.encoding = gpg_params['encoding']

################################################################################
#                                     main                                     #
################################################################################

if __name__ == '__main__':
  generate_key(gpg_params['key_params']['name_real'])
