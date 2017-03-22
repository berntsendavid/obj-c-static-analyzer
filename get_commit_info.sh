#!/bin/bash

date=$(git log --pretty=format:"%cd" --date=short $1)
hash=$(git log --pretty=format:"%h" $1)
changes=$(git log --pretty=format:"" --numstat $1)
counter=1
line_changes=0
array_changes=()
for i in $date
do
    echo $i
done
echo '****************'
for i in $hash
do
    echo $i
done
echo '****************'
for i in $changes
do
    if [ `echo $counter % 3 | bc` -eq 1 ]; then
       line_changes=$i
       counter=$((counter+1))
    elif [ `echo $counter % 3 | bc` -eq 2 ]; then
        line_changes=$((line_changes+i))
        counter=$((counter+1))
    else
        echo $line_changes
        counter=1
    fi
done
