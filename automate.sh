#!/usr/bin/env bash

folders=('20210719_5C4660ED_0F1B_47BF_91E6_80EDBD8FC192' '20210719_726BA1AA_F78B_458A_A6FF_D366B6D5E5FA')
models=('model_joint_04-1.94.h5' 'model_joint_01-1.70.h5')

for run in {0..2}; do
    echo $run >> time.txt
    date >> time.txt
    folder=${folders[$run]}
    model=${models[$run]}
    python3 lstm.py -a pred_sfx -c "$folder" -b "$model" -v 'arg_max' -r 1 -s 0 -x 0 
    date >> time.txt
done
