#!/usr/bin/env python
#encoding: utf-8
import gnupg
import os

# optional arguments: binary, homedir, keyring, secring

def gpg_path(systemwide=True):
  if systemwide:
    return os.path.join(os.environ['HOME'], ".gnupg-test") # remove -test
  else:
    print("I am not a grown-up function yet...")
    #return ep.return_location(ep.key_loc)


def check_key(key_id, remote_check=True):
  """
  @param: key_id
  @type: string
  """
  local_klist = gpg.list_keys()
  if key_id in [key['keyid'] for key in local_klist]:
    #return [{key_id: 'LOCAL'}]
    return key
  elif remote_check:
    remote_klist = [key_id for server in gpg_params['key_server_list']
          if gpg.recv_keys(server, key_id)]
    if remote_klist:
      return remote_klist
  else:
    raise NameError
    print 'shit'

def key_chooser(key_list=None):
  pass
  #if key_list:
    #for

################################################################################
gpg_params =  {
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
          'key_server_list': ['keys.gnupg.net','pgp.mit.edu'],
          }

# :: main ::
gpg = gnupg.GPG(**gpg_params['init'])
gpg.encoding = gpg_params['encoding']

#input_data = gpg.gen_key_input(**gpg_params['key_params'])
#my_key = gpg.gen_key(input_data)
#assert my_key
#print(my_key)
