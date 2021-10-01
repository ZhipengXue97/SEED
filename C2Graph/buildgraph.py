import re
import networkx as nx
import os
import json


#判断是否是常量
def isDecimalOrIntOrstr(str):
    #去除字符串两边的空格
    s= str.strip()
    flag = True
    tmp = s.replace("+","")
    tmp = tmp.replace("-","")
    tmp = tmp.replace(".","")
    if not tmp.isalnum():
        return False
    #判断是否是null
    if s == "null":
        return flag
    #判断是否是字符串
    if str[0] == '"' and str[-1] == '"':
        return flag
    pattern = r'0x[0-9A-F]*'
    a = re.findall(pattern, str)
    if len(a) == 1:
        if a == str:
            return flag
    decRet= re.match("-?\d+\.?\d*e?-?\d*?",s)
    if decRet:
        return flag
    if s == "true" or s=="false":
        return flag
    flag = False
    return flag

#提取常量类型
def get_numtype(str):
    if str == "null" :
        return "null"
    elif str == "true" or str == "false":
        return "i1"
    elif '.' in str:
        str = str.replace('F','')
        return "float"
    else:
        pattern = '-?\d+'
        return "i32"


#根据变量名取node值
def get_node_num(cfg, value):
    for i in cfg.nodes:
        if 'value' in cfg.nodes[i]:
            if cfg.nodes[i]['value'] == value:
                return i
    return -1

def get_funname(file):
    with open(file) as f:
        content = f.readlines()
        for i in content:
            pattern = r' (.*?)[(]'
            res = re.findall(pattern,i)
        return res

#提取函数名、函数体
def get_fun(file):
    with open(file) as f:
        content = f.readlines()

    fun_name = []
    fun_body = []
    globalv={}
    start_index = 0

    for i in range(len(content)):

        # 全局变量
        if "global " in content[i] or "constant" in content[i]:
            if "__dso_handle" not in content[i] and "ioinit" not in content[i] and "cin" not in content[i] and "cout" not in content[i] and "global_ctors" not in content[i]:
                name = content[i].split('=')[0].strip()
                type = check_type(content[i])
                if "@.str" in name:
                    pattern = r'"(.*?)"'
                    type = re.findall(pattern, content[i])[0]
                    type = "globle"+type
                globalv[name] = type

        #函数名
        if "define" in content[i] and '"' not in content[i] and "linkonce_odr" not in content[i]:
            pattern = r'@(.*?)[(]'
            name = re.findall(pattern,content[i])[0]
            fun_name.append(name)
            start_index = i

        #函数体
        if "}\n" == content[i]:
            if start_index != 0:
                body = content[start_index: i]
                fun_body.append(body)
                start_index = 0

    if len(fun_name) == len(fun_body):
        function_dict  = dict(zip(fun_name,fun_body))
    return function_dict, globalv

#获取数据类型
def check_type(line):
    res = '-1'
    if "struct" in line or ":" in line:
        res = "struct"
    elif "i1" in line:
        res = "i1"
    elif "i8" in line:
        res = "i8"
    elif "i16" in line:
        res = "i16"
    elif "32" in line:
        res = "i32"
    elif "64" in line:
        res = "i64"
    elif "float" in line:
        res = "float"
    elif "double" in line:
        res = "double"
    elif "86_fp80" in line:
        res = "86_fp80"
    elif "null" in line:
        res = line
    if "[" in line or "*" in line:
        res = res + "[]"
    type = res

    return type

#截取数组字符
def split_elem(line):
    index = line.find("getelementptr")
    line = line[index:]
    index = line.find(")")
    return line[:index]

#数组取值操作
def getelem(cfg, funname, line):
    global node_num
    tmp = line.split(",")
    op1_type = tmp[0]
    op1_type = check_type(op1_type).replace("[]","")
    get_1 = tmp[1]
    get_1 = get_1.split(" ")
    get_op1 = get_1[-1]
    if get_op1 in globalv:
        get_op1_num = get_node_num(cfg, get_op1)
    else:
        get_op1_num = get_node_num(cfg, funname+"_"+get_op1)
    if "getelementptr" in get_1:
        index = line.find(",")
        tmpline = line[index:]
        tmpline = split_elem(tmpline)
        get_op1_num, type = getelem(cfg, funname, tmpline)
    get_2 = tmp[-1].strip()
    get_2 = get_2.split(" ")
    get_op2 = get_2[-1]
    if isDecimalOrIntOrstr(get_op2):
        get_op2_type = check_type(get_2[0])
        get_op2_num = node_num
        node_num = node_num + 1
        cfg.add_node(get_op2_num, value = get_op2, type = get_op2_type)
    else:
        get_op2_num = get_node_num(cfg, funname+"_"+get_op2)
    getele_num = node_num
    node_num = node_num + 1
    cfg.add_node(getele_num, value = "getelem", type = "operation")
    cfg.add_edge(get_op1_num, getele_num, type = "dataflow")
    cfg.add_edge(get_op2_num, getele_num, type = "dataflow")
    return getele_num, op1_type

#返回值
def get_return(g):
    res = []
    for i in g:
        if g._node[i]['value'] =='return' and g._node[i]['type'] == 'operation':
            res.append(i)
    return res

