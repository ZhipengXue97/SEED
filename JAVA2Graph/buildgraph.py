import re
import networkx as nx
import os
import json
import matplotlib.pyplot as plt

#提取函数调用关系
#返回值、调用、函数名、参数
def get_invoke(str):
    pattern = r"<(.*?):"
    invoke_class = re.findall(pattern, str)[0]
    if '=' in str:
        tmp = str.replace(" ",'')
        res = tmp.split('=')[0]
    else:
        res = ""
    pattern = r"[(](.*?)[)]"
    para1 = re.findall(pattern, str)[1].split(',')
    para = []
    for i in para1:
        i = i.strip()
        para.append(i)
    pattern = r":\s(.*?)[(]"
    name = re.findall(pattern, str)[0].split(" ")[1]
    if ".<" in str:
        pattern = r"\s(.*?).<"
        ob = re.findall(pattern, str)[0].split(" ")[-1]
    else:
        ob = ""
    return invoke_class, res, ob, name, para

#提取操作
#返回值、操作数一，操作符，操作数二
def get_op(str):
    res = str.split('=')[0].replace(' ','')
    tmp = str.split('=')[1].split(' ')
    op1 = tmp[1]
    op2 = tmp[-1].replace(';','')
    op = tmp[-2]
    return res, op1, op, op2

#提取If
#操作数一，比较符，操作数二，目标
def get_if(str):
    tmp = str.split(' ')
    tar = tmp[-1].replace(';','')
    op1 = tmp[-5]
    op = tmp[-4]
    op2 = tmp[-3]
    return op1, op, op2, tar


#提取变量
def get_type(str):
    var = []
    tmp = str.split(',')
    type = tmp[0].split(' ')[0]
    var.append(tmp[0].split(' ')[1].replace(';',''))
    tmp = tmp[1:]
    for i in tmp:
        i = i.replace(' ','')
        i = i.replace(';','')
        var.append(i)
    return type, var

#提取常量类型
def get_numtype(str):
    if str == "null" :
        return str, "null"
    if str[0] == '"' and str[-1] == '"':
        num = str
        return  num, "string"
    elif '.' in str:
        str = str.replace('F','')
        num = float(str)
        return num, "float"
    else:
        pattern = '-?\d+'
        num = re.findall(pattern, str)[0]
        return int(num), "int"

#判断是否为常数
def isDecimalOrIntOrstr(str):
    #去除字符串两边的空格
    s= str.strip()
    flag = True
    #判断是否是null
    if s == "null":
        return flag
    #判断是否是字符串
    if str[0] == '"' and str[-1] == '"':
        return flag
    decRet= re.match("-?\d+\.?\d*e?-?\d*?",s)
    if decRet:
        return flag
    flag = False
    return flag

#根据变量名取node值
def get_node_num(cfg, value):
    for i in cfg.nodes:
        if 'value' in cfg.nodes[i]:
            if cfg.nodes[i]['value'] == value:
                return i
    return -1

def get_return(fun_body):
    res=[]
    lines = []
    for i in fun_body:
        i = i.replace('\n', '')
        lines.append(i)
    for line in lines:
        if "return" in line and "invoke" not in line and "=" not in line and "if" not in line:
            line = line.replace(' ','')
            if "return;" in line:
                continue
            else:
                line = line.replace('return','')
                line = line.replace(';','')
                res.append(line)
    return res

def get_para(fun_body):
    res=[]
    lines = []
    for i in fun_body:
        i = i.replace('\n', '')
        lines.append(i)
    for line in lines:
        if ":= @parameter" in line:
            tmp = line.split(':= @parameter')[0].replace(' ','')
            res.append(tmp)
    return res

def build_globalvar_graph():
    global node_num
    cfg = nx.DiGraph()
    for i in globalv:
        global_num = node_num
        node_num = node_num + 1
        type = i.split(' ')[0]
        if type == classname:
            type = "mainclass"
        if "." in type:
            type = type.split('.')[-1].lower()
        cfg.add_node(global_num, value=i, type=type)
    return cfg



