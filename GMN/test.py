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
seen_testdata = utils.loaddataset(jsonlist,"seen_testdataset.txt")
unseen_testdata = utils.loaddataset(jsonlist,"91_104_dataset.txt")
num_layers = int(args.num_layers)
model = models.GMNnet(len(vocablist), embedding_dim=100, num_layers=num_layers, device=device).to(device)

def test(dataset,threshold):
    tp = 0
    tn = 0
    fp = 0
    fn = 0
    for data, label in dataset:
        try:
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
            if prediction > threshold and label.item() == 1:
                tp += 1
                # print('tp')
            if prediction <= threshold and label.item() == -1:
                tn += 1
                # print('tn')
            if prediction > threshold and label.item() == -1:
                fp += 1
                # print('fp')
            if prediction <= threshold and label.item() == 1:
                fn += 1
                # print('fn')
        except:
            continue
    print("\n")
    print(tp, tn, fp, fn)
    p = 0.0
    r = 0.0
    f1 = 0.0
    if tp + fp == 0:
        print('precision is none')
        return
    p = tp / (tp + fp)
    if tp + fn == 0:
        print('recall is none')
        return
    r = tp / (tp + fn)
    f1 = 2 * p * r / (p + r)
    print('precision')
    print(p)
    print('recall')
    print(r)
    print('F1')
    print(f1)
    with open("./test_result.txt","a+") as f:
        f.write('precision:'+str(p)+"\n")
        f.write("recall:"+str(r)+"\n")
        f.write("F1:"+str(f1)+"\n")



i = 16
model.load_state_dict(torch.load("./model/epo"+str(i)+".h5", map_location=device))
# with open("./test_result.txt", "a+") as f:
#     f.write(str(i)+"\n")
#     f.write("seen_test\n")
# test(seen_testdata,0.4)
with open("./test_result.txt", "a+") as f:
    f.write(str(i)+"\n")
    f.write("unseen_test\n")
test(unseen_testdata,0.8)