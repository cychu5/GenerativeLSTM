# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 15:07:19 2020

@author: Manuel Camargo
"""
import os
import glob

import csv
import itertools

import pandas as pd
import numpy as np

from operator import itemgetter

import readers.log_reader as lr
import utils.support as sup
import readers.log_splitter as ls

from model_training.features_manager import FeaturesMannager as feat
from model_training import embedding_training as em
from model_training import model_optimizer as op


class ModelTrainer():
    """
    This is the man class encharged of the model training
    """

    def __init__(self, params):
        """constructor"""
        self.log = self.load_log(params)
        self.output = sup.folder_id()
        self.output_folder = os.path.join('output_files', self.output)
        # Split validation partitions
        self.log_train = pd.DataFrame()
        self.log_test = pd.DataFrame()
        # Activities and roles indexes
        self.ac_index = dict()
        self.index_ac = dict()

        self.rl_index = dict()
        self.index_rl = dict()
        # Training examples
        self.examples = dict()
        # Embedded dimensions
        self.ac_weights = list()
        self.rl_weights = list()
        # Preprocess the event-log
        self.preprocess(params)
        # Train model
        params['output'] = os.path.join('output_files', sup.folder_id())
        optimizer = op.ModelOptimizer(params, 
                                      self.log, 
                                      self.ac_index, 
                                      self.ac_weights,
                                      self.rl_index,
                                      self.rl_weights)
        optimizer.execute_trials()
        print(optimizer.best_output)
        print(optimizer.best_parms)
        print(optimizer.best_loss)


    def preprocess(self, params):
        self.log = feat.add_resources(self.log, params['rp_sim'])
        # indexes creation
        self.indexing()
        # split validation
        self.split_timeline(0.8, params['one_timestamp'])
        # Load embedded matrix
        ac_emb_name = 'ac_' + params['file_name'].split('.')[0]+'.emb'
        rl_emb_name = 'rl_' + params['file_name'].split('.')[0]+'.emb'
        if os.path.exists(os.path.join('input_files',
                                       'embedded_matix',
                                       ac_emb_name)):
            self.ac_weights = self.load_embedded(self.index_ac, ac_emb_name)
            self.rl_weights = self.load_embedded(self.index_rl, rl_emb_name)
        else:
            em.training_model(params,
                              self.log,
                              self.ac_index, self.index_ac,
                              self.rl_index, self.index_rl)
            self.ac_weights = self.load_embedded(self.index_ac, ac_emb_name)
            self.rl_weights = self.load_embedded(self.index_rl, rl_emb_name)
        # Export parameters
        # self.export_parms(params)

    @staticmethod
    def load_log(params):
        params['read_options']['filter_d_attrib'] = False
        log = lr.LogReader(os.path.join('input_files', params['file_name']),
                           params['read_options'])
        log_df = pd.DataFrame(log.data)
        if set(['Unnamed: 0', 'role']).issubset(set(log_df.columns)):
            log_df.drop(columns=['Unnamed: 0', 'role'], inplace=True)
        log_df = log_df[~log_df.task.isin(['Start', 'End'])]
        return log_df

    def indexing(self):
        # Activities index creation
        self.ac_index = self.create_index(self.log, 'task')
        self.ac_index['start'] = 0
        self.ac_index['end'] = len(self.ac_index)
        self.index_ac = {v: k for k, v in self.ac_index.items()}
        # Roles index creation
        self.rl_index = self.create_index(self.log, 'role')
        self.rl_index['start'] = 0
        self.rl_index['end'] = len(self.rl_index)
        self.index_rl = {v: k for k, v in self.rl_index.items()}
        # Add index to the event log
        ac_idx = lambda x: self.ac_index[x['task']]
        self.log['ac_index'] = self.log.apply(ac_idx, axis=1)
        rl_idx = lambda x: self.rl_index[x['role']]
        self.log['rl_index'] = self.log.apply(rl_idx, axis=1)

    @staticmethod
    def create_index(log_df, column):
        """Creates an idx for a categorical attribute.
        parms:
            log_df: dataframe.
            column: column name.
        Returns:
            index of a categorical attribute pairs.
        """
        temp_list = log_df[[column]].values.tolist()
        subsec_set = {(x[0]) for x in temp_list}
        subsec_set = sorted(list(subsec_set))
        alias = dict()
        for i, _ in enumerate(subsec_set):
            alias[subsec_set[i]] = i + 1
        return alias


    def split_timeline(self, size: float, one_ts: bool) -> None:
        """
        Split an event log dataframe by time to peform split-validation.
        prefered method time splitting removing incomplete traces.
        If the testing set is smaller than the 10% of the log size
        the second method is sort by traces start and split taking the whole
        traces no matter if they are contained in the timeframe or not

        Parameters
        ----------
        size : float, validation percentage.
        one_ts : bool, Support only one timestamp.
        """
        # Split log data
        splitter = ls.LogSplitter(self.log)
        train, test = splitter.split_log('timeline_contained', size, one_ts)
        total_events = len(self.log)
        # Check size and change time splitting method if necesary
        if len(test) < int(total_events*0.1):
            train, test = splitter.split_log('timeline_trace', size, one_ts)
        # Set splits
        key = 'end_timestamp' if one_ts else 'start_timestamp'
        test = pd.DataFrame(test)
        train = pd.DataFrame(train)
        self.log_test = (test.sort_values(key, ascending=True)
                         .reset_index(drop=True))
        self.log_train = (train.sort_values(key, ascending=True)
                          .reset_index(drop=True))



    @staticmethod
    def load_embedded(index, filename):
        """Loading of the embedded matrices.
        parms:
            index (dict): index of activities or roles.
            filename (str): filename of the matrix file.
        Returns:
            numpy array: array of weights.
        """
        weights = list()
        input_folder = os.path.join('input_files', 'embedded_matix')
        with open(os.path.join(input_folder, filename), 'r') as csvfile:
            filereader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in filereader:
                cat_ix = int(row[0])
                if index[cat_ix] == row[1].strip():
                    weights.append([float(x) for x in row[2:]])
            csvfile.close()
        return np.array(weights)

    def export_parms(self, parms):
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            os.makedirs(os.path.join(self.output_folder, 'parameters'))

        parms['max_trace_size'] = self.get_max_trace_size(self.log)
        
        parms['index_ac'] = self.index_ac
        parms['index_rl'] = self.index_rl
        
        if not parms['model_type'] == 'simple_gan':
            shape = self.examples['prefixes']['activities'].shape
            parms['dim'] = dict(
                samples=str(shape[0]),
                time_dim=str(shape[1]),
                features=str(len(self.ac_index)))

        sup.create_json(parms, os.path.join(self.output_folder,
                                            'parameters',
                                            'model_parameters.json'))
        self.log_test.to_csv(os.path.join(self.output_folder,
                                          'parameters',
                                          'test_log.csv'),
                             index=False,
                             encoding='utf-8')
    @staticmethod
    def get_max_trace_size(log):
        return int(log.groupby('caseid')['task'].count().max())        

    # def read_model_definition(self, model_type):
    #     Config = cp.ConfigParser(interpolation=None)
    #     Config.read('models_spec.ini')
    #     #File name with extension
    #     self.model_def['additional_columns'] = sup.reduce_list(
    #         Config.get(model_type,'additional_columns'), dtype='str')
    #     self.model_def['scaler'] = Config.get(
    #         model_type, 'scaler')
    #     self.model_def['vectorizer'] = Config.get(
    #         model_type, 'vectorizer')
    #     self.model_def['trainer'] = Config.get(
    #         model_type, 'trainer')
