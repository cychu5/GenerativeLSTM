# -*- coding: utf-8 -*-
import itertools
import numpy as np
import random
import jellyfish as jf
from operator import itemgetter
#from sklearn.metrics import mean_absolute_error

def gen_mesurement(log_data, simulation_data, features, ramp_io_perc = 0.2):
    
    # get log 
    temp_data = log_data + simulation_data
    alias = create_task_alias(temp_data, features)
    
    log_data = reformat_events(log_data, alias, features )
    # get simulation data
    simulation_data = reformat_events(simulation_data, alias, features)
#    print(simulation_data)
    # cut simulation data avoiding rampage input/output
    num_traces = int(np.round((len(log_data) * ramp_io_perc),0))
    simulation_data = simulation_data[num_traces:-num_traces]
    # select randomly the same number of log traces
    temp_log_data = random.sample(log_data, len(simulation_data))
    # calculate similarity
    JW_sim = measure_distance_JW(temp_log_data, simulation_data)
    DL_sim = measure_distance_DL(temp_log_data, simulation_data)
    mae = measure_mae(temp_log_data, simulation_data)
    DL_T_sim = measure_DL_time(DL_sim)
    return JW_sim, DL_sim, mae, DL_T_sim

def process_results(similarity):
    data = sorted(list(similarity), key=lambda x:x['run_num'])
    run_similarity = list()
    for key, group in itertools.groupby(data, key=lambda x:x['run_num']):
        values = list(group)
        group_similarity = [x['sim_score'] for x in values]
        run_similarity.append(np.mean(group_similarity))
    print(run_similarity)
    print(np.mean(run_similarity))
    # [print(x) for x in similarity]


def measure_distance_JW(log_data, simulation_data):
    similarity = list()
    for sim_instance in simulation_data:
        temp_log_data = log_data.copy()
        max_sim, max_index = 0 , 0
        for i in range(0,len(temp_log_data)):
            sim = jf.jaro_winkler(sim_instance['profile'], temp_log_data[i]['profile'])
            if max_sim < sim:
                max_sim = sim
                max_index = i
        del temp_log_data[max_index]
        similarity.append(dict(caseid=sim_instance['caseid'],sim_score=max_sim))
    return similarity


def measure_distance_DL(log_data, simulation_data):
    similarity = list()
    for sim_instance in simulation_data:
        temp_log_data = log_data.copy()
        min_dist, min_index = jf.damerau_levenshtein_distance(sim_instance['profile'], temp_log_data[0]['profile']) , 0
        for i in range(0,len(temp_log_data)):
            sim = jf.damerau_levenshtein_distance(sim_instance['profile'], temp_log_data[i]['profile'])
            if min_dist > sim:
                min_dist = sim
                min_index = i
        length=np.max([len(sim_instance['profile']), len(temp_log_data[min_index]['profile'])])
        similarity.append(dict(caseid=sim_instance['caseid'],
                               sim_order=sim_instance['profile'],
                               log_order=temp_log_data[min_index]['profile'],
                               sim_tbtw=sim_instance['tbtw_list'],
                               log_tbtw=temp_log_data[min_index]['tbtw_list'],
                               sim_score=(1-(min_dist/length))))
        del temp_log_data[min_index]

    return similarity

def measure_mae(log_data, simulation_data):
    abs_err_list = list()
    for sim_instance in simulation_data:
        temp_log_data = log_data.copy()
        min_dist, min_index = jf.damerau_levenshtein_distance(sim_instance['profile'], temp_log_data[0]['profile']) , 0
        for i in range(0,len(temp_log_data)):
            sim = jf.damerau_levenshtein_distance(sim_instance['profile'], temp_log_data[i]['profile'])
            if min_dist > sim:
                min_dist = sim
                min_index = i
        abs_err = abs(temp_log_data[min_index]['tbtw'] - sim_instance['tbtw'])
        del temp_log_data[min_index]
        abs_err_list.append(dict(caseid=sim_instance['caseid'],abs_err=abs_err))
    return abs_err_list

def measure_DL_time(data):
    similarity = list()
    for record in data:
        length=np.max([len(record['sim_order']), len(record['log_order'])])
        sim2 = damerau_levenshtein_distance(record['sim_order'],
                                            record['log_order'],
                                            record['sim_tbtw'],
                                            record['log_tbtw'])
        similarity.append(1 - (sim2/length))
    return np.mean(similarity)

def create_task_alias(df, features):
    subsec_set = set()
    if isinstance(features, list):
        task_list = [(x[features[0]],x[features[1]]) for x in df]   
    else:
        task_list = [x[features] for x in df]
    [subsec_set.add(x) for x in task_list]
    variables = sorted(list(subsec_set))
    characters = [chr(i) for i in range(0, len(variables))]
    aliases = random.sample(characters, len(variables))
    alias = dict()
    for i, _ in enumerate(variables):
        alias[variables[i]] = aliases[i]
    return alias

def reformat_events(data, alias, features):
    # Add alias
    if isinstance(features, list):
        [x.update(dict(alias=alias[(x[features[0]],x[features[1]])])) for x in data]   
    else:
        [x.update(dict(alias=alias[x[features]])) for x in data]
    # Define cases
    cases = sorted(list(set([x['caseid'] for x in data])))
    # Reformat dataset
    temp_data = list()
    for case in cases:
        temp_dict= dict(caseid=case,profile='',tbtw=0, tbtw_list=list())
        events = sorted(list(filter(lambda x: x['caseid']==case, data)), key=itemgetter('start_timestamp'))
        for i in range(0, len(events)):
            temp_dict['profile'] = temp_dict['profile'] + events[i]['alias']
            temp_dict['tbtw'] = temp_dict['tbtw'] + events[i]['tbtw'] 
            temp_dict['tbtw_list'].append(events[i]['tbtw'])
        temp_dict['start_time'] = events[0]['start_timestamp']
        temp_data.append(temp_dict)
    return sorted(temp_data, key=itemgetter('start_time'))

"""
Compute the Damerau-Levenshtein distance between two given
strings (s1 and s2)
"""
#Normalizacion del mae en relacion con el maximo tiempo de las dos trazas
def damerau_levenshtein_distance(s1, s2, t1, t2):
    d = {}
    max_size = max(t1+t2)
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in range(-1,lenstr1+1):
        d[(i,-1)] = i+1
    for j in range(-1,lenstr2+1):
        d[(-1,j)] = j+1
    for i in range(0, lenstr1):
        for j in range(0, lenstr2):
            if s1[i] == s2[j]:
                cost = abs(t2[j]-t1[i])/max_size
            else:
                cost = 1
            d[(i,j)] = min(
                           d[(i-1,j)] + 1, # deletion
                           d[(i,j-1)] + 1, # insertion
                           d[(i-1,j-1)] + cost, # substitution
                          )
            if i and j and s1[i]==s2[j-1] and s1[i-1] == s2[j]:
                d[(i,j)] = min (d[(i,j)], d[i-2,j-2] + cost) # transposition
 
    return d[lenstr1-1,lenstr2-1]