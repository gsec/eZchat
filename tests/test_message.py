from __future__ import print_function
from test_tools import *

import ezc_message as em
import ezc_user as new_user
from datetime import datetime

#def test_Message():
msg = """ If your public attribute name collides with a reserved keyword,
    append a single trailing underscore to your attribute name. This is
    preferable to an abbreviation or corrupted spelling. (However,
    notwithstanding this rule, 'cls' is the preferred spelling for any
    variable or argument which is known to be a class, especially the first
    argument to a class method.)"""
short_msg = "hi, was geht"
author = 'derEine'
reader = 'derAndere'

new_user.User(author)
new_user.User(reader)

#mx = em.Message(author, reader, msg, dtime = datetime(2014, 07, 06, 17,
  #41, 05))
#print("Testing the basic message object: \n" + str(mx) + str(my))
my = em.Message('derEine','derEine', short_msg)
# at the moment sender=recipient
print("Testing the basic message object: \n" + str(my))

#mx_secret = mx.encrypt()
#print("Encrypted + armored: \n-----\n", mx_secret)
#print("Decrypted again: \n-----\n", mx.decrypt(mx_secret))
#eq_ (mx.sender, author)
#eq_ (mx.recipient, reader)
#eq_ (mx.msg_id, 'f41af76925eddfac4447e4ce2d0a1a03f4af27ba83a99e1e723b91ffccfd54f9')
#eq_ (mx.time, '2014-07-06 17:41:05')

# NOT WORKING
#my.encrypt()
#print("Ciphertext:\n", my.cipher)
#my.decrypt()
#print("Plaintext:\n", my.plain)

# NOT WORKING
#my.var_encrypt()
#print("VARIABLE Ciphertext:\n", my.var_cipher)
#my.var_decrypt()
#print("VARIABLE Plaintext:\n", my.var_plain)
