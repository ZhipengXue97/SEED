import os
import random
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import torch.optim as optim
import argparse
from tqdm import tqdm, trange
import pycparser
import models
import utils


parser = argparse.ArgumentParser()
parser.add_argument("--cuda", default=True)
parser.add_argument("--dataset", default='gcj')
parser.add_argument("--data_setting", default='cf')
parser.add_argument("--graphmode", default='astandnext')
parser.add_argument("--batch_size", default=32)
parser.add_argument("--num_layers", default=4)
parser.add_argument("--num_epochs", default=40)
parser.add_argument("--lr", default=0.001)
parser.add_argument("--threshold", default=0.9)
parser.add_argument("--jsonpath", default="E:\\POJ-104\\json")
args = parser.parse_args(args=[])


device = torch.device('cuda:0')
vocablist = utils.buildvocabdataset(args.jsonpath)
jsonlist = utils.merginjson(args.jsonpath, vocablist)
# seen_testdata = utils.loaddataset(jsonlist,"seen_valdataset.txt")
unseen_testdata = utils.loaddataset(jsonlist,"91_104_dataset.txt")
num_layers = int(args.num_layers)
model = models.GMNnet(len(vocablist), embedding_dim=100, num_layers=num_layers, device=device).to(device)
# model.load_state_dict(torch.load("./model/epo11.h5", map_location=device))

def test(dataset):
    pairlist = []
    for data, label in dataset:
        label = torch.tensor(label, dtype=torch.float, device=device)
        x1, x2, edge_index1, edge_index2, edge_attr1, edge_attr2 = data
        x1 = torch.tensor(x1, dtype=torch.long, device=device)
        x2 = torch.tensor(x2, dtype=torch.long, device=device)
        edge_index1 = torch.tensor(edge_index1, dtype=torch.long, device=device)
        edge_index2 = torch.tensor(edge_index2, dtype=torch.long, device=device)
        if edge_attr1 != None:
            edge_attr1 = torch.tensor(edge_attr1, dtype=torch.long, device=device)
            edge_attr2 = torch.tensor(edge_attr2, dtype=torch.long, device=device)
        data = [x1, x2, edge_index1, edge_index2, edge_attr1, edge_attr2]
        prediction = model(data)
        output = F.cosine_similarity(prediction[0], prediction[1])
        prediction = output.item()
        pairlist.append((prediction,label.item()))
    f1dict = caculatef1(pairlist)
    p = f1dict['p']
    r = f1dict['r']
    f1 = f1dict['f1']
    threshold = f1dict['threshold']
    print(f1dict['tp'],f1dict['tn'],f1dict['fp'],f1dict['fn'])
    print('precision')
    print(p)
    print('recall')
    print(r)
    print('F1')
    print(f1)
    print("threshold")
    print(threshold)
    with open("./test_result.txt","a+") as f:
        f.write('precision:'+str(p)+"\n")
        f.write("recall:"+str(r)+"\n")
        f.write("F1:"+str(f1)+"\n")
        f.write("threshold:" + str(threshold) + "\n")

def caculatef1(data):
    maxf1 = 0.0
    f1dict = {}
    for i in range(0,20):
        threshold = 0+i*0.05
        tp = 0
        tn = 0
        fp = 0
        fn = 0
        for pair in data:
            prediction = pair[0]
            label = pair[1]
            if prediction > threshold and label == 1:
                tp += 1
            if prediction <= threshold and label == -1:
                tn += 1
            if prediction > threshold and label == -1:
                fp += 1
            if prediction <= threshold and label== 1:
                fn += 1
        if tp + fp == 0:
            continue
        p = tp / (tp + fp)
        if tp + fn == 0:
            continue
        r = tp / (tp + fn)
        f1 = 2 * p * r / (p + r)
        if f1 > maxf1:
            maxf1 = f1
            f1dict['p'] = p
            f1dict['r'] = r
            f1dict['f1'] = f1
            f1dict['tp'] = tp
            f1dict['tn'] = tn
            f1dict['fp'] = fp
            f1dict['fn'] = fn
            f1dict['threshold'] = threshold
    return f1dict


for i in range(1,23):
    print(i)
    model.load_state_dict(torch.load("./model/epo"+str(i)+".h5", map_location=device))
    # with open("./test_result.txt", "a+") as f:
    #     f.write(str(i)+"\n")
    #     f.write("seen_val\n")
    # test(seen_testdata)
    with open("./test_result.txt", "a+") as f:
        f.write("unseen_val\n")
    test(unseen_testdata)