def build_graph(fun_name, fun_body):
    global node_num
    lines=[]
    cfg = nx.DiGraph()
    cfg = nx.compose(cfg,gfg)
    for i in fun_body:
        i = i.replace('\n','')
        lines.append(i)

    #添加所有变量节点
    for line in lines:
        line = line.strip()
        if '{' in line:
            continue
        if line == '' or "case" in line:
            break
        type,var = get_type(line)
        if type == classname:
            type = "mainclass"
        if "." in type:
            type = type.split('.')[-1].lower()
        for j in var:
            tmp_node_num = node_num
            node_num = node_num + 1
            cfg.add_node(tmp_node_num, value = fun_name+"_"+j, type = type)



    #添加标签
    for line in lines:
        if "label" in line and ":" in line:
            pattern = r'\d+'
            label_index = re.findall(pattern, line)[0]
            label_name = "label" + label_index
            label_num = node_num
            node_num = node_num + 1
            cfg.add_node(label_num, value=fun_name+"_"+label_name, type="label")
    label_name = fun_name+"_"+"start"
    label_num = node_num
    node_num = node_num + 1
    cfg.add_node(label_num, value = label_name, type = "label")



    #添加边
    for line in lines:
        line = line.strip()
        line = line.replace(';','')
        # print(line)

        #标签跳转
        if "label" in line and ":" in line:
            pattern = r'\d+'
            label_index = re.findall(pattern, line)[0]
            label_name = "label" + label_index
            label_num = get_node_num(cfg, fun_name+"_"+label_name)

        elif "invoke" in line:
            inclass, res, ob, name, para = get_invoke(line)
            #调用API
            if name not in function_name or inclass != classname:
                tmp_num_invoke = node_num
                node_num = node_num + 1
                cfg.add_node(tmp_num_invoke, value = name, type = "invoke")
                cfg.add_edge(label_num, tmp_num_invoke,type = "controlflow")
                if ob != '':
                    ob_num = get_node_num(cfg, fun_name+"_"+ob)
                    cfg.add_edge(ob_num,tmp_num_invoke,type = "dataflow")
                if res != '':
                    res_num = get_node_num(cfg, fun_name+"_"+res)
                    cfg.add_edge(tmp_num_invoke,res_num,type = "dataflow")
                if para != ['']:
                    for p in para:
                        p_num = get_node_num(cfg, fun_name+"_"+p)
                        if p_num != -1:
                            cfg.add_edge(p_num ,tmp_num_invoke,type = "dataflow")
                        elif isDecimalOrIntOrstr(p):
                                p_num = node_num
                                node_num = node_num + 1
                                num, type = get_numtype(p)
                                cfg.add_node(p_num, value=num, type=type)
                                cfg.add_edge(p_num, tmp_num_invoke,type = "dataflow")
            #递归函数
            elif name == fun_name:
                start_node_num = get_node_num(cfg, name+"_"+"start")
                cfg.add_edge(label_num, start_node_num,type = "controlflow")
                if res != '':
                    res_node_num = get_node_num(cfg, fun_name+"_"+res)
                    return_node_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(return_node_num, value = "=", type = "operation")
                    cfg.add_edge(return_node_num,res_node_num, type = "dataflow")
                    return_list = get_return(function_dict[name])
                    for r in return_list:
                        r_num = get_node_num(cfg, name+"_"+r)
                        if r_num != -1:
                            cfg.add_edge(r_num, return_node_num, type="dataflow")
                        elif isDecimalOrIntOrstr(r):
                                r_num = node_num
                                node_num = node_num + 1
                                num, type = get_numtype(r)
                                cfg.add_node(r_num, value=num, type=type)
                                cfg.add_edge(r_num, return_node_num, type="dataflow")
                if para != ['']:
                    p_list = get_para(function_dict[name])
                    for p in range(len(para)):
                        equl_num = node_num
                        node_num = node_num + 1
                        cfg.add_node(equl_num, value="=", type="operation")
                        op1 = p_list[p]
                        op2 = para[p]
                        op1_num = get_node_num(cfg, name+"_"+op1)
                        cfg.add_edge(equl_num, op1_num, type = "dataflow")
                        op2_num = get_node_num(cfg, fun_name+"_"+op2)
                        if op2_num != -1:
                            cfg.add_edge(op2_num, equl_num, type="dataflow")
                        elif isDecimalOrIntOrstr(op2):
                            op2_num = node_num
                            node_num = node_num + 1
                            num, type = get_numtype(op2)
                            cfg.add_node(op2_num, value=num, type=type)
                            cfg.add_edge(op2_num, equl_num, type="dataflow")

            #普通函数调用
            elif name in function_name and name != fun_name:
                if name not in g_dist:
                    g=build_graph(name, function_dict[name])
                    g_dist[name] = g
                else:
                    g = g_dist[name]
                cfg = nx.compose(cfg, g)
                start_node_num = get_node_num(cfg, name+"_"+"start")
                cfg.add_edge(label_num, start_node_num, type = "controlflow")
                if res != '':
                    res_node_num = get_node_num(cfg, fun_name + "_" + res)
                    return_node_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(return_node_num, value = "=", type = "operation")
                    cfg.add_edge(return_node_num, res_node_num, type="dataflow")
                    return_list = get_return(function_dict[name])
                    for r in return_list:
                        r_num = get_node_num(cfg, name+"_"+r)
                        if r_num != -1:
                            cfg.add_edge(r_num, return_node_num, type="dataflow")
                        elif isDecimalOrIntOrstr(r):
                                r_num = node_num
                                node_num = node_num + 1
                                num, type = get_numtype(r)
                                cfg.add_node(r_num, value=num, type=type)
                                cfg.add_edge(r_num, return_node_num, type="dataflow")
                if para != ['']:
                    p_list = get_para(function_dict[name])
                    for p in range(len(para)):
                        equl_num = node_num
                        node_num = node_num + 1
                        cfg.add_node(equl_num, value="=", type="operation")
                        op1 = p_list[p]
                        op2 = para[p]
                        op1_num = get_node_num(cfg, name + "_" + op1)
                        cfg.add_edge(equl_num, op1_num, type="dataflow")
                        op2_num = get_node_num(cfg, fun_name + "_" + op2)
                        if op2_num != -1:
                            cfg.add_edge(op2_num, equl_num, type="dataflow")
                        elif isDecimalOrIntOrstr(op2):
                            op2_num = node_num
                            node_num = node_num + 1
                            num, type = get_numtype(op2)
                            cfg.add_node(op2_num, value=num, type=type)
                            cfg.add_edge(op2_num, equl_num, type="dataflow")

        #运算操作
        elif ("/" in line or "%" in line or "+" in line or "-" in line or "*" in line or "cmp" in line) and "if" not in line and ":"not in line and "["not in line and "return" not in line:
            res, op1, op, op2 = get_op(line)
            op_node_num = node_num
            node_num = node_num + 1
            cfg.add_node(op_node_num, value = op, type = "operation")
            cfg.add_edge(label_num, op_node_num, type="controlflow")
            op1_num = get_node_num(cfg, fun_name+"_"+op1)
            if op1_num != -1:
                cfg.add_edge(op1_num, op_node_num,type = "dataflow")
            elif isDecimalOrIntOrstr(op1):
                op1_num = node_num
                node_num = node_num + 1
                num, type = get_numtype(op1)
                cfg.add_node(op1_num, value=num, type=type)
                cfg.add_edge(op1_num, op_node_num, type = "dataflow")
            op2_num = get_node_num(cfg, fun_name+"_"+op2)
            if op2_num != -1:
                cfg.add_edge(op2_num, op_node_num,type = "dataflow")
            elif isDecimalOrIntOrstr(op2):
                op2_num = node_num
                node_num = node_num + 1
                num, type = get_numtype(op2)
                cfg.add_node(op2_num, value=num, type=type)
                cfg.add_edge(op2_num, op_node_num, type = "dataflow")
            res_num = get_node_num(cfg, fun_name+"_"+res)
            cfg.add_edge(op_node_num, res_num, type = "dataflow")

        #数组取值
        elif "[" in line and "=" in line and '<' not in line:
            i = line.replace(' ','')
            left = i.split('=')[0]
            right = i.split('=')[1]
            if "[" in left:
                for j in range(len(left)):
                    if left[j] == "[":
                        op = left[:j]
                        op = op.split(' ')[-1]
                        break
                op_num = get_node_num(cfg, fun_name+"_"+op)
                if op_num != -1:
                    pattern = r"[[](.*?)[]]"
                    para = re.findall(pattern, left)
                    getelem_node_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(getelem_node_num, value = "getelement", type = "operation")
                    cfg.add_edge(op_num, getelem_node_num,type = "dataflow")
                    cfg.add_edge(label_num, getelem_node_num, type="controlflow")
                    for p in para:
                        p_num = get_node_num(cfg, fun_name+"_"+p)
                        if p_num != -1:
                            cfg.add_edge(p_num, getelem_node_num, type="dataflow")
                        elif isDecimalOrIntOrstr(p):
                            para_num = node_num
                            node_num = node_num + 1
                            num, type = get_numtype(p)
                            cfg.add_node(para_num, value=num, type=type)
                            cfg.add_edge(para_num, getelem_node_num, type="dataflow")
                    right_num = get_node_num(cfg, fun_name+"_"+right)
                    if right_num != -1:
                        cfg.add_edge(right_num,getelem_node_num, type="dataflow")
                    elif isDecimalOrIntOrstr(right):
                        right_num = node_num
                        node_num = node_num + 1
                        num, type = get_numtype(right)
                        cfg.add_node(right_num, value=num, type=type)
                        cfg.add_edge(right_num, getelem_node_num, type="dataflow")
                    elif "<" in right and ":" in right:
                        for glv in globalv:
                            if glv in right:
                                right_num = get_node_num(cfg, glv)
                                cfg.add_edge(right_num, getelem_node_num, type="dataflow")

            if "[" in right:
                for j in range(len(right)):
                    if right[j] == "[":
                        op = right[:j]
                        op = op.split(' ')[-1]
                        break
                op_num = get_node_num(cfg, fun_name+"_"+op)
                if op_num != -1:
                    pattern = r"[[](.*?)[]]"
                    para = re.findall(pattern, right)
                    getelem_node_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(getelem_node_num, value = "getelement", type = "operation")
                    cfg.add_edge(op_num, getelem_node_num,type = "dataflow")
                    cfg.add_edge(label_num, getelem_node_num, type="controlflow")
                    for p in para:
                        p_num = get_node_num(cfg, fun_name+"_"+p)
                        if p_num != -1:
                            cfg.add_edge(p_num, getelem_node_num, type="dataflow")
                        elif isDecimalOrIntOrstr(p):
                            para_num = node_num
                            node_num = node_num + 1
                            num, type = get_numtype(p)
                            cfg.add_node(para_num, value=num, type=type)
                            cfg.add_edge(para_num, getelem_node_num, type="dataflow")
                    left_num = get_node_num(cfg, fun_name+"_"+left)
                    cfg.add_edge(getelem_node_num, left_num, type="dataflow")

        # if语句
        elif "if" in line:
            op1, op, op2, tar = get_if(line)
            op_node_num = node_num
            node_num = node_num + 1
            cfg.add_node(op_node_num, value=op, type="operation")
            cfg.add_edge(label_num, op_node_num, type = "controlflow")
            tar_label_num = get_node_num(cfg, fun_name+"_"+tar)
            false_node_num = node_num
            node_num = node_num + 1
            cfg.add_node(false_node_num, value=False, type="label")
            label_num = false_node_num
            op1_num = get_node_num(cfg, fun_name+"_"+op1)
            if op1_num != -1:
                cfg.add_edge(op1_num, op_node_num, type="dataflow")
            elif isDecimalOrIntOrstr(op1):
                op1_num = node_num
                node_num = node_num + 1
                num, type = get_numtype(op1)
                cfg.add_node(op1_num, value=num, type=type)
                cfg.add_edge(op1_num, op_node_num, type="dataflow")
            op2_num = get_node_num(cfg, fun_name+"_"+op2)
            if op2_num != -1:
                cfg.add_edge(op_node_num, op2_num, type="dataflow")
                cfg.add_edge(op2_num, tar_label_num, type="controlflow")
                cfg.add_edge(op2_num, false_node_num, type="controlflow")
            elif isDecimalOrIntOrstr(op2):
                op2_num = node_num
                node_num = node_num + 1
                num, type = get_numtype(op2)
                cfg.add_node(op2_num, value=num, type=type)
                cfg.add_edge(op_node_num, op2_num, type="dataflow")
                cfg.add_edge(op2_num, tar_label_num, type="controlflow")
                cfg.add_edge(op2_num, false_node_num, type="controlflow")

        # 添加switch
        elif "tableswitch" in line:
            op_num = node_num
            node_num = node_num + 1
            cfg.add_node(op_num, value = "switch", type = "operation")
            pattern = r'[(](.*?)[)]'
            op1 = re.findall(pattern,line)[0]
            switch_num = get_node_num(cfg, fun_name+"_"+op1)
            cfg.add_edge(op_num, switch_num, type = "controflow")

        elif "case" in line and "goto label" in line:
            tar = line.split(" ")[-1]
            tar_label_num = get_node_num(cfg,fun_name+"_"+tar)
            cfg.add_edge(switch_num, tar_label_num, type = "controflow")
        elif "default" in line and "goto label" in line:
            tar = line.split(" ")[-1]
            tar_label_num = get_node_num(cfg,fun_name+"_"+tar)
            cfg.add_edge(switch_num, tar_label_num, type = "controflow")

        #goto语句
        elif "goto" in line:
            tmp = line.split(' ')[-1]
            tar = tmp.replace(';','')
            tar_label_num = get_node_num(cfg, fun_name+"_"+tar)
            cfg.add_edge(label_num, tar_label_num,type = "controlflow")

        #最后赋值语句、类型转换语句
        elif '=' in line:
            op1 = line.split('=')[0]
            op1 = op1.strip()
            op1_num = get_node_num(cfg, fun_name+"_"+op1)
            #忽略对全局变量赋值
            op2 = line.split('=')[-1]
            op2_num = get_node_num(cfg, op2)
            if "<" in op2 and ":" in op2:
                for glv in globalv:
                    if glv in op2:
                        op2_num = get_node_num(cfg, glv)
            else:
                op2 = line.split('=')[-1]
                op2 = op2.split(' ')[-1]
                op2 = op2.strip()
                op2 = op2.replace(';','')
                op2_num = get_node_num(cfg, fun_name+"_"+op2)
            if op1_num != -1:
                if op2_num != -1:
                    equl_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(equl_num, value = "=", type="operation")
                    cfg.add_edge(label_num, equl_num, type="controlflow")
                    cfg.add_edge(op2_num, equl_num,type="dataflow")
                    cfg.add_edge(equl_num, op1_num,type="dataflow")
                if isDecimalOrIntOrstr(op2):
                    value_num = node_num
                    node_num = node_num + 1
                    equl_num = node_num
                    node_num = node_num + 1
                    cfg.add_node(equl_num, value = "=", type="operation")
                    cfg.add_edge(label_num, equl_num, type="controlflow")
                    num, type = get_numtype(op2)
                    cfg.add_node(value_num, value = num, type = type)
                    cfg.add_edge(value_num, equl_num, type="dataflow")
                    cfg.add_edge(equl_num, op1_num,type="dataflow")
    return cfg

