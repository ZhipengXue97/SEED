import os

poj_path = "./POJ_104"
codepath = poj_path+"/code"
txtpath = poj_path+"/txt"
irpath = poj_path+"/ir"


for dir in os.listdir(codepath):
    if not os.path.exists(irpath+"/"+dir):
        os.mkdir(irpath + "/" + dir)
    for file in os.listdir(codepath + "/" + dir):
        codefilepath = codepath + "/" + dir + "/" + file
        irfilepath = irpath+ "/" + dir + "/" + file.replace('.c','.ll')
        print(irfilepath)
        if os.path.exists(irfilepath):
            continue
        os.system("clang++ -c -emit-llvm " + codefilepath+" -S -o "+irfilepath)