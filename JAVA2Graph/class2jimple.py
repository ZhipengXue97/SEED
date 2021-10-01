import os
import re
import shutil
codeforcepath = "K:\codeforces"
codefilepath = codeforcepath + "\\code"
classfilepath = codeforcepath + "\\class"
jimplefilepath = codeforcepath + "\\jimple"
localpath = "C:\\Users\\xzp\\PycharmProjects\\clonedetection_data_preprocess"
for i in os.listdir(codefilepath):
    if not os.path.exists(jimplefilepath + "\\" + i):
        os.mkdir(jimplefilepath + "\\" + i)
    for j in os.listdir(codefilepath + "\\" + i ):
        if os.path.exists(classfilepath + "\\" + i + "\\" + j.replace(".java",".jimple")):
            continue
        try:
            cmd = "javac "+codefilepath + "\\" + i +"\\"+j
            print(cmd)
            os.system(cmd+ " 2>out.txt")
            with open("out.txt") as f:
                out = f.read()
            patternName = '为 (.*?).java 的'
            name = re.findall(patternName, out, re.S | re.M)
            if name == []:
                os.remove(codefilepath + "\\" + i +"\\"+j)
                continue
            name = name[0].replace(" ","")
            print(name)
            os.rename(codefilepath + "\\" + i +"\\"+j,codefilepath + "\\" + i +"\\"+name+".java")
            os.system("javac "+codefilepath + "\\" + i +"\\"+name+".java")
            os.rename(codefilepath + "\\" + i +"\\"+name+".java",codefilepath + "\\" + i +"\\"+j)
            shutil.move(codefilepath + "\\" + i + "\\" + name + ".class",localpath +"\\"+ name + ".class")
            os.system("java -cp sootclasses-trunk-jar-with-dependencies.jar soot.Main -pp -f J -cp . " + name)
            shutil.move(localpath +"\\sootOutput\\"+ name + ".jimple",jimplefilepath + "\\" + i +"\\"+j.replace(".java",".jimple"))
            os.remove(localpath + "\\" + name+".class")
            for k in os.listdir(codefilepath + "\\" + i):
                if ".class" in k:
                    os.remove(codefilepath + "\\" + i +"\\"+k)
        except Exception as e:
            print(e)