def get_fun(file):
    with open(file) as f:
        content = f.readlines()

    #类名
    line = content[0]
    line = line.split(' ')
    id = line.index('class')
    classname = line[id+1]

    #全局变量
    globalv = []
    for i in range(len(content)):
        if content[i]=='\n':
            glv = content[2: i]
            break
    for i in glv:
        i = i.replace(';','')
        i = i.replace('\n','')
        i = i.strip()
        i = i.split(' ')
        i = i[-2]+' '+i[-1]
        globalv.append(i)

    # function name
    function_name = []
    for line in  content:
        s = line.replace('.','')
        pattern = r'(public\s|private\s|protected\s)?(static\s)?(final\s)?\s?(\S+)\s(\S+)\((\S+.*\S*)?\)$'
        s = s.split('\n')
        for line in s:
            index = line.find('throws')
            if index!=-1:
                line = line[:index-1]
            p = re.findall(pattern, line)
            if p!= []:
                function_name.append(p[0][-2])


    #function body
    function_body = []
    l_position = 0
    r_position = 0

    for i in range(len(content)):
        line = content[i].strip()
        if line=='{':
            if "switch" not in content[i-1].strip():
               l_position = i
        if line=='}':
            r_position = i
        if l_position != 0 and r_position != 0:
            function_body.append(content[l_position: r_position+1])
            l_position = 0
            r_position = 0
    if len(function_name) == len(function_body):
        function_dict = dict(zip(function_name,function_body))
    return classname, function_name, function_body, function_dict, globalv

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