def get_var(fun_body):
    res = []
    lines = []

    for i in fun_body:
        i = i.replace('\n', '')
        lines.append(i)

    for line in lines:
        if " = " in line and "<label>" not in line:
            op = line.split("=")[0].strip()
            res.append(op)

    return res




def build_graph(defalt_graph, fun_name, fun_body):
    global node_num
    lines=[]
    tmp_g = nx.DiGraph()
    cfg = nx.compose(defalt_graph,tmp_g)

    for i in fun_body:
        i = i.replace('\n','')
        lines.append(i)

    #添加所有变量
    var_list = get_var(fun_body)
    for var in var_list:
        var_name = fun_name +"_"+ var
        var_node = node_num
        node_num = node_num + 1
        cfg.add_node(var_node, value = var_name, type = "null")

    #添加返回值
    for line in lines:
        if "ret" in line:
            if "void" in line:
                continue
            if "getelementptr" in line:
                res_op = split_elem(line)
                res_num, type = getelem(cfg, fun_name, res_op)
            else:
                res_op = line.split(" ")[-1]
                res_type = line.split(" ")[-2]
                if isDecimalOrIntOrstr(res_op):
                    res_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(res_num, value=res_op, type=res_type)
                else:
                    res_name = fun_name+ "_" +res_op
                    res_num = get_node_num(cfg, res_name)
            res_op_num = node_num
            node_num = node_num + 1
            cfg.add_node(res_op_num, value="return", type="operation")
            cfg.add_edge(res_num, res_op_num, type="dataflow")



    #添加所有label
    for line in lines:
        if "; <label>:" in line:
            pattern = r'\d+'
            label_index = re.findall(pattern, line)[0]
            label_name = "label" + label_index
            label_num = node_num
            node_num = node_num + 1
            cfg.add_node(label_num, value=fun_name + "_" + label_name, type="label")
    label_name = fun_name + "_" + "start"
    label_num = node_num
    node_num = node_num + 1
    cfg.add_node(label_num, value=label_name, type="label")

    #添加边
    for line in lines:
        line = line.strip()
        print(line)
        tmp = ""
        if "cmp" in line or "and" in line or "sub" in line or "mul" in line or "div" in line or "add" in line or "rem" in line or "or" in line or "sh" in line:
            tmp = line.split(" ")[2]


        # 标签块，调整labelnum
        if "; <label>:" in line:
            pattern = r'\d+'
            label_index = re.findall(pattern, line)[0]
            label_name = "label" + label_index
            label_num = get_node_num(cfg, fun_name+"_"+label_name)

        #数据流跳转
        elif "label" in line and "br" in line:
            pattern = r'label %(\d+)'
            tar = re.findall(pattern,line)
            for label_index in tar:
                label_name = "label" + label_index
                tar_label_num = get_node_num(cfg, fun_name + "_" + label_name)
                cfg.add_edge(label_num, tar_label_num,type = "controlflow")

        elif "; No predecessors!" in line:
            label_num = get_node_num(cfg, fun_name+"_"+"start")

        elif "define " in line:
            index = line.find("@")
            line = line[index:]
            index = line.find("#")
            line = line[:index]
            index = line.find("(")
            line = line[index+1:]
            index = line.rfind(")")
            line = line[:index]
            tmp = line.split(",")
            define_list = []
            if line == "":
                tmp = []
            for item in tmp:
                item = item.strip()
                name = item.split(" ")[-1]
                type  = item.split(" ")[0]
                op_num = node_num
                node_num = node_num + 1
                op_name = fun_name + "_" + name
                op_type = check_type(type)
                cfg.add_node(op_num, value = op_name, type = op_type)
                define_list.append(op_num)
            g_dist[fun_name+"define"] = define_list

        #变量定义
        elif " alloca" in line:
            name = line.split('=')[0].strip()
            type = check_type(line)
            name = fun_name + "_" + name
            name_num = get_node_num(cfg, name)
            cfg.add_node(name_num, value = name, type = type)

        #函数调用
        elif "invoke " in line or "call " in line:
            if "istream" in line:
                stream = line.split("=")[0].strip()
                stream_name = fun_name + "_" + stream
                stream_num = get_node_num(cfg, stream_name)
                cfg.add_node(stream_num, value=stream_name, type="structure[]")
                cinnode_num = node_num
                node_num = node_num + 1
                cfg.add_node(cinnode_num, value="cin", type="invoke")
                cfg.add_edge(label_num, cinnode_num, type="controlflow")
                cfg.add_edge(cinnode_num,stream_num, type = "dataflow")
                if "Ev" in line:
                    continue
                elif "EPci" in line:
                    index = line.find("i8")
                    line = line[index:]
                    if "getelementptr" in line:
                        get_line = split_elem(line)
                        getelem_num, type = getelem(cfg,fun_name, get_line)
                        cfg.add_edge(getelem_num, cinnode_num, type = "dataflow")
                        cfg.add_edge(label_num, getelem_num, type = "controlflow")
                    else:
                        op = line.split(",")[0].split(" ")[-1]
                        if op in globalv:
                            op_num = get_node_num(cfg, op)
                        else:
                            op_name = fun_name + "_" + op
                            op_num = get_node_num(cfg, op_name)
                        cfg.add_edge(op_num, cinnode_num, type = "dataflow")
                elif "char_traits" in line or "getERc" in line or "Sirs" in line:
                    index = line.find(",")
                    line = line[index+1:]
                    if "getelementptr" in line:
                        get_line = split_elem(line)
                        getelem_num, type = getelem(cfg, fun_name, get_line)
                        cfg.add_edge(getelem_num, cinnode_num, type = "dataflow")
                        cfg.add_edge(label_num, getelem_num, type="controlflow")
                    else:
                        op = line.split(" ")[-1].replace(")","")
                        if op in globalv:
                            op_num = get_node_num(cfg, op)
                        else:
                            op_name = fun_name + "_" + op
                            op_num = get_node_num(cfg, op_name)
                        cfg.add_edge(op_num, cinnode_num, type = "dataflow")
                continue

            elif "ostream" in line:
                stream = line.split("=")[0].strip()
                stream_name = fun_name + "_" + stream
                index = line.find(",")
                line = line[index+1:].strip()
                if "getelementptr" in line:
                    op = split_elem(line)
                    getelem_num, type = getelem(cfg, fun_name, op)
                    cout_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(cout_num, value = "cout", type = "invoke")
                    stream_num = get_node_num(cfg, stream_name)
                    cfg.add_node(stream_num, value = stream_name, type = "structure[]")
                    cfg.add_edge(cout_num, stream_num, type = "dataflow")
                    cfg.add_edge(getelem_num, cout_num, type = "dataflow")
                    cfg.add_edge(label_num, getelem_num, type = "controlflow")
                    cfg.add_edge(label_num, cout_num, type="controlflow")
                else:
                    op = line.split(" ")[-1].replace(")","")
                    if isDecimalOrIntOrstr(op):
                        op_type = line.split(" ")[0]
                        op_num = node_num
                        node_num = node_num + 1
                        cfg.add_node(op_num, value = op, type = op_type)
                    else:
                        op_name = fun_name + "_" +op
                        op_num = get_node_num(cfg, op_name)
                    if op_num!=-1:
                        cout_num = node_num
                        node_num = node_num + 1
                        cfg.add_node(cout_num, value="cout", type="invoke")
                        stream_num = get_node_num(cfg, stream_name)
                        cfg.add_node(stream_num, value=stream_name, type="structure[]")
                        cfg.add_edge(cout_num, stream_num, type="dataflow")
                        cfg.add_edge(op_num, cout_num, type="dataflow")
                        cfg.add_edge(label_num, cout_num, type="controlflow")
                continue

            elif "basic_ios" in line:
                if "=" in line:
                    stream = line.split("=")[0].strip()
                    stream_name = fun_name + "_" + stream
                    stream_num = get_node_num(cfg, stream_name)
                    cfg.add_node(stream_num, value = stream_name, type = "structure[]")
                line = line.split("=")[-1].strip()
                pattern = r'%(\d+)*'
                op1 = "%" + re.findall(pattern, line)[-1]
                op1_name = fun_name + "_" +op1
                op1_num = get_node_num(cfg, op1_name)
                ios_num = node_num
                node_num = node_num + 1
                cfg.add_node(ios_num, value = "basic_ios", type = "invoke")
                cfg.add_edge(op1_num, ios_num, type = "dataflow")
                if "=" in line:
                    cfg.add_edge(ios_num, stream_num, type = "dataflow")
                cfg.add_edge(label_num, ios_num, type = "controlflow")
                continue

            elif "precision" in line:
                if "=" in line:
                    op = line.split("=")[0].strip()
                    op_name = fun_name + "_" +  op
                    op_num = get_node_num(cfg, op_name)
                    cfg.add_node(op_num, value = op_name, type = "structure[]")
                line = line.split("=")[-1].strip()
                pattern = r'[(](.*?)[)]'
                tmp = re.findall(pattern, line)[-1]
                tmp = tmp.split(" ")
                op1 = tmp[-1]
                op1_type = tmp[0]
                if isDecimalOrIntOrstr(op1):
                    op1_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(op1_num, value=op1, type=op1_type)
                else:
                    op1_name = fun_name + "_" + op1
                    op1_num = get_node_num(cfg, op1_name)
                pre_num = node_num
                node_num = node_num + 1
                cfg.add_node(pre_num, value = "setprecision", type = "invoke")
                op2_num = node_num
                node_num = node_num + 1
                op2 = line.split(" ")[-1].replace(")","")
                cfg.add_node(op2_num, value = op2, type = "i32")
                cfg.add_edge(op1_num, pre_num, type  = "dataflow")
                cfg.add_edge(op2_num, pre_num, type="dataflow")
                cfg.add_edge(label_num, pre_num, type="controlflow")
                if "=" in line:
                    cfg.add_edge(pre_num, op_num, type = "dataflow")
                continue

            pattern = r'@(.*?)[(]'
            res = re.findall(pattern,line)
            for i in res:
                # API其他函数
                if i not in function_dict.keys() and ")" not in i and "*" not in i:
                    if "llvm" in i:
                        i = i.split('.')[1]
                    if "bitset" in i:
                        i = "bitset"
                    op_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(op_num, value=i, type="invoke")
                    cfg.add_edge(label_num, op_num, type="controlflow")
                    if "=" in line:
                        op1 = line.split("=")[0].strip()
                        tmp = line.split(" ")
                        op1_type=-1
                        for word in tmp:
                            if check_type(word) != '-1':
                                op1_type = check_type(word)
                                break
                        if op1_type!=-1:
                            op1_name = fun_name + "_" + op1
                            op1_num = get_node_num(cfg, op1_name)
                            cfg.add_node(op1_num, value = op1_name, type = op1_type)
                            cfg.add_edge(op_num, op1_num, type = "dataflow")
                    index = line.find(i)
                    tmpline = line[index:]
                    index = tmpline.find("(")
                    tmpline = tmpline[index + 1:]
                    index = tmpline.rfind(")")
                    tmpline = tmpline[:index]
                    tmp = tmpline.split(",")
                    if tmpline == "":
                        tmp=[]
                    it = iter(range(len(tmp)))
                    for index in it:
                        part = tmp[index]
                        if "getelementptr" in part:
                            part = tmp[index] + "," + tmp[index + 1] + "," + tmp[index + 2] + "," + tmp[index + 3]+")"
                            part = split_elem(part)
                            getelem_num, type = getelem(cfg, fun_name, part)
                            cfg.add_edge(getelem_num, op_num, type = "dataflow")
                            cfg.add_edge(label_num, getelem_num, type = "controlflow")
                            next(it)
                            next(it)
                            next(it)
                            continue
                        elif "bitcast" in part:
                            pattern = r'@(.*?) '
                            op_tmp = re.findall(pattern,part)[0]
                            op_tmp_name = "@" + op_tmp
                            op_tmp_num = get_node_num(cfg, op_tmp_name)
                            cfg.add_edge(op_tmp_num, op_num, type = "dataflow")
                            continue
                        part = part.strip()
                        op_tmp_type = part.split(" ")[0]
                        op_tmp = part.split(" ")[-1]
                        if op_tmp in globalv:
                            op_tmp_num = get_node_num(cfg, op_tmp)
                        elif isDecimalOrIntOrstr(op_tmp):
                            op_tmp_num = node_num
                            node_num = node_num + 1
                            cfg.add_node(op_tmp_num, value = op_tmp, type = op_tmp_type)
                        else:
                            op_tmp_name = fun_name + "_" + op_tmp
                            op_tmp_num = get_node_num(cfg, op_tmp_name)
                        if op_tmp_num != -1:
                            cfg.add_edge(op_tmp_num, op_num, type = "dataflow")

            #定义函数
                if i in function_dict.keys() and i != fun_name:
                    if "=" in line:
                        op1 = line.split("=")[0].strip()
                        tmp = line.split(" ")
                        op1_type=-1
                        for word in tmp:
                            if check_type(word) != '-1':
                                op1_type = check_type(word)
                                break
                        if op1_type!=-1:
                            op1_name = fun_name + "_" + op1
                            op1_num_res = get_node_num(cfg, op1_name)
                            cfg.add_node(op1_num_res, value = op1_name, type = op1_type)
                    if i not in g_dist:
                        g = build_graph(defalt_graph, i, function_dict[i])
                        g_dist[i] = g
                    else:
                        g = g_dist[i]
                    cfg = nx.compose(cfg, g)
                    start_num = get_node_num(cfg, i+"_"+"start")
                    cfg.add_edge(label_num, start_num, type = "controlflow")
                    para_list = []
                    index = line.find(i)
                    tmpline = line[index:]
                    index = tmpline.find("(")
                    tmpline = tmpline[index + 1:]
                    index = tmpline.rfind(")")
                    tmpline = tmpline[:index]
                    tmp = tmpline.split(",")
                    if tmpline == "":
                        tmp=[]
                    it = iter(range(len(tmp)))
                    for index in it:
                        part = tmp[index]
                        if "getelementptr" in part:
                            part = tmp[index] + "," + tmp[index + 1] + "," + tmp[index + 2] + "," + tmp[index + 3]+")"
                            part = split_elem(part)
                            getelem_num, type = getelem(cfg, fun_name, part)
                            para_list.append(getelem_num)
                            cfg.add_edge(label_num, getelem_num, type = "controlflow")
                            next(it)
                            next(it)
                            next(it)
                            continue
                        elif "bitcast" in part:
                            pattern = r'@(.*?) '
                            op_tmp = re.findall(pattern,part)[0]
                            op_tmp_name = "@" + op_tmp
                            op_tmp_num = get_node_num(cfg, op_tmp_name)
                            para_list.append(op_tmp_num)
                            continue
                        part = part.strip()
                        op_tmp_type = part.split(" ")[0]
                        op_tmp = part.split(" ")[-1]
                        if op_tmp in globalv:
                            op_tmp_num = get_node_num(cfg, op_tmp)
                            para_list.append(op_tmp_num)
                        elif isDecimalOrIntOrstr(op_tmp):
                            op_tmp_num = node_num
                            node_num = node_num + 1
                            cfg.add_node(op_tmp_num, value = op_tmp, type = op_tmp_type)
                            para_list.append(op_tmp_num)
                        else:
                            op_tmp_name = fun_name + "_" + op_tmp
                            op_tmp_num = get_node_num(cfg, op_tmp_name)
                            para_list.append(op_tmp_num)
                    define_list = g_dist[i+"define"]
                    for num in range(len(para_list)):
                        equal_num = node_num
                        node_num = node_num + 1
                        cfg.add_node(equal_num, value = "=", type = "operation")
                        op1_num = para_list[num]
                        op2_num = define_list[num]
                        cfg.add_edge(op1_num, equal_num, type = "dataflow")
                        cfg.add_edge(equal_num, op2_num, type="dataflow")
                        cfg.add_edge(label_num, equal_num, type="dataflow")
                    res_list = get_return(g)
                    for res in res_list:
                        cfg.add_edge(label_num, res, type="controlflow")
                        if "=" in line:
                            cfg.add_edge(res, op1_num_res, type="dataflow")

            #递归函数
                if i == fun_name:
                    if "=" in line:
                        op1 = line.split("=")[0].strip()
                        tmp = line.split(" ")
                        op1_type=-1
                        for word in tmp:
                            if check_type(word) != '-1':
                                op1_type = check_type(word)
                                break
                        if op1_type!=-1:
                            op1_name = fun_name + "_" + op1
                            op1_num_res = get_node_num(cfg, op1_name)
                            cfg.add_node(op1_num_res, value = op1_name, type = op1_type)
                    para_list = []
                    index = line.find(i)
                    tmpline = line[index:]
                    index = tmpline.find("(")
                    tmpline = tmpline[index + 1:]
                    index = tmpline.rfind(")")
                    tmpline = tmpline[:index]
                    tmp = tmpline.split(",")
                    if tmpline == "":
                        tmp=[]
                    it = iter(range(len(tmp)))
                    for index in it:
                        part = tmp[index]
                        if "getelementptr" in part:
                            part = tmp[index] + "," + tmp[index + 1] + "," + tmp[index + 2] + "," + tmp[index + 3]+")"
                            part = split_elem(part)
                            getelem_num, type = getelem(cfg, fun_name, part)
                            para_list.append(getelem_num)
                            cfg.add_edge(label_num, getelem_num, type = "controlflow")
                            next(it)
                            next(it)
                            next(it)
                            continue
                        elif "bitcast" in part:
                            pattern = r'@(.*?) '
                            op_tmp = re.findall(pattern,part)[0]
                            op_tmp_name = "@" + op_tmp
                            op_tmp_num = get_node_num(cfg, op_tmp_name)
                            para_list.append(op_tmp_num)
                            continue
                        part = part.strip()
                        op_tmp_type = part.split(" ")[0]
                        op_tmp = part.split(" ")[-1]
                        if op_tmp in globalv:
                            op_tmp_num = get_node_num(cfg, op_tmp)
                            para_list.append(op_tmp_num)
                        elif isDecimalOrIntOrstr(op_tmp):
                            op_tmp_num = node_num
                            node_num = node_num + 1
                            cfg.add_node(op_tmp_num, value = op_tmp, type = op_tmp_type)
                            para_list.append(op_tmp_num)
                        else:
                            op_tmp_name = fun_name + "_" + op_tmp
                            op_tmp_num = get_node_num(cfg, op_tmp_name)
                            para_list.append(op_tmp_num)
                    define_list = g_dist[i + "define"]
                    for num in range(len(para_list)):
                        equal_num = node_num
                        node_num = node_num + 1
                        cfg.add_node(equal_num, value = "=", type = "operation")
                        op1_num = para_list[num]
                        op2_num = define_list[num]
                        cfg.add_edge(op1_num, equal_num, type = "dataflow")
                        cfg.add_edge(equal_num, op2_num, type="dataflow")
                        cfg.add_edge(label_num, equal_num, type="dataflow")
                    res_list = get_return(cfg)
                    for res in res_list:
                        cfg.add_edge(label_num, res, type = "controlflow")
                        if "=" in line:
                            cfg.add_edge(res, op1_num_res, type = "dataflow")


        #load操作
        elif " load" in line:
            if "cin" in line and "bitcast" in line:
                continue
            op1_name = line.split("=")[0].strip()
            op1_name = fun_name + "_" +op1_name
            tmp = line.split("=")[1].strip()
            type = tmp.split(",")[0]
            op1_type = check_type(type)
            op1_num = get_node_num(cfg, op1_name)
            cfg.add_node(op1_num, value = op1_name, type = op1_type)
            op2 = tmp.split(",")[1]
            if "getelementptr" in op2:
                op2 = split_elem(line)
                getelem_num, type = getelem(cfg, fun_name,op2)
                cfg.add_edge(getelem_num, op1_num, type = "dataflow")
                cfg.add_edge(label_num, getelem_num, type="controlflow")
            else:
                tmpline = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", line)
                op2 = tmpline.split(",")[1]
                op2_name = op2.split(' ')[-1]
                if op2_name in globalv:
                    op2_num = get_node_num(cfg,op2_name)
                else:
                    op2_num = get_node_num(cfg, fun_name+"_"+op2_name)
                equal_num = node_num
                node_num = node_num + 1
                cfg.add_node(equal_num, value ="=", type = "operation")
                cfg.add_edge(op2_num, equal_num,type="dataflow")
                cfg.add_edge(equal_num, op1_num, type="dataflow")
                cfg.add_edge(label_num, equal_num, type="controlflow")

        elif "store " in line:
            if "cin" in line and "bitcast" in line:
                continue
            line = line.replace("store","").strip()
            op1 = line.split(",")[0]
            op2 = line.split(",")[1]
            op1_name = op1.split(" ")[-1]
            if isDecimalOrIntOrstr(op1_name):
                op1_num = node_num
                node_num = node_num + 1
                op1_type = op1.split(" ")[-2]
                op1_type = check_type(op1_type)
                cfg.add_node(op1_num, value = op1_name, type = op1_type)
            elif "getelementptr" in op1:
                op1 = split_elem(line)
                op1_num, type = getelem(cfg, fun_name, op1)
                op2 = line.split(",")[-2]
            else:
                tmpline = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", line)
                op1 = tmpline.split(",")[0]
                op1_name = op1.split(" ")[-1]
                if op1_name in globalv:
                    op1_num = get_node_num(cfg, op1_name)
                else:
                    op1_name = fun_name + "_" +op1_name
                    op1_num = get_node_num(cfg, op1_name)
            if "getelementptr" in op2:
                op2 = split_elem(line)
                getelem_num, type = getelem(cfg, fun_name, op2)
                equal_num = node_num
                node_num = node_num + 1
                cfg.add_node(equal_num, value="=", type="operation")
                cfg.add_edge(op1_num, equal_num, type="dataflow")
                cfg.add_edge(equal_num, getelem_num, type="dataflow")
                cfg.add_edge(label_num, getelem_num, type="controlflow")
            else:
                tmpline = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", line)
                op2 = tmpline.split(",")[1]
                op2_name = op2.split(' ')[-1]
                if op2_name in globalv:
                    op2_num = get_node_num(cfg, op2_name)
                else:
                    op2_num = get_node_num(cfg, fun_name + "_" + op2_name)
                equal_num = node_num
                node_num = node_num + 1
                cfg.add_node(equal_num, value="=", type="operation")
                cfg.add_edge(op1_num, equal_num, type="dataflow")
                cfg.add_edge(equal_num, op2_num, type="dataflow")
                cfg.add_edge(label_num, equal_num, type="controlflow")

        #操作符
        elif "cmp" in tmp or "and" in tmp or "sub" in tmp or "mul" in tmp or "div" in tmp or "add" in tmp or "rem" in tmp or "or" in tmp or "sh" in tmp:
            op1 = line.split("=")[0].strip()
            op1_name = fun_name + "_" +op1
            op1_num = get_node_num(cfg, op1_name)
            tmp = line.split("=")[1].strip()
            op = tmp.split(" ")[0]
            op3 = tmp.split(",")[-1]
            op3 = op3.strip()
            tmp = tmp.split(",")[0]
            op2 = tmp.split(" ")[-1]
            op1_type = tmp.split(" ")[-2]
            op1_type = check_type(op1_type)
            cfg.add_node(op1_num, value = op1_name, type = op1_type)
            op_num = node_num
            node_num = node_num + 1
            cfg.add_node(op_num, value = op, type = "operation")
            if isDecimalOrIntOrstr(op2):
                op2_type = get_numtype(op2)
                op2_num = node_num
                node_num = node_num + 1
                cfg.add_node(op2_num, value = op2, type = op2_type)
            else:
                if op2 in globalv:
                    op2_num = get_node_num(cfg, op2)
                else:
                    op2_name = fun_name + "_" + op2
                    op2_num = get_node_num(cfg, op2_name)
            if "getelementptr" in line.split(",")[1]:
                op3 = split_elem(line)
                op3_num, type = getelem(cfg, fun_name, op3)
            else:
                if len(op3.split(" "))>2:
                    if "to" in op3:
                        op3 = op3.split(" ")[-3].strip()
                if isDecimalOrIntOrstr(op3):
                    op3_type = get_numtype(op3)
                    op3_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(op3_num, value = op3, type = op3_type)
                else:
                    if op3 in globalv:
                        op3_num = get_node_num(cfg, op3)
                    else:
                        op3_name = fun_name + "_" + op3
                        op3_num = get_node_num(cfg, op3_name)
            cfg.add_edge(op_num,op1_num,type = "dataflow")
            cfg.add_edge(op2_num,op_num, type = "dataflow")
            cfg.add_edge(op3_num,op_num, type = "dataflow")
            cfg.add_edge(label_num, op_num,type = "controlflow")

        elif ("trunc" in line or "ext" in line or "bitcast" in line or " to " in line) and "getelementptr" not in line:
            op1_name = line.split("=")[0].strip()
            tmp = line.split(" ")
            index = tmp.index("to")
            op2 = tmp[index-1]
            op1_type = tmp[index + 1]
            op1_type = check_type(op1_type)
            op1_name = fun_name + "_" + op1_name
            op1_num = get_node_num(cfg, op1_name)
            cfg.add_node(op1_num, value = op1_name,type = op1_type)
            op2_num = get_node_num(cfg, fun_name+ "_" + op2)
            equal_num = node_num
            node_num = node_num + 1
            cfg.add_node(equal_num, value = "=", type = "operation")
            cfg.add_edge(op2_num, equal_num, type = "dataflow")
            cfg.add_edge(equal_num, op1_num, type = "dataflow")

        elif "select" in line:
            op1 = line.split("=")[0].strip()
            op1_name = fun_name +"_" + op1
            op1_num = get_node_num(cfg, op1_name)
            tmp = line.split(",")
            if "getelementptr" in tmp[1]:
                part = tmp[1] +  ","  + tmp[2] +  ","  + tmp[3] +  ","  + tmp[4] + ")"
                part = split_elem(part)
                op2_num, op1_type = getelem(cfg, fun_name, part)
                part = tmp[5]
            else:
                part = tmp[1].strip()
                op2_type = part.split(" ")[0]
                op1_type = op2_type
                op2 = part.split(" ")[-1]
                if isDecimalOrIntOrstr(op2):
                    op2_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(op2_num, value = op2, type = op2_type)
                else:
                    op2_name = fun_name + "_" +op2
                    op2_num = get_node_num(cfg, op2_name)
                part = tmp[2]
            if "getelementptr" in part:
                part = tmp[5] +  ","  + tmp[6] +  ","  + tmp[7] +  ","  + tmp[8] + ")"
                part = split_elem(part)
                op3_num, op1_type = getelem(cfg, fun_name, part)
            else:
                part = part.strip()
                op3_type = part.split(" ")[0]
                op3 = part.split(" ")[-1]
                if isDecimalOrIntOrstr(op3):
                    op3_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(op3_num, value = op3, type = op3_type)
                else:
                    op3_name = fun_name + "_" +op3
                    op3_num = get_node_num(cfg, op3_name)
            sele_num = node_num
            node_num = node_num + 1
            cfg.add_node(sele_num, value = "select", type = "operation")
            cfg.add_node(op1_num, value = op1_name, type = op1_type)
            cfg.add_edge(sele_num, op1_num, type = "dataflow")
            cfg.add_edge(op2_num, sele_num, type="dataflow")
            cfg.add_edge(op3_num, sele_num, type="dataflow")
            cfg.add_edge(label_num, sele_num, type="dataflow")






        #数组取值：
        elif "getelementptr" in line and "ret" not in line:
            if "cin" in line and "bitcast" in line:
                continue
            op1 = line.split("=")[0].strip()
            op1_name = fun_name + "_" +op1
            op1_num = get_node_num(cfg, op1_name)
            op2 = line.split("=")[1].strip()
            getelem_num, op1_type = getelem(cfg, fun_name, op2)
            cfg.add_node(op1_num, value = op1_name, type = op1_type)
            cfg.add_edge(getelem_num, op1_num, type  = "dataflow")
            cfg.add_edge(label_num, getelem_num, type = "controlflow")


        if -1 in cfg._node:
            print(cfg._node)
        for i in cfg._node:
            if cfg._node[i]['type'] == "":
                print(cfg._node)
                raise 1
    return cfg

