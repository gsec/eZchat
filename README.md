eZchat
=======
eZchat is a network-driven decentralized chat program.
It has the flexibility of a P2P network without the drawbacks,
especially it does not require chat partners to be online at the same time.

A `network` is a group of users which are willing to transmit the messages of
the network, similar to torrent users.
Each user is client and server.
Since all messages are encrypted, each user can still only read the messages
that are dedicated to them.
For now, we still need a `tracker` where the IPs of the user of a network are
stored.
An interesting alternative might be the Kademlia algorithm, which would promote
`eZchat` to a truly independent decentralized protocol.

Messages can be addressed to single `persons` or groups.
A `message` can be pure text or have a file associated.
Messages stay in the network and allow to view the chat history.
The only unencrypted information visible is the user name of the recipient and
the time stamp of the message.
Optionally, one can chose to drop messages from the network to the local archive
after some time.

`eZchat` also gives anonymity as it is by construction impossible to tell
whether the `sender` is also the `author` of the message.
