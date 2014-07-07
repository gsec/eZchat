# creates an user of the network
# feel free to add and edit if you got good ideas
# bcn: The adding part will be in ezc_database.py while we can put
# functionalities and information here. Just as with Message

class User(object):
  """
  - check if user already in database, if not:
  - ask for username, pw
      - create db entry
      - create private/public key pair
      - store public key public
      - store private key? encrypted? suggestions
  - db-entry for groups, network
  - db-entry for with all msg-ids as recipient

  - UNSOLVED: how to store sent messages, without giving up anonymity?
  """

  def generate_keys(self):
      """
      @todo:
      """
      fresh_key       = RSA.generate(self.key_size)
      public_key      = fresh_key.publickey.exportKey(format='PEM')
      private_key     = fresh_key.exportKey(format="PEM")
      return  private_key, public_key