#图转成json格式
def grapg2json(g):
    graph_json = {}
    tar_json = {}
    for i in g:
        node_dict = {}
        #变量
        if g.nodes[i]['type'] != 'invoke' and g.nodes[i]['type'] != 'operation':
            node = g.nodes[i]['type']
            if "[]" in node:
                node = node.replace('[]','')
                node = node+'[]'
        elif g.nodes[i]['type'] == 'invoke' or g.nodes[i]['type'] == 'operation':
            node = g.nodes[i]['value']
        node_dict['node'] = node
        snode = list(g[i].keys())
        node_dict['snode'] = snode
        graph_json[i] = node_dict
    index = list(range(len(graph_json)))
    index_dict = dict(zip(list(graph_json.keys()),index))
    for i in graph_json:
        tmp_dic = {}
        node_index = index_dict[i]
        snode=[]
        for j in graph_json[i]['snode']:
            tmp_snode = index_dict[j]
            snode.append(tmp_snode)
        tmp_dic['node'] = graph_json[i]['node']
        tmp_dic['snode'] = snode
        tar_json[node_index] = tmp_dic

    return tar_json



codeforcepath = "E:\codeforces"
jimplefilepath = codeforcepath + "\\jimple"
jsonfilepath = codeforcepath + "\\json"

