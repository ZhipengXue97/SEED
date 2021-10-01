import os
import random
import json


def merginjson(jsonfilepath, vocab):
    jsondict = {}
    for dir in os.listdir(jsonfilepath):
        dirpath = jsonfilepath + "\\" + str(dir)
        for json_file in os.listdir(dirpath):
            x = []
            edgstr = []
            edgtar = []
            edgattr = []
            tmpdict = {}
            file = dirpath + "\\" + json_file
            print(file)
            json_line = json.loads(open(file, 'r').readline())
            # if len(json_line)>500:
            #     os.remove(file)
            #     continue
            for i in json_line:
                node = json_line[i]['node']
                snode = json_line[i]['snode']
                word_index = vocab[node]
                tmp = []
                tmp.append(word_index)
                x.append(tmp)
                for j in snode:
                    edgstr.append(int(i))
                    edgtar.append(j)
                    if node == "label" or json_line[str(j)]['node'] == "label":
                        tmp = []
                        tmp.append(1)
                        edgattr.append(tmp)
                    else:
                        tmp = []
                        tmp.append(0)
                        edgattr.append(tmp)
            tmpdict['x'] = x
            tmpdict['edge'] = [edgstr, edgtar]
            tmpdict['edgeattr'] = edgattr
            jsondict[file] = tmpdict
    return jsondict


def buildvocabdataset(jsonfilepath):
    dict = {}
    id = 0
    for dir in os.listdir(jsonfilepath):
        for dirfile in os.listdir(jsonfilepath + "\\" + dir):
            file = jsonfilepath + "\\" + dir + "\\" + dirfile
            print(file)
            vocab = json.loads(open(file, 'r').readline())
            for i in vocab:
                word = vocab[i]["node"]
                if word in dict:
                    continue
                else:
                    dict[word] = id
                    id = id + 1
    return dict

