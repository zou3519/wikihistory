#!/bin/bash
for ((i = 1; i <= 30; ++i)); do
    echo "Processing $i..."
    ./query.py "data/chall/small/challs-$i.csv" -c -s -i "e -a;q"
    ./query.py "data/chall/small/challs-$i.csv" -c -p -i "e -a;q"
    echo "Finished $i."
done