wrong_path = "wrong.txt"
true_path = "true.txt"
n=0
for dir in os.listdir(jimplefilepath):
    for dirfile in os.listdir(jimplefilepath+"\\"+dir):
        try:
            file = jimplefilepath+"\\"+dir+"\\"+dirfile
            dirpath = jsonfilepath+"\\"+dir
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
            # file = "E:\codeforces\jimple\\107E\\2.jimple"
            print(file)
            n=n+1
            print(n)
            node_num = 0
            g_dist={}
            classname, function_name, function_body, function_dict, globalv = get_fun(file)
            gfg = build_globalvar_graph()
            G = build_graph("main", function_dict['main'])
            remove_node=[]
            for i in G:
                if G.degree[i]==0:
                    remove_node.append(i)
            for i in remove_node:
                G.remove_node(i)
            G, remove_node = opt_graph(G)
            for i in remove_node:
                G.remove_node(i)
            g_json = grapg2json(G)
            if len(g_json) != len(G._node):
                raise ValueError("json和图不匹配")
            if len(G._node) <= 0 or -1 in G._node:
                with open(wrong_path, 'a') as f:
                    f.write(file)
                    f.write("\n")
                    if len(G._node) <= 0:
                        f.write("null")
                        f.write("\n")
                    if -1 in G._node:
                        f.write("-1")
                        f.write("\n")
            else:
                with open(true_path,'a') as f:
                    f.write(file)
                    f.write("\n")
                    f.write(str(len(G._node)))
                    f.write("\n")
                with open(jsonfilepath+"\\"+dir+"\\"+dirfile.replace('jimple','')+"json", 'w+') as f:
                    f.write(json.dumps(g_json))
        except Exception as e:
            with open(wrong_path, 'a') as f:
                f.write(file)
                f.write("\n")
                f.write(repr(e))
                f.write("\n")
            continue