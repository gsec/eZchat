#==============================================================================#
#                                   ez_user                                    #
#==============================================================================#

# creates a user of the network
# bcn: The adding part will be in ez_database.py while we can put
# functionalities and information here. Just as with Message

#==============================================================================#
#                                  class User                                  #
#==============================================================================#
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
  def __init__(self, name, public_key, current_ip):
    self.name = name
    self.public_key = public_key
    self.current_ip = current_ip
