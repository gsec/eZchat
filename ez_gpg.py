#!/usr/bin/env python
#encoding: utf-8
import re
import os
import gnupg
import ez_preferences as ep

###############
#  functions  #
###############

class ez_gpg(object):

  """Docstring for ez_gpg. """
  # ep.join(ep.location['gpg'], fname)
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

    @param: key_id
    @type:  string
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
  def generate_key(self, user=None, params=None, secret=True):
    """ Generates a gpg-key object and exports it to a file.

    The `params` dictionary contains various options, see
    gpg_params['key_params'] for required fields.

    @param: user
    @type:  string

    @param: params
    @type:  dict

    @param: secret
    @type:  bool
    """

    if params is None:
      key_params = {'key_type': "RSA",
                    'key_length': 4096,
                    'name_real': os.environ['USER'],
                    'name_comment': "eZchat communication key"}
      params = self.gpg.gen_key_input(**key_params)

    new_key = self.gpg.gen_key(params)

    if user:
      if secret:
        ext = 'sec'
      else:
        ext = 'pub'
      uname = '.'.join((user, ext))
      with open(self.gpg_path(fname=uname), 'w') as f:
        f.write(new_key.gpg.export_keys(new_key.fingerprint, secret))
    else:
      return new_key

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
    msg = self.gpg.decrypt(cipher.data, always_trust=True)
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
      fingerprint = verified.__dict__['pubkey_fingerprint']
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

################################################################################
#                                     main                                     #
################################################################################

if __name__ == '__main__':
  pass
  #ez_gpg.generate_key('yolo')
  #data = 'randomdata'
  #import ez_user as eu
  #for key in ez_gpg.gpg.list_keys():
    #name = key['uids'][0].split()[0]
    #fingerprint = key['fingerprint']
    #if not eu.user_database.in_DB(UID=fingerprint):
      #new_user = eu.User(UID=fingerprint, name=name)
      #eu.user_database.add_entry(new_user)

    #print "uid:", uid
    #print "fingerprint:", fingerprint

  #with open('ez.pub', 'r') as f:
    #ez_key = f.read()
    #ez_gpg.gpg.import_keys(ez_key)

    #f.write(ez_gpg.gpg.export_keys(u'8D38E2A7CC1D9602'))
  #print(gpg.list_keys())
  #print find_key('gsec')
  #fp = find_key('gsec')
  #print  gpg.import_keys(fp)
  #print gpg.encrypt(data, fp)
  #try:
    #print ez_gpg.encrypt_msg('yolo', data)
  #except Exception as e:
    #print(e)

  #signed_data = ez_gpg.gpg.sign(data.data)

  #stream = open("example.txt", "rb")

  #import ez_message as em
  #sender = 'jlang'
  #recipient = u'jlang'
  #msg = 'hi'
  #print ez_gpg.gpg.list_keys(True)
  #print ez_gpg.find_key(nickname='jlang', secret=True)
  #cipher = ez_gpg.decrypt_msg(ez_gpg.encrypt_msg(recipient, msg))
  #print cipher
  #import sys
  #import cPickle as pickle
  #print "cipher.status:", cipher.status
  #ccipher = pickle.dumps(cipher)

  #print sys.getsizeof(ccipher)

  #print ez_gpg.gpg.list_keys()
  #mx = em.Message(sender, recipient, msg)
  #print "mx:", mx.clear_text()
  ##print "mx.__dict__:", mx.__dict__

  #signed_data = ez_gpg.gpg.sign(data)
  #print "signed_data:", signed_data.data
  #import re
  #pat = re.compile('Version: [ \t\r\f\v]*\n(.*)\n(?=-----BEGIN PGP SIGNATURE-----)+?')
  #msg = re.search('[ \t\r\n\f\v]+(.*?)(?=\n-----BEGIN PGP SIGNATURE-----)', signed_data.data, re.MULTILINE)
  #print "msg.groups():", msg.groups()[0]
  #print "signed_data.data:", signed_data.data
  #verified = ez_gpg.gpg.verify(signed_data.data)
  #print "verified:", verified.__dict__['pubkey_fingerprint']
  #if verified.trust_level is not None and verified.trust_level >= verified.TRUST_FULLY:
    #print('Trust level: %s' % verified.trust_text)

  #print "Verified" if verified else "Unverified"

  #print ez_gpg.export_key(nickname='eZchat')
