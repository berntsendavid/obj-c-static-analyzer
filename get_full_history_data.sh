#!/bin/bash
source venv/bin/activate
touch commits.txt

git log --format="%h" $1 >> commits.txt

python obj-c-static-analyzer/get_data.py $1 # get the current commit first

while read p; do
    git checkout -f -q --detach $p
    python obj-c-static-analyzer/get_data.py $1
done <commits.txt

rm commits.txt
deactivate