def remove_equal(g):
    remove_list = []
    for i in g._node:
        if (g._node[i]['value'] == "=" or g._node[i]['value'] == "equal") and g._node[i]['type'] == "operation":
            inedge_list = g.in_edges(i)
            outedge_list = g.out_edges(i)
            innode_list = []
            outnode_list = []
            new_outnode_list = []
            for edge in inedge_list:
                node = edge[0]
                if g._node[node]['type'] != "label":
                    innode_list.append(node)
            for edge in outedge_list:
                node = edge[1]
                outnode_list.append(node)
                #等号只有一个输入输出
            if len(innode_list) == 1 and len(outnode_list) == 1:
                outnode = outnode_list[0]
                tmp = g.in_edges(outnode)
                # 当等号的输出节点只有等号一个作为输入时，输入取代输出
                if len(tmp) == 1:
                    remove_list.append(i)
                    remove_list.append(outnode)
                    new_outedge_list = g.out_edges(outnode)
                    for edge in new_outedge_list:
                        node = edge[1]
                        new_outnode_list.append(node)
                    in_node= innode_list[0]
                    for node in new_outnode_list:
                        g.add_edge(in_node, node, type = "dataflow")
    return g, remove_list

def remove_label(g):
    # 没有输出或仅仅只有跳转
    remove_list = []
    for i in g._node:
        if g._node[i]['type'] == "label":
            inedge_list = g.in_edges(i)
            outedge_list = g.out_edges(i)
            innode_list = []
            outnode_list = []

            for edge in inedge_list:
                node = edge[0]
                innode_list.append(node)
            for edge in outedge_list:
                node = edge[1]
                outnode_list.append(node)
            if len(outnode_list) == 0:
                remove_list.append(i)
            if len(outnode_list) == 1:
                node = outnode_list[0]
                if g._node[node]["type"] == "label":
                    remove_list.append(i)
                    for innode in innode_list:
                        g.add_edge(innode, node, type = "controlflow")
    return g, remove_list

