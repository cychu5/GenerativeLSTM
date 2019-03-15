# -*- coding: utf-8 -*-
"""
@author: Manuel Camargo
"""
import sys
import getopt
import n_gram_emb_training as tr
import embedding_training as em
import predict_n_gram_emb as pr
import predict_prefix as px


def catch_parameter(opt):
    """Change the captured parameters names"""
    switch = {'-h':'help', '-i':'imp', '-l':'lstm_act',
              '-d':'dense_act', '-n':'norm_method', '-f':'folder',
              '-m':'model_file', '-t':'model_type', '-a':'activity',
              '-e':'file_name', '-b':'n_size', '-c':'l_size', '-o':'optim'}
    try:
        return switch[opt]
    except:
        raise Exception('Invalid option ' + opt)

# --setup--
def main(argv):
    """Main aplication method"""

    timeformat = '%Y-%m-%dT%H:%M:%S.%f'
    parameters = dict()
#   Parameters setting manual fixed or catched by console for batch operations
    if not argv:
#       Type of LSTM task -> emb_training, training, pred_log, pred_sfx
        parameters['activity'] = 'training'
#       General training parameters
        if parameters['activity'] in ['emb_training', 'training']:
            parameters['file_name'] = 'Helpdesk.xes.gz'
#       Specific model training parameters
            if parameters['activity'] == 'training':
                parameters['imp'] = 1 # keras lstm implementation 1 cpu, 2 gpu
                parameters['lstm_act'] = None # optimization function see keras doc
                parameters['dense_act'] = None # optimization function see keras doc
                parameters['optim'] = 'Nadam' # optimization function see keras doc
                parameters['norm_method'] = 'max' # max, lognorm
                # Model types --> specialized, concatenated, shared_cat, joint, shared
                parameters['model_type'] = 'concatenated'
                parameters['n_size'] = 5 # n-gram size
                parameters['l_size'] = 100 # LSTM layer sizes
#       Generation parameters
        if parameters['activity'] in ['pred_log', 'pred_sfx']:
            parameters['folder'] = '20190306_205146800602'
            parameters['model_file'] = 'model_rd_50 Nadam_05-1.63.h5'

    else:
#       Catch parameters by console
        try:
            opts, _ = getopt.getopt(argv, "hi:l:d:n:f:m:t:a:e:b:c:o:",
                                    ["imp=", "lstmact=", "denseact=", "norm=",
                                     'folder=', 'model=', 'mtype=',
                                     'activity=', 'eventlog=', 'batchsize=',
                                     'cellsize=', 'optimizer='])
            for opt, arg in opts:
                parameters[catch_parameter(opt)] = arg
        except getopt.GetoptError:
            print('Invalid option')
            sys.exit(2)

#   Execution
    try:
        if parameters['activity'] == 'emb_training':
            print(parameters)
            em.training_model(parameters['file_name'], timeformat, timeformat)
        elif parameters['activity'] == 'training':
            print(parameters)
            tr.training_model(parameters['file_name'], timeformat, timeformat, parameters)
        elif parameters['activity'] == 'pred_log':
            print(parameters['folder'])
            print(parameters['model_file'])
            pr.predict(timeformat, parameters['folder'],
                       parameters['model_file'],
                       is_single_exec=False)
        elif parameters['activity'] == 'pred_sfx':
            print(parameters['folder'])
            print(parameters['model_file'])
            px.predict_prefix(timeformat, parameters['folder'],
                              parameters['model_file'],
                              is_single_exec=False)
    except:
        raise Exception('Missing parameters...')


if __name__ == "__main__":
    main(sys.argv[1:])
