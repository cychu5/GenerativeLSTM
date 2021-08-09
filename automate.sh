#!/usr/bin/env bash

# This script is used to automate multiple runs of the algorithm without using system-level features.
# The example below was used for the bpic2012o event log. The .txt file name and parameters in the command should be changed accordingly for other event logs.

for m in joint concatenated shared_cat
do
    for run in {0..19}; do
        echo $run >> time_bpic2012o.txt
        date >> time_bpic2012o.txt
        output=`python3 lstm.py -a training -f bpic2012o_all.csv -i 2 -l relu -d linear -p Nadam -n max -m $m -z 5 -y 100 -s 0 | tail -n 1`
        output_arr=( $output )
        folder=${output_arr[0]}
        model=${output_arr[1]}
        echo $folder >> time_bpic2012o.txt
        echo $model >> time_bpic2012o.txt
        date >> time_bpic2012o.txt

        # move output folder to the dev branch for prediction
        mv output_files/$folder ../GenerativeLSTM-dev-git/GenerativeLSTM/output_files/
    done
done