def opt_graph(g):
    remove_node = []
    for i in g:
        if g.nodes[i]['type'] != 'invoke' and g.nodes[i]['type'] != 'operation' and g.nodes[i]['type'] != 'label':
            inedge_list = g.in_edges(i)
            if len(inedge_list) != 0:
                inedge_equalnode_list = []
                inedge_notequalnode_list = []
                outedge_node_list = []
                inedge_node_list = []
                outedge_list = g.out_edges(i)
                if len(outedge_list) == 0:
                    remove_node.append(i)
                else:
                    for edge in outedge_list:
                        op_node = edge[1]
                        outedge_node_list.append(op_node)
                    for edge in inedge_list:
                        op_node = edge[0]
                        if g.nodes[op_node]['value'] == '=':
                            inedge_equalnode_list.append(op_node)
                        else:
                            inedge_notequalnode_list.append(op_node)
                    if len(inedge_notequalnode_list) == 0 and len(inedge_equalnode_list) != 0:
                        inedge_node_list = inedge_equalnode_list
                    if len(inedge_equalnode_list) == 0 and len(inedge_notequalnode_list) != 0:
                        inedge_node_list = inedge_notequalnode_list
                    if len(inedge_notequalnode_list) != 0 and len(inedge_equalnode_list) != 0:
                        for node1 in inedge_equalnode_list:
                            for node2 in inedge_notequalnode_list:
                                g.add_edge(node1,node2)
                        inedge_node_list = inedge_notequalnode_list
                    for node1 in inedge_node_list:
                        for node2 in outedge_node_list:
                            g.add_edge(node1,node2)
                    remove_node.append(i)
    return g, remove_node


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False

