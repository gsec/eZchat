#==============================================================================#
#                                  ez_gpg.py                                   #
#==============================================================================#

#===========#
#  Imports  #
#===========#

import re
import os
import gnupg
import ez_preferences as ep

#==============================================================================#
#                                 class ez_gpg                                 #
#==============================================================================#

class ez_gpg(object):
  """ Wrapper for python-gnupg to eZchat """

  # setup some default values.
  gpg_path = os.path.join(os.environ['HOME'], '.gnupg')
  gpg_params = {'encoding': "utf-8",
                'init': {'gnupghome': gpg_path},
                'key_server_list': ['keys.gnupg.net', 'pgp.mit.edu']}

  gpg = gnupg.GPG(**gpg_params['init'])
  gpg.encoding = gpg_params['encoding']

  @classmethod
  def find_key(self, nickname=None, secret=False):
    if nickname is None:
      raise ValueError('No nickname given')

    thatkey = [(any(nickname in u for u in key['uids']))
               for key in self.gpg.list_keys(secret)]

    if not any(thatkey):
      raise Exception('Key not found')

    thatkey = self.gpg.list_keys()[thatkey.index(True)]
    return thatkey['fingerprint']

  @classmethod
  def get_active_fingerprint(cls):
    data = 'random'
    signed_data = cls.gpg.sign(data)
    return signed_data.fingerprint

  @classmethod
  def get_name(cls, fingerprint):
    for key in ez_gpg.gpg.list_keys():
      if key['fingerprint'] == fingerprint:
        name = key['uids'][0].split()[0]
        return name

  @classmethod
  def export_key(self, fingerprint=None, nickname=None):
    if fingerprint:
      return self.gpg.export_keys(fingerprint)
    elif nickname:
      try:
        fingerprint = self.find_key(nickname)
      except:
        raise
      return self.gpg.export_keys(fingerprint)

  @classmethod
  def import_key(self, publickey):
    self.gpg.import_keys(publickey)

  @classmethod
  def check_keys(self, key_id=None, remote_check=True):
    """ Check if given `key_id` matches a database.

    If provided with a key ID, first checks locally, then remotely for the key.
    Without arguments it just return all local keys.
    """

    local_list = self.gpg.list_keys()

    if key_id is None:
      return local_list
    elif key_id in [key['keyid'] for key in local_list]:
      #return [{key_id: 'LOCAL'}]
      return key
    elif remote_check:
      remote_list = [key_id for server in self.gpg_params['key_server_list']
                     if self.gpg.recv_keys(server, key_id)]
      if remote_list:
        return remote_list
    raise NameError('Key with ID \'' + key_id + '\' not found')

  @classmethod
  def encrypt_msg(self, nickname, msg):
    cipher = self.gpg.encrypt(msg, nickname, always_trust=True)
    status = cipher.status
    if status != 'encryption ok':
      if status == 'invalid recipient':
        raise Exception('Invalid recipient')
      elif status == '':
        err_msg = ('User `' + nickname + '` propably found, ' +
                   'but trust level must be ultimate.')
        raise Exception(err_msg)

    return cipher

  @classmethod
  def decrypt_msg(self, cipher):
    msg = self.gpg.decrypt(cipher, always_trust=True)
    return msg

  @classmethod
  def sign_msg(self, msg):
    signed_msg = self.gpg.sign(msg)
    return signed_msg

  @classmethod
  def verify_signed_msg(self, signed_msg):
    verified = self.gpg.verify(signed_msg.data)

    if(verified.trust_level is not None and
       verified.trust_level >= verified.TRUST_FULLY):
      fingerprint = verified.__dict__['fingerprint']
      return True, fingerprint
    else:
      return False, None

  @classmethod
  def separate_msg_signature(self, signed_msg):
    pat = '[ \t\r\n\f\v]+(.*?)(?=\n-----BEGIN PGP SIGNATURE-----)'
    try:
      msg = re.search(pat, signed_msg.data, re.MULTILINE).groups(0)[0]
    except:
      raise Exception('Failed to extract the message.')

    return msg
