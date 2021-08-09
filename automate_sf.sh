#!/usr/bin/env bash

# This script is used to automate multiple runs of the algorithm using system-level features.
# The example below was used for the bpic2012o event log. The .txt file name and parameters in the command should be changed accordingly for other event logs.

for m in concatenated_sf 
do
    for run in {0..5}; do
        echo $run >> time_bpic2012o.txt
        for sf in curr_active_cases curr_active_resources curr_unique_traces events_within_interval_12h events_within_interval_1d events_within_interval_7d events_within_interval_14d events_within_interval_30d resources_within_interval_12h resources_within_interval_1d resources_within_interval_7d resources_within_interval_14d resources_within_interval_30d entry_rate_12h entry_rate_1d entry_rate_7d entry_rate_14d entry_rate_30d exit_rate_12h exit_rate_1d exit_rate_7d exit_rate_14d exit_rate_30d
        do
            echo $sf >> time_bpic2012o.txt
            date >> time_bpic2012o.txt

            # training
            output=`python3 lstm.py -a training -f bpic2012o_all.csv -i 2 -l relu -d linear -p Nadam -n max -m $m -z 5 -y 100 -s 0 -u $sf | tail -n 1`
            output_arr=( $output )
            folder=${output_arr[0]}
            model=${output_arr[1]}
            date >> time_bpic2012o.txt

            # prediction
            python3 lstm.py -a pred_sfx -c "$folder" -b "$model" -v 'arg_max' -r 1 -s 0 -x 0 -u "$sf" 
            date >> time_bpic2012o.txt
        done
    done
done