def opt_word(g):
    global vocab
    for i in g:
        if g._node[i]['type'] == "invoke":
            word = g._node[i]['value']
            if "abs" in word:
                word = "abs"
            if "ato" in word:
                word = "ato"
            if "floor" in word:
                word = "floor"
            if "max" in word:
                word = "max"
            if "min" in word:
                word = "min"
            if "sqrt" in word:
                word = "sqrt"
            if "pow" in word:
                word = "pow"
            if "log10" in word:
                word = "log10"
            if "log2" in word:
                word = "log2"
            if "swap" in word:
                word = "swap"
            if "sort" in word:
                word = "sort"
            if "isprimei" in word:
                word = "isprimei"
            if "ceil" in word:
                word = "ceil"
            if "mod" in word:
                word = "mod"
            if "cmp" in word:
                word = "cmp"
            if "div" in word:
                word = "div"
            if "log" in word and "log2" not in word and "log10" not in word:
                word = "log"
            if "strn" in word:
                word = word.replace("strn", "str")
            if word[1:] in vocab:
                word = word[1:]
            if word in vocab:
                pass
            else:
                vocab.add(word)
            g._node[i]['value'] = word
    return g



def graph2json(g):
    graph_json = {}
    tar_json = {}
    for i in g:
        node_dict = {}
        #变量
        if g.nodes[i]['type'] == 'label':
            node = "label"
        elif g.nodes[i]['type'] == "invoke" or g.nodes[i]['type'] == 'operation':
            node = g.nodes[i]['value']
        elif "globle" in g.nodes[i]['type']:
            if "@.str" in g.nodes[i]['value'] or "main" in g.nodes[i]['value']:
                node = g.nodes[i]['type'].replace("globle","")
            else:
                node = g.nodes[i]['type']
        else:
            node = g.nodes[i]['type']
        node_dict['node'] = node
        snode = list(g[i].keys())
        node_dict['snode'] = snode
        graph_json[i] = node_dict
    #修改序号
    index = list(range(len(graph_json)))
    index_dict = dict(zip(list(graph_json.keys()),index))
    for i in graph_json:
        tmp_dic = {}
        node_index = index_dict[i]
        snode = []
        for j in graph_json[i]['snode']:
            tmp_snode = index_dict[j]
            snode.append(tmp_snode)
        tmp_dic['node'] = graph_json[i]['node']
        tmp_dic['snode'] = snode
        tar_json[node_index] = tmp_dic
    return tar_json




