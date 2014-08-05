eZchat [![Build Status](https://travis-ci.org/gsec/eZchat.svg?branch=master)](https://travis-ci.org/gsec/eZchat)
=======
Manifesto
--------------------------------------------------------------------------------
eZchat is a network-driven decentralized chat program.
It has the flexibility of a P2P network without the drawbacks,
especially it does not require chat partners to be online at the same time.

A `network` is a group of users willing to transmit the messages of
the network, similar to torrent users.
All users are client and server at the same time.
Since all messages are encrypted, each user can only read the messages
that are dedicated to them.
For now, we still need a `tracker` where the IPs of the user of a network are
stored, as well as at least one user that accepts incoming connections.
An interesting alternative might be the Kademlia algorithm, which would promote
`eZchat` to a truly independent decentralized protocol.

Messages can be addressed to single `persons` or groups.
A `message` can be pure text or have a file associated.
Messages stay in the network and can be viewed the chat history.
The only unencrypted information visible, is the user name of the recipient and
the time stamp of the message.
Optionally, one can chose to drop messages from the network to the local archive
after some time.

`eZchat` also gives anonymity as it is by construction impossible to tell
whether the `sender` is also the `author` of the message.

Dependencies
--------------------------------------------------------------------------------
Install dependencies using `pip`:
- `pip install -r requirements.txt`

Development
--------------------------------------------------------------------------------
Contributors should have a look at the [Developer 
Guidelines](https://github.com/gsec/eZchat/wiki/Developer-Guidelines).

As we are still in heavy development, you might want to check
[Travis](https://travis-ci.org/gsec/eZchat) to see the current build status of
the continuous integration server.
