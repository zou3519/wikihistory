#!/bin/bash
for ((i = 1; i <= 30; ++i)); do
    tools/avg.py "data/chall/small/challs-$i-s-ea.dat"
done
