# creates an user of the network
# feel free to add and edit if you got good ideas
# bcn: The adding part will be in ezc_database.py while we can put
# functionalities and information here. Just as with Message

#import rsa # Key generation should be done by ezc_crypto. Pls fix
#KEY_SIZE = 1024

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
