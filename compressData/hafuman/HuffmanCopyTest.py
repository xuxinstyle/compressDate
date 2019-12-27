# -*- coding: utf-8 -*-
import sys
import os

sys.setrecursionlimit(1000000)  # 压缩大文件实时会出现超出递归深度，故修改限制


# tell() 函数用于判断文件指针当前所处的位置，而
# seek() 函数用于移动文件指针到文件的指定位置。

# 定义哈夫曼树的节点类
class node(object):

    def __init__(self, value=None, left=None, right=None, father=None):
        self.value = value
        self.left = left
        self.right = right
        self.father = father

    def build_father(left, right):
        n = node(value=left.value + right.value, left=left, right=right)
        left.father = right.father = n
        return n

    def encode(n):
        if n.father == None:
            return b''
        if n.father.left == n:
            return node.encode(n.father) + b'0'  # 左节点编号'0'
        else:
            return node.encode(n.father) + b'1'  # 右节点编号'1'


# 哈夫曼树构建
def build_tree(l):
    if len(l) == 1:
        return l
    sorts = sorted(l, key=lambda x: x.value, reverse=False)
    n = node.build_father(sorts[0], sorts[1])
    sorts.pop(0)
    sorts.pop(0)
    sorts.append(n)
    return build_tree(sorts)


def encode(echo):
    for x in node_dict.keys():
        ec_dict[x] = node.encode(node_dict[x])
        if echo == True:  # 输出编码表（用于调试）
            print(x)
            print(ec_dict[x])


# 将指定的文件路径转换成该目录下以

def encodefile(inputfile, encodePath, encodeSuffix):
    print("Starting encode...")
    f = {}
    count = {}
    nodes = []  # 结点列表，用于构建哈夫曼树
    buff = {}
    for parent, dirname, filenames in os.walk(inputfile):
        index1 = 0
        while index1 < len(filenames):
            filename = parent + "\\" + filenames[index1]
            print(filename)
            f[index1] = open(filename, "rb")
            bytes_width = 1  # 每次读取的字节宽度
            i = 0

            f[index1].seek(0, 2)
            count[index1] = f[index1].tell() / bytes_width
            print(count[index1])

            buff[index1] = [b''] * int(count[index1])
            f[index1].seek(0)

            # 计算字符频率,并将单个字符构建成单一节点
            while i < count[index1]:
                buff[index1][i] = f[index1].read(bytes_width)
                if count_dict.get(buff[index1][i], -1) == -1:
                    count_dict[buff[index1][i]] = 0
                count_dict[buff[index1][i]] = count_dict[buff[index1][i]] + 1
                i = i + 1
            index1 = index1 + 1
    print("Read OK")
    print(count_dict)  # 输出权值字典,可注释掉
    for x in count_dict.keys():
        node_dict[x] = node(count_dict[x])
        nodes.append(node_dict[x])

    findex = 0
    while findex < len(f):
        f[findex].close()
        findex = findex + 1
    tree = build_tree(nodes)  # 哈夫曼树构建

    encode(False)  # 构建编码表
    print("Encode OK")

    head = sorted(count_dict.items(), key=lambda x: x[1], reverse=True)  # 对所有根节点进行排序
    bit_width = 1
    print("head:", head[0][1])  # 动态调整编码表的字节长度，优化文件头大小
    if head[0][1] > 255:
        bit_width = 2
        if head[0][1] > 65535:
            bit_width = 3
            if head[0][1] > 16777215:
                bit_width = 4
    print("bit_width:", bit_width)


    name = inputfile.split('\\')
    filenamecsv = name[len(name) - 1].split(".")

    compressDatePath = encodePath + "data" + encodeSuffix

    o = open(compressDatePath, 'wb')

    for parent, dirname, filenames in os.walk(inputfile):

        index2 = 0
        while index2 < len(filenames):
            i = 0
            raw = 0b1
            last = 0
            filename = parent +  filenames[index2]
            print(filename)
            split = filename.split("\\")
            filename = split[len(split) - 1]

            if(index2 == 0):
                o.write((filename + '\n').encode(encoding="utf-8"))  # 写出原文件名
            else:
                o.write(('\n' + filename + '\n').encode(encoding="utf-8"))  # 写出原文件名
            o.write(int.to_bytes(len(ec_dict), 2, byteorder='big'))  # 写出结点数量
            o.write(int.to_bytes(bit_width, 1, byteorder='big'))  # 写出编码表字节宽度
            for x in ec_dict.keys():  # 编码文件头
                o.write(x)
                o.write(int.to_bytes(count_dict[x], bit_width, byteorder='big'))


            print('head OK')
            while i < count[index2]:  # 开始压缩数据
                for x in ec_dict[buff[index2][i]]:
                    raw = raw << 1
                    if x == 49:
                        raw = raw | 1
                    if raw.bit_length() == 9:
                        raw = raw & (~(1 << 8))
                        o.write(int.to_bytes(raw, 1, byteorder='big'))
                        o.flush()
                        raw = 0b1
                        tem = int(i / len(buff[index2]) * 100)
                        if tem > last:
                            print("encode:", tem, '%')  # 输出压缩进度
                            last = tem
                i = i + 1

            if raw.bit_length() > 1:  # 处理文件尾部不足一个字节的数据
                raw = raw << (8 - (raw.bit_length() - 1))
                raw = raw & (~(1 << raw.bit_length() - 1))
                o.write(int.to_bytes(raw, 1, byteorder='big'))
            index2 = index2 + 1
    o.close()
    print("File encode successful.")


