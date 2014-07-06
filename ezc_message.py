#! /usr/bin/env python
# -*- coding: utf_8 -*-

from __future__ import print_function
from datetime import datetime
from base64 import b64encode, b64decode
from Crypto.Hash import SHA256 as SHA   # considered more secure than SHA1
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

class Message(object):
    """
    Creates a message object with and unique ID based on sender, recipient and
    exact creation time. Encrypts or decrypts content if provided with keys.
    @todo: message size limited by the key though!!!
        further implementation of AES needed for msg_size to be arbitrary
    """
    def __init__(self, sender, recipient, content, datatype='text'):
        _time           = datetime.now()
        self.time       = _time.ctime()
        self.sender     = sender
        self.recipient  = recipient
        self.content    = content
        self.datatype   = datatype

        self.key_size   = 4096          # 2048 bits considered secure

        self.private_key, self.public_key = self.generate_keys()
        # pubkey of RECIPIENT, private key of SENDER

        self.msg_id     = SHA.new(self.sender + self.recipient + \
                str(_time)).hexdigest()

    def __str__(self):
        return "\nFrom: " + self.sender + "\tTo: " + self.recipient + "\n@ "  \
                + self.time + "\n---\n" + self.content + "\n---\n" +          \
                "Message ID: " + self.msg_id + " (" + self.datatype + ")" +   \
                "\n+++++++++++++\n"

    def generate_keys(self):
        """
        @todo: temporarily duplicate of function in ezc_create_user.py
        should at the end be imported from (secured) files
        """
        fresh_key   = RSA.generate(self.key_size)
        public_key  = fresh_key.publickey().exportKey(format='PEM')
        private_key = fresh_key.exportKey(format="PEM")
        return  private_key, public_key

    def encrypt(self):
        """
        @todo:
        """
        armored_key = RSA.importKey(self.public_key)
        public_key  = PKCS1_OAEP.new(armored_key)
        cipher      = public_key.encrypt(self.content)
        return cipher.encode('base64')

    def decrypt(self, ciphertext):
        armored_key = RSA.importKey(self.private_key)
        private_key = PKCS1_OAEP.new(armored_key)
        plaintext   = private_key.decrypt(ciphertext.decode('base64'))
        return plaintext

#::: main :::

MSG = """If your public attribute name collides with a reserved keyword, append
a single trailing underscore to your attribute name. This is preferable to an
abbreviation or corrupted spelling. 
But yield isn’t even allowed inside a try-finally in 2.4 and earlier. And while 
that could be fixed (and it has been fixed in 2.5), it’s still a bit weird to 
use a loop construct when you know that you only want to execute something 
once."""
short_msg = "hi, was geht"

mx = Message('derEine','derAndere', MSG)
my = Message('derType','demGone', short_msg)
mx_geheim = mx.encrypt()

print(my)
print(mx)
print("Encrypted + armored: \n-----\n", mx_geheim)
print("Decrypted again: \n-----\n", mx.decrypt(mx_geheim))
