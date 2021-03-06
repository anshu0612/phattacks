# this file is based on https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html
# Author: Sasank Chilamkurthy

'''
We use this file to do the gausian training in order to do Randomized smoothing 
Type 'python linf_retrain.py {}.pt -out 70 -sigma 1' to run
{} name of your model want to train from a clean model, right now it is training from pretrain weight,
so type something to fill in {}
70 is name of your output models, number is fine 
1 is sigma of gaussian 
other hyperparameter is defult, like epochs of training is 30, learning rate is ...
'''


import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import numpy as np
import time
import cv2
import torchfile
from origin_train import data_process
import argparse
import copy
#from save_image import save_image
#uncomment to see some images 
from origin_test import test
from new_vgg_face import VGG_16


def gauss_train_model(model,sigma, criterion, optimizer, scheduler, num_epochs=10):
    since = time.time()
    
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0
    mean = torch.Tensor(np.array([129.1863, 104.7624, 93.5940])).view(1, 3, 1, 1) # bgr mean

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)
        # Each epoch has a training and validation phase
        for phase in ['train', 'val']:
            if phase == 'train':
                scheduler.step()
                model.train()  # Set model to training mode
            else:
                model.eval()   # Set model to evaluate mode
            running_loss = 0.0
            running_corrects = 0

            # Iterate over data.
            for inputs, labels in dataloaders[phase]:
                device1 = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
                inputs = inputs[:,[2,1,0],:,:] #rgb to bgr
                
                inputs = inputs.to(device1)
                labels = labels.to(device1)
                mean = mean.to(device1)
                
                inputs = inputs.detach() + ( torch.randn_like(inputs, device='cuda') * sigma * 255 )
                optimizer.zero_grad()
                # forward
                # track history if only in train
                with torch.set_grad_enabled(phase == 'train'):
                    #save_image('gauss'+ str(args.sigma),(inputs.detach() +mean).clamp(0,255)-mean)
                    outputs = model(inputs)

                    _, preds = torch.max(outputs, 1)

                    loss = criterion(outputs, labels)

                    # backward + optimize only if in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                # statistics
                running_loss += loss.item() * inputs.size(0)
                #print(preds,labels)
                running_corrects += torch.sum(preds == labels.data)
                #print(running_loss,running_corrects)
            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print('{} Loss: {:.4f} Acc: {:.4f}'.format(
                phase, epoch_loss, epoch_acc))

            # deep copy the model
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

        print()

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))
    print('Best val Acc: {:4f}'.format(best_acc))

    # load best model weights
    model.load_state_dict(best_model_wts)
    return model



if __name__ == "__main__":
    torch.manual_seed(123456)

    parser = argparse.ArgumentParser(description='training gaussian model')
    parser.add_argument("model", type=str, help="ori_model")      # this is just for training from a clean model 
    parser.add_argument("-out", type=str, help="output models")   # number name of output models name (a number is good)
    parser.add_argument("-sigma", type=int, help="sigma value")   # sigma of the gaussian noise e.g. 1
    args = parser.parse_args()


    dataloaders,dataset_sizes =data_process(batch_size =32)
    
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model_ft = VGG_16() 
    model_ft.load_weights()
    #model_ft.load_state_dict(torch.load('../donemodel/'+args.model))
    #uncomment to train from a clean model 
    model_ft.to(device)

    # model_ft = nn.DataParallel(model,device_ids=[0,1]) # if you want to use mutliple gpus 

    criterion = nn.CrossEntropyLoss()
    
    #optimizer_ft = optim.SGD(model_ft.parameters(), lr=0.001, momentum=0.9)
    optimizer_ft = optim.Adam(model_ft.parameters(), lr=0.0001)

    # Decay LR by a factor of 0.1 every 7 epochs
    exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=10, gamma=0.1)

    
    model_ft = gauss_train_model(model_ft, args.sigma, criterion, optimizer_ft, exp_lr_scheduler,num_epochs=30)
    # default of number of epochs
    test(model_ft,dataloaders,dataset_sizes)

    torch.save(model_ft.state_dict(), '../donemodel/new_rs_model0'+ str(args.out) +'.pt')