def decodefile(inputfile, decodePath, decodeSuffix):
    print("Starting decode...")
    count = 0
    raw = 0
    last = 0
    f = open(inputfile, 'rb')
    f.seek(0, 2)
    eof = f.tell()
    f.seek(0)

    name = inputfile.split('/')
    outputfile = inputfile.replace(name[len(name) - 1], f.readline().decode(encoding="utf-8"))
    # decodefilename = decodePath + "decodeDate" + decodeSuffix
    o = open(outputfile.replace('\n', ''), 'wb')
    # o = open(decodefilename, 'wb')
    count = int.from_bytes(f.read(2), byteorder='big')  # 取出结点数量
    bit_width = int.from_bytes(f.read(1), byteorder='big')  # 取出编码表字宽
    i = 0
    de_dict = {}
    while i < count:  # 解析文件头
        key = f.read(1)
        value = int.from_bytes(f.read(bit_width), byteorder='big')
        de_dict[key] = value
        i = i + 1
    for x in de_dict.keys():
        node_dict[x] = node(de_dict[x])
        nodes.append(node_dict[x])
    tree = build_tree(nodes)  # 重建哈夫曼树
    encode(False)  # 建立编码表
    for x in ec_dict.keys():  # 反向字典构建
        inverse_dict[ec_dict[x]] = x
    i = f.tell()
    data = b''
    while i < eof:  # 开始解压数据
        raw = int.from_bytes(f.read(1), byteorder='big')
        # print("raw:",raw)
        i = i + 1
        j = 8
        while j > 0:
            if (raw >> (j - 1)) & 1 == 1:
                data = data + b'1'
                raw = raw & (~(1 << (j - 1)))
            else:
                data = data + b'0'
                raw = raw & (~(1 << (j - 1)))
            if inverse_dict.get(data, 0) != 0:
                o.write(inverse_dict[data])
                o.flush()
                # print("decode",data,":",inverse_dict[data])
                data = b''
            j = j - 1
        tem = int(i / eof * 100)
        if tem > last:
            print("decode:", tem, '%')  # 输出解压进度
            last = tem
        raw = 0

    f.close()
    o.close()
    print("File decode successful.")


if __name__ == '__main__':

    # 数据初始化
    node_dict = {}  # 建立原始数据与编码节点的映射，便于稍后输出数据的编码
    count_dict = {}
    ec_dict = {}
    nodes = []
    inverse_dict = {}
    f = {}
    # C:\Users\xuxin\Documents\GitHub\compressDate\compressData\EquipStrenResource.ys
    # C:\Users\xuxin\Documents\GitHub\compressDate\compressData\testDate\
    # C:\Users\xuxin\Documents\GitHub\compressDate\compressData\testDate\EquipStrenResource.csv
    # C:\Users\xuxin\Documents\GitHub\compressDate\compressData\testDate\encodeDate\EquipStrenResource.ys
    # C:\Users\xuxin\Documents\GitHub\compressDate\compressData\testDate\initFile\
    select = input("1：压缩文件\t2：解压文件\t3:文件夹读取 \n请输入你要执行的操作：")
    encodePath = "C:\\Users\\xuxin\\Documents\\GitHub\\compressDate\\compressData\\testDate\\encodeDate\\"
    decodePath = "C:\\Users\\xuxin\\Documents\\GitHub\\compressDate\\compressData\\testDate\\decodeDate\\"
    encodeSuffix = ".ys"
    decodeSuffix = ".csv"
    if select == '1':
        encodefile(input("请输入要压缩的文件："), encodePath, encodeSuffix)
    else:
        if select == "3":
            p = input("请输入要压缩的文件夹：")
            encodefile(p, encodePath, encodeSuffix)

        else:
            decodefile(input("请输入要解压的文件："), decodePath, decodeSuffix)
