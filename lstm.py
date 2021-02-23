# -*- coding: utf-8 -*-
"""
@author: Manuel Camargo
"""
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import sys
import getopt

from model_prediction import model_predictor as pr
from model_training import model_trainer as tr
# from intercase_feat import intercase_feat_extraction as itf


def catch_parameter(opt):
    """Change the captured parameters names"""
    switch = {'-h': 'help', '-o': 'one_timestamp', '-a': 'activity',
              '-f': 'file_name', '-i': 'imp', '-l': 'lstm_act',
              '-d': 'dense_act', '-p': 'optim', '-n': 'norm_method',
              '-m': 'model_type', '-z': 'n_size', '-y': 'l_size',
              '-c': 'folder', '-b': 'model_file', '-x': 'is_single_exec',
              '-t': 'max_trace_size', '-e': 'splits', '-g': 'sub_group',
              '-v': 'variant', '-r': 'rep'}
    try:
        return switch[opt]
    except:
        raise Exception('Invalid option ' + opt)


# --setup--
def main(argv):
    """Main aplication method"""
    parameters = dict()
    column_names = {'Case ID': 'caseid',
                    'Activity': 'task',
                    'lifecycle:transition': 'event_type',
                    'Resource': 'user'}
    # Similarity btw the resources profile execution (Song e.t. all)
    parameters['rp_sim'] = 0.85
    parameters['batch_size'] = 32 # Usually 32/64/128/256
    # parameters['epochs'] = 1
    # Parameters setting manual fixed or catched by console
    if not argv:
        # Type of LSTM task -> training, pred_log
        # pred_sfx, predict_next, inter_case
        parameters['activity'] = 'pred_log'
        # Event-log reading parameters
        parameters['one_timestamp'] = False  # Only one timestamp in the log
        parameters['read_options'] = {
            'timeformat': '%Y-%m-%dT%H:%M:%S.%f',
            'column_names': column_names,
            'one_timestamp': parameters['one_timestamp'],
            'ns_include': True,
            'filter_d_attrib': False}
        # General training parameters
        if parameters['activity'] in ['training']:
            # Event-log parameters
            parameters['file_name'] = 'PurchasingExample.xes'
            # Specific model training parameters
            if parameters['activity'] == 'training':
                parameters['norm_method'] = 'max'  # max, lognorm
                # # Model types --> shared_cat, shared_cat_inter, shared_cat_rd
                # # cnn_lstm_inter, simple_gan
                parameters['model_type'] = 'shared_cat'
                parameters['imp'] = 1
                parameters['max_eval'] = 2
                parameters['batch_size'] = 32 # Usually 32/64/128/256
                parameters['epochs'] = 2
                parameters['n_size'] = [5, 10, 15]
                parameters['l_size'] = [50, 100, 200] 
                parameters['lstm_act'] = ['selu', 'relu', 'tanh']
                parameters['dense_act'] = ['linear']
                parameters['optim'] = ['Nadam', 'Adam']
                
                if parameters['model_type'] == 'simple_gan':
                    parameters['gan_pretrain'] = False
                # Generation parameters
        elif parameters['activity'] in ['pred_log', 'pred_sfx', 'predict_next']:
            parameters['folder'] = '20210208_AE2236CA_E88C_4EC9_ABC1_17173FD4DCFF'
            parameters['model_file'] = 'confidential_2000.h5'
            parameters['is_single_exec'] = False  # single or batch execution
            # variants and repetitions to be tested Random Choice, Arg Max
            parameters['variant'] = 'Random Choice'
            parameters['rep'] = 5
        elif parameters['activity'] == 'inter_case':
            parameters['file_name'] = 'BPI_Challenge_2017_W_Two_TS_training.csv'
            parameters['mem_limit'] = 1000000
            parameters['sub_group'] = 'inter'  # pd, rw, inter
        else:
            raise ValueError(parameters['activity'])
    else:
        # Catch parameters by console
        try:
            opts, _ = getopt.getopt(
                argv,
                "ho:a:f:i:l:d:p:n:m:z:y:c:b:x:t:e:v:r:",
                ['one_timestamp=', 'activity=',
                 'file_name=', 'imp=', 'lstm_act=',
                 'dense_act=', 'optim=', 'norm_method=',
                 'model_type=', 'n_size=', 'l_size=',
                 'folder=', 'model_file=', 'is_single_exec=',
                 'max_trace_size=', 'splits=', 'sub_group=',
                 'variant=', 'rep='])
            for opt, arg in opts:
                key = catch_parameter(opt)
                if arg in ['None', 'none']:
                    parameters[key] = None
                elif key in ['is_single_exec', 'one_timestamp']:
                    parameters[key] = arg in ['True', 'true', 1]
                elif key in ['imp', 'n_size', 'l_size',
                             'max_trace_size','splits', 'rep']:
                    parameters[key] = int(arg)
                else:
                    parameters[key] = arg
            parameters['read_options'] = {'timeformat': '%Y-%m-%dT%H:%M:%S.%f',
                                          'column_names': column_names,
                                          'one_timestamp': parameters['one_timestamp'],
                                          'filter_d_attrib': False}
        except getopt.GetoptError:
            print('Invalid option')
            sys.exit(2)
#   Execution
    if parameters['activity'] == 'training':
        print(parameters)
        trainer = tr.ModelTrainer(parameters)
        # print(trainer.output, trainer.model, sep=' ')
    elif parameters['activity'] in ['predict_next', 'pred_sfx', 'pred_log']:
        print(parameters['folder'])
        print(parameters['model_file'])
        predictor = pr.ModelPredictor(parameters)
        print(predictor.acc)
    # elif parameters['activity'] == 'inter_case':
    #     parameters['mem_limit'] = 1000000
    #     parameters['sub_group'] = 'inter'
    #     print(parameters)
    #     itf.extract_features(parameters)

if __name__ == "__main__":
    main(sys.argv[1:])
