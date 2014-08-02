#!/bin/bash
rm deps.dot
echo 'digraph {' >> deps.dot
grep 'import ' *.py | sed 's/.py:from/" -> "/' | sed 's/.py:import/" -> "/' | sed 's/ as.*//' | sed 's/ import.*//' | sed 's/ #.*//' | sed 's/ *$//' | sed 's/$/"/' | sed 's/^/" /' | sed 's/\..*"/"/' | uniq >> deps.dot
echo '}' >> deps.dot
dot -Tpdf -o deps.pdf deps.dot
