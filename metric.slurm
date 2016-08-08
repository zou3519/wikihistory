#!/bin/bash
#SBATCH -p general
#SBATCH -J metric
#SBATCH -n 1
#SBATCH -N 1
#SBATCH -t 0-3:00
#SBATCH --mem 8000
#SBATCH -o test_%j.out
#SBATCH -e test_%j.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=gdiehl@hmc.edu

module load python/2.7.11-fasrc01
python metric.py "Hillary Clinton" -r -n -a "test"