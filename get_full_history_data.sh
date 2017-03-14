#!/bin/bash
source venv/bin/activate
touch commits.txt

git log --format="%h" $1'/'$2'.m' >> commits.txt

while read p; do
    git checkout $p $1'/'$2'.m'
    python get_data.py $1 $2
done <commits.txt

rm commits.txt
deactivate
