import os
import random
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import torch.optim as optim
import argparse
from tqdm import tqdm, trange
import models
import utils

parser = argparse.ArgumentParser()
parser.add_argument("--cuda", default=True)
parser.add_argument("--dataset", default='gcj')
parser.add_argument("--data_setting", default='cf')
parser.add_argument("--graphmode", default='astandnext')
parser.add_argument("--batch_size", default=32)
parser.add_argument("--num_layers", default=4)
parser.add_argument("--num_epochs", default=50)
parser.add_argument("--lr", default=0.001)
parser.add_argument("--threshold", default=0.9)
parser.add_argument("--jsonpath", default="json")
parser.add_argument("--filter", default="none")
args = parser.parse_args(args=[])

device = torch.device('cuda:0')
vocablist = utils.buildvocabdataset(args.jsonpath)
jsonlist = utils.merginjson(args.jsonpath, vocablist)
# traindata, valdata, testdata = utils.buildtraindataset(jsonlist, args.jsonpath, 1, 400, args.filter)
# unseen_valdata = utils.buildunseendataset(jsonlist, args.jsonpath, 500, 540, args.filter)
# unseen_testdata = utils.buildunseendataset(jsonlist, args.jsonpath, 541, 581, args.filter)

#1-30

if os.path.exists("76_90_dataset.txt"):
    unseen_valdata = utils.loaddataset(jsonlist,"76_90_dataset.txt")
if os.path.exists("seen_traindataset.txt"):
    traindata = utils.loaddataset(jsonlist,"seen_traindataset.txt")
if os.path.exists("seen_valdataset.txt"):
    valdata = utils.loaddataset(jsonlist,"seen_valdataset.txt")
num_layers = int(args.num_layers)
model = models.GMNnet(len(vocablist), embedding_dim=100, num_layers=num_layers, device=device).to(device)
optimizer = optim.Adam(model.parameters(), lr=args.lr)
scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.9)
# criterion = FocalLoss(alpha=2, gamma=5)
# criterion = nn.CosineEmbeddingLoss()
criterion = nn.MSELoss()
# criterion = models.FocalLoss(alpha=0.9, gamma=2)

def create_batches(data):
    random.shuffle(data)
    batches = [data[graph:graph + args.batch_size] for graph in range(0, len(data), args.batch_size)]
    return batches
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
    with open("./val_result.txt","a+") as f:
        f.write('precision:'+str(p)+"\n")
        f.write("recall:"+str(r)+"\n")
        f.write("F1:"+str(f1)+"\n")
        f.write("threshold:" + str(threshold) + "\n")

epochs = trange(args.num_epochs, leave=True, desc="Epoch")
for epoch in epochs:  # without batching
    print(epoch)
    batches = create_batches(traindata)
    totalloss = 0.0
    main_index = 0.0
    for index, batch in tqdm(enumerate(batches), total=len(batches), desc="Batches"):
        optimizer.zero_grad()
        batchloss = 0
        for data, label in batch:
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
                cossim = F.cosine_similarity(prediction[0], prediction[1])
                batchloss = batchloss + criterion(cossim, label)
            except:
                continue
        batchloss.backward(retain_graph=True)
        optimizer.step()
        loss = batchloss.item()
        totalloss += loss
        main_index = main_index + len(batch)
        loss = totalloss / main_index
        epochs.set_description("Epoch (Loss=%g)" % round(loss, 5))
    with open("./val_result.txt", "a+") as f:
        f.write(str(epoch+1)+"\n")
        f.write("seen_val\n")
    test(valdata)
    with open("./val_result.txt", "a+") as f:
        f.write("unseen_val\n")
    test(unseen_valdata)
    scheduler.step()
    torch.save(model.state_dict(),'./model/'+"epo"+str(epoch+1)+".h5")