def buildtraindataset(jsonlist, jsonpath, start, end, mode):
    if mode == "sourcererCC":
        pairlist = getclone("sourceerCC_result.txt")
    if mode == "complexity":
        comlist = getcomplexity("complexity.txt")
    dirindex = range(start, end+1)
    jsonfilelist = []
    for i in dirindex:
        dirpath = jsonpath + "\\" + str(i)
        for jsonfile in os.listdir(dirpath):
            jsonfile = dirpath + "\\" + jsonfile
            jsonfilelist.append(jsonfile)
    random.shuffle(jsonfilelist)
    flag1 = int(len(jsonfilelist)*0.8)
    flag2 = int(len(jsonfilelist)*0.9)
    traindata = []
    valdata = []
    testdata = []
    T = 0
    F = 0
    with open("seen_traindataset.txt",'a+')as f:
        print("start build traindata")
        while(1):
            print(T+F)
            i = random.randint(0, flag1-1)
            j = random.randint(0, flag1-1)
            item = []
            data = []
            if i == j:
                continue
            else:
                if T + F >= 100000:
                    break
                else:
                    path1 = jsonfilelist[i]
                    path2 = jsonfilelist[j]
                    if path1.split("\\")[-2] == path2.split("\\")[-2]:
                        if T >= 50000:
                            continue
                        else:
                            T = T + 1
                            label = 1
                    else:
                        if F >= 50000:
                            continue
                        else:
                            F = F + 1
                            label = -1
                    input1 = jsonlist[path1]
                    input2 = jsonlist[path2]
                    data.append(input1['x'])
                    data.append(input2['x'])
                    data.append(input1['edge'])
                    data.append(input2['edge'])
                    data.append(input1['edgeattr'])
                    data.append(input2['edgeattr'])
                    item.append(data)
                    item.append(label)
                    traindata.append(item)
                    line = jsonfilelist[i] + "\t" +jsonfilelist[j] + "\t" +str(label) + "\n"
                    f.write(line)
    T = 0
    F = 0
    with open("seen_valdataset.txt", 'a+')as f:
        print("start build valdata")
        while(1):
            print(T+F)
            i = random.randint(flag1,flag2-1)
            j = random.randint(flag1,flag2-1)
            item = []
            data = []
            if i == j:
                continue
            else:
                if T + F >= 10000:
                    break
                else:
                    path1 = jsonfilelist[i]
                    path2 = jsonfilelist[j]
                    if path1.split("\\")[-2] == path2.split("\\")[-2]:
                        if T >= 1000:
                            continue
                        else:
                            tmppath1 = path1.replace(".json",".txt")
                            tmppath1 = tmppath1.replace("json", "data")
                            tmppath2 = path2.replace(".json",".txt")
                            tmppath2 = tmppath2.replace("json", "data")
                            if mode == "line":
                                if abs(checklines(tmppath1) - checklines(tmppath2)) < 1:
                                    continue
                                else:
                                    T = T + 1
                                    label = 1
                            elif mode == "complexity":
                                com1 = int(comlist[tmppath1])
                                com2 = int(comlist[tmppath2])
                                if abs(com1-com2) <= 3:
                                    continue
                                else:
                                    T = T + 1
                                    label = 1
                            elif mode == "sourcererCC":
                                if (path1,path2) in pairlist or (path2, path1) in pairlist:
                                    continue
                                else:
                                    T = T + 1
                                    label = 1
                            elif mode == "none":
                                T = T + 1
                                label = 1
                    else:
                        if F >= 9000:
                            continue
                        else:
                            F = F + 1
                            label = -1
                    input1 = jsonlist[path1]
                    input2 = jsonlist[path2]
                    data.append(input1['x'])
                    data.append(input2['x'])
                    data.append(input1['edge'])
                    data.append(input2['edge'])
                    data.append(input1['edgeattr'])
                    data.append(input2['edgeattr'])
                    item.append(data)
                    item.append(label)
                    valdata.append(item)
                    line = jsonfilelist[i] + "\t" + jsonfilelist[j] + "\t" + str(label) + "\n"
                    f.write(line)

    T = 0
    F = 0
    with open("seen_testdataset.txt", 'a+')as f:
        print("start build testdata")
        while(1):
            print(T+F)
            i = random.randint(flag2,len(jsonfilelist)-1)
            j = random.randint(flag2,len(jsonfilelist)-1)
            item = []
            data = []
            if i == j:
                continue
            else:
                if T + F >= 10000:
                    break
                else:
                    path1 = jsonfilelist[i]
                    path2 = jsonfilelist[j]
                    if path1.split("\\")[-2] == path2.split("\\")[-2]:
                        if T >= 1000:
                            continue
                        else:
                            tmppath1 = path1.replace(".json",".txt")
                            tmppath1 = tmppath1.replace("json", "data")
                            tmppath2 = path2.replace(".json",".txt")
                            tmppath2 = tmppath2.replace("json", "data")
                            if mode == "line":
                                if abs(checklines(tmppath1) - checklines(tmppath2)) < 1:
                                    continue
                                else:
                                    T = T + 1
                                    label = 1
                            elif mode == "complexity":
                                com1 = int(comlist[tmppath1])
                                com2 = int(comlist[tmppath2])
                                if abs(com1-com2) <= 3:
                                    continue
                                else:
                                    T = T + 1
                                    label = 1
                            elif mode == "sourcererCC":
                                if (path1,path2) in pairlist or (path2, path1) in pairlist:
                                    continue
                                else:
                                    T = T + 1
                                    label = 1
                            elif mode == "none":
                                T = T + 1
                                label = 1
                    else:
                        if F >= 9000:
                            continue
                        else:
                            F = F + 1
                            label = -1
                    input1 = jsonlist[path1]
                    input2 = jsonlist[path2]
                    data.append(input1['x'])
                    data.append(input2['x'])
                    data.append(input1['edge'])
                    data.append(input2['edge'])
                    data.append(input1['edgeattr'])
                    data.append(input2['edgeattr'])
                    item.append(data)
                    item.append(label)
                    testdata.append(item)
                    line = jsonfilelist[i] + "\t" + jsonfilelist[j] + "\t" + str(label) + "\n"
                    f.write(line)
    random.shuffle(traindata)
    random.shuffle(valdata)
    random.shuffle(testdata)
    return traindata, valdata, testdata