wrong_path = "wrong.txt"
true_path = "true.txt"
pojpath = "D:\POJ_104"
IRfilepath = pojpath + "\\ir"
gmlfilepath = pojpath + "\\gml"
for dir in os.listdir(IRfilepath):
    for dirfile in os.listdir(IRfilepath+"\\"+dir):
        # try:
            file = IRfilepath+"\\"+dir+"\\"+dirfile
            dirpath = gmlfilepath + "\\" + dir
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
            print(file)
            file = "D:\POJ_104\ir\\101D\\12.ll"
            function_dict, globalv = get_fun(file)

            node_num = 0
            g_dist={}
            defalt_graph = nx.DiGraph()

            # 添加全局变量
            for i in globalv:
                global_num = node_num
                node_num = node_num + 1
                defalt_graph.add_node(global_num, value=i, type=globalv[i])
            g = build_graph(defalt_graph, 'main',function_dict['main'])
            print(len(g_dist))

            #等号赋值
            while(1):
                tmp_len = len(g._node)
                g, remove_list = remove_equal(g)
                for i in remove_list:
                    g.remove_node(i)
                if tmp_len == len(g):
                    break
            #空转移节点
            while(1):
                tmp_len = len(g._node)
                g, remove_list = remove_label(g)
                for i in remove_list:
                    g.remove_node(i)
                if tmp_len == len(g):
                    break
            #删除中间变量
            while(1):
                tmp_len = len(g._node)
                g, remove_list = opt_graph(g)
                for i in remove_list:
                    g.remove_node(i)
                if tmp_len == len(g):
                    break
            #孤立节点
            remove_list = []
            for i in g:
                if g.degree[i] == 0:
                    remove_list.append(i)
            for i in remove_list:
                g.remove_node(i)

            g = opt_word(g)
            print(len(g._node))
            g_json = graph2json(g)
            for i in g_json:
                if g_json[i]['node'] == "":
                    raise 1
            print(g_json)

            with open(dirpath+"\\"+dirfile.replace("ll","json"),"w+")as f:
                f.write(json.dumps(g_json))






