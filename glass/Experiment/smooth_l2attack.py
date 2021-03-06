# this file is based on https://github.com/locuslab/smoothing
# This is done by Jeremy Cohen, Elan Rosenfeld, and Zico Kolter 

'''
This file is used to test the randomized smoothing against l2 attacks
Type 'python smooth_l2attack.py {}.pt -sigma 1 -outfile output1'
{}.pt is the name of gaussian model you need to train by gaussian_train.py
1 is sigma of gaussian noise (I use same sigma with the sigma training the gaussian model)
output1 is the file name of your output file 
'''


import argparse
from core import Smooth
from time import time
import torch
import datetime
import torch
from origin_train import data_process
import numpy as np
import torchvision
from new_vgg_face import VGG_16
from torchvision import datasets, models, transforms
import os
import copy
import cv2
from l2_attack import pgd2


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Predict on many examples')
    parser.add_argument("model", type=str, help="test_model")
    parser.add_argument("-sigma", type=float, help="noise hyperparameter")
    parser.add_argument("-outfile", type=str, help="output file")
    parser.add_argument("--batch", type=int, default=32, help="batch size")
    parser.add_argument("--skip", type=int, default=1, help="how many examples to skip")
    parser.add_argument("--max", type=int, default=-1, help="stop after this many examples")
    parser.add_argument("--N", type=int, default=1000, help="number of samples to use")
    parser.add_argument("--alpha", type=float, default=0.001, help="failure probability")
    args = parser.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    f = open(args.outfile, 'w')
    print("idx\tlabel\tpredict\tcorrect\ttime", file=f, flush=True)
    batch_size = 1
    dataloaders,dataset_sizes =data_process(batch_size)
    model = VGG_16() 
    model.load_state_dict(torch.load('../donemodel/'+args.model))
    model.to(device)
    smoothed_classifier = Smooth(model, 10, args.sigma)
    
    eps     = [0.5  , 1   , 1.5  , 2   , 2.5  , 3  ]  # eps is epsilon of the l_2 bound 
    alpha   = [0.05 , 0.1 , 0.15 , 0.2 , 0.25 , 0.3]  # alpha is learning rate 
    itera   = [20   , 20  , 20   , 20  , 20   , 20 ]  # iterations to find optimal 
    restart = [1    , 1   , 1    , 1   , 1    , 1  ]  # restart times, since we just do some standard check of our model,
    # we do not use mutliple restarts, but you can change that if you want 
    # delete some hyperparmeters could speed up 

    
    for i in range(len(eps)):
        cor = 0
        tot = 0 
        for k in dataloaders['test']:
            (x, label) = k
            x = x[:,[2,1,0],:,:]
            x = x.to(device)
            labels = label.to(device)
            before_time = time()
            x1 = x + pgd2(model, x, labels, eps[i]*255, alpha[i]*255,itera[i] ,False, restart[i])
            prediction = smoothed_classifier.predict(x1, args.N, args.alpha, args.batch)
            after_time = time()
            cor += int(prediction == int(label))
            time_elapsed = str(datetime.timedelta(seconds=(after_time - before_time)))
            # log the prediction and whether it was correct
            print("{}\t{}\t{}\t{}\t{}".format(i, label, prediction, cor, time_elapsed), file=f, flush=True)
            

    f.close()