def buildunseendataset(jsonlist, jsonpath, start, end, mode):
    if mode == "sourcererCC":
        pairlist = getclone("sourceerCC_result.txt")
    if mode == "complexity":
        comlist = getcomplexity("complexity.txt")
    dirindex = range(start, end+1)
    jsonfilelist = []
    for i in dirindex:
        dirpath = jsonpath + "\\" + str(i)
        dirlist = os.listdir(dirpath)
        random.shuffle(dirlist)
        for jsonfile in dirlist:
            jsonfile = dirpath + "\\" + jsonfile
            jsonfilelist.append(jsonfile)
    random.shuffle(jsonfilelist)
    flag = len(jsonfilelist)
    testdata = []
    T = 0
    F = 0
    print("start build dataset")
    with open(str(start) + "_" + str(end)+"_dataset.txt", "a+")as f:
        while(1):
            print(T+F)
            i = random.randint(0,flag-1)
            j = random.randint(0, flag-1)
            item = []
            data = []
            if i == j:
                continue
            else:
                if T + F >= 10000:
                    break
                else:
                    path1 = jsonfilelist[i]
                    path2 = jsonfilelist[j]
                    if path1.split("\\")[-2] == path2.split("\\")[-2]:
                        if T >= 1000:
                            continue
                        else:
                            tmppath1 = path1.replace(".json",".txt")
                            tmppath1 = tmppath1.replace("json", "data")
                            tmppath2 = path2.replace(".json",".txt")
                            tmppath2 = tmppath2.replace("json", "data")
                            if mode == "line":
                                if abs(checklines(tmppath1) - checklines(tmppath2)) < 1:
                                    continue
                                else:
                                    T = T + 1
                                    label = 1
                            elif mode == "complexity":
                                com1 = int(comlist[tmppath1])
                                com2 = int(comlist[tmppath2])
                                if abs(com1-com2) <= 3:
                                    continue
                                else:
                                    T = T + 1
                                    label = 1
                            elif mode == "sourcererCC":
                                if (path1,path2) in pairlist or (path2, path1) in pairlist:
                                    continue
                                else:
                                    T = T + 1
                                    label = 1
                            elif mode == "none":
                                T = T + 1
                                label = 1
                    else:
                        if F >= 9000:
                            continue
                        else:
                            F = F + 1
                            label = -1
                    input1 = jsonlist[path1]
                    input2 = jsonlist[path2]
                    data.append(input1['x'])
                    data.append(input2['x'])
                    data.append(input1['edge'])
                    data.append(input2['edge'])
                    data.append(input1['edgeattr'])
                    data.append(input2['edgeattr'])
                    item.append(data)
                    item.append(label)
                    testdata.append(item)
                    line = jsonfilelist[i] + "\t" + jsonfilelist[j] + "\t" + str(label) + "\n"
                    f.write(line)
    random.shuffle(testdata)
    return testdata

def loaddataset(jsonlist,datasetpath):
    dataset = []
    with open(datasetpath,"r")as f:
        lines = f.readlines()
    for line in lines:
        try:
            item = []
            data = []
            line = line.split("\t")
            input1 = jsonlist[line[0]]
            input2 = jsonlist[line[1]]
            data.append(input1['x'])
            data.append(input2['x'])
            data.append(input1['edge'])
            data.append(input2['edge'])
            data.append(input1['edgeattr'])
            data.append(input2['edgeattr'])
            item.append(data)
            item.append(int(line[-1]))
            dataset.append(item)
        except:
            continue
    random.shuffle(dataset)
    return dataset

def checklines(path):
    with open(path,"r")as f:
        lines = f.readlines()
        for i in range(len(lines)):
            lines[i] = lines[i].replace("\t","")
            lines[i] = lines[i].replace("\n", "")
        while "" in lines:
            lines.remove("")
        while "}" in lines:
            lines.remove("}")
        while "{" in lines:
            lines.remove("{")
        return len(lines)

def getclone(path):
    pairlist = []
    with open(path,"r") as f:
        lines = f.readlines()
    for line in lines:
        file1 = line.split("\t")[0]
        fil2 = line.split("\t")[-1].replace("\n","")
        pair = (file1, fil2)
        pairlist.append(pair)
    return pairlist

def getcomplexity(path):
    comlist = {}
    with open(path,'r')as f:
        lines = f.readlines()
    for line in lines:
        file = line.split("\t")[0]
        complx = line.split("\t")[-1].replace("\n","")
        comlist[file] = complx
    return comlist

