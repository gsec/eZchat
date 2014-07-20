What this is
------------

A general purpose help and reference page for all different python, coding and
linux(& windows :) stuff.

Python
======
- [Python testing](http://pythontesting.net/start-here/) Introductions to
  Python Testing Frameworks

Advanced nosetests usage I: Coverage
-----------
- [Coverage](http://nose.readthedocs.org/en/latest/plugins/cover.html):
  Nosetests can be nicely convoluted with the coverage module that shows which
  parts of your code is actually accessed
- Install with `pip install coverage`
- To only include our stuff (and not imported modules) in the report, use this sweet alias in your `~/.bashrc`:
```
nosetests_cover_cmd="nosetests --with-coverage --cover-erase --cover-tests --cover-package=`ls *.py | sed -r 's/[.]py$//' | fgrep -v '.' | paste -s -d ',' `"
alias nosetests_cover=$nosetests_cover_cmd
```
- In `eZchat` directory, run `nosetests_cover` from cmdline. You should be able
  to get code coverage to 100 % with appropriate tests.
- Functions which really don't make sense to be tested can get a `def
  function(): # pragma: no cover`

Markdown
========
- [Mastering Markdown](https://guides.github.com/features/mastering-markdown/)
  an introduction from GitHub

Markdown CLI
------------
- Requires: pandoc, lynx
- alias in ~/.bashrc:
    - `myfunc(){pandoc $1 | lynx -stdin}`
    - `alias myalias='myfunc'`
- Do not forget to enable vi-keys in lynx:
    - `o` => `[] Save to disk` => `Accept changes`

Network
=======
- [Nmap and Ports tutorial](https://www.digitalocean.com/community/tutorials/how-to-use-nmap-to-scan-for-open-ports-on-your-vps)
