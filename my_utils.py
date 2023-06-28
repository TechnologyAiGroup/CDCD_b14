import copy
import json

from PIL import Image
import numpy as np
import os
import argparse
import random


def draw(matrix, i):
    m = copy.deepcopy(matrix)
    m[i + 1:][:] = 127
    m = m.astype(np.uint8)
    img = Image.fromarray(m).convert("L")
    # img.show()
    return img


def matirx2bmp(matrix, saveto, namepre):
    """
    :param matrix: the whole test output
    :return:
    """

    m = len(matrix)
    n = len(matrix[0])
    matrix = matrix * 255
    error = 0  # the number of failing test pattern
    isF = 0
    for i in range(m):
        for j in range(n):
            if matrix[i][j] == 0:
                continue
            elif matrix[i][j] == 255:
                isF = 1
                break
            else:
                print("error")
                exit()
        if (i != m - 1 and isF == 1) or (i == m - 1):
            if isF == 1:
                error += 1
            img = draw(matrix, i)
            # save
            # if not os.path.exists(saveto):
            #     os.makedirs(saveto)
            if i == m - 1 and isF == 0:
                img.save(saveto + f"/{namepre}all.bmp")
            else:
                img.save(saveto + "/" +namepre+ str(error) + ".bmp")
            isF = 0
        elif i == m - 1:
            if isF == 1:
                error += 1
    return error


def generateBMP(fileid2content, chip, fault):
    # get .bmp pic from matrixs
    for fileid, content in fileid2content.items():
        # saveto = "./pic/" + chip + "/" + fault + "/" + str(fileid) + "_resp" + "/"
        saveto = f"./{chip}/pic/{fault}/{str(fileid)}_resp"
        if not os.path.exists(saveto):
            os.makedirs(saveto)
        namepre = f"{fault}-{str(fileid)}_resp_"
        matirx2bmp(content, saveto, namepre)
        # print("---{}.resp done---".format(fileid))


def getPO(chip):
    # get POs of circuits from .bench file
    bench = "./data/" + chip + ".bench"
    with open(bench, "r") as f:
        lines = f.readlines()
    f.close()
    outputs = 0
    po2id = {}
    for line in lines:
        if "OUTPUT" in line:
            po2id[line.split("(")[1].split(")")[0]] = outputs
            outputs += 1
        else:
            continue
    return po2id


def getRESP(chip, fault):
    # get test outputs from test patterns
    path = "./" + chip + "/source/" + fault + "/fat-results/responses/" + chip + "/"
    checkfailpath = "./"+chip+"/source/"+fault+"/diagnosis_report/"
    fileid2content = {}
    checkline = {}
    for file_name in os.listdir(path):
        fileid = int(file_name.split(".")[0])
        if not os.path.exists(checkfailpath+f"{fileid}_fail/"):
            print("drop {}".format(fileid))
            continue
        isDrop = 0
        with open(path + "/" + file_name, "r") as file:
            lines = file.readlines()
        isBEGIN = 0
        outputs_expect = []
        outputs = []
        for line in lines:
            if "Primary outputs" in line:
                # POs
                pos = line.split(":")[-1].split(" ")
                isBEGIN = 1
            elif isBEGIN == 1 and ":" in line:
                # outputs
                _, pis, _, output_expect, output, _ = line.split(":")[-1].split(" ")
                try:
                    outputs_expect.append([int(c) for c in output_expect])
                    outputs.append([int(c) for c in output])
                except Exception as e:
                    isDrop = 1
                    break
            else:
                continue
        if isDrop == 1:
            continue
        res = np.array(outputs_expect) ^ np.array(outputs)
        cl = []
        for i in range(len(res)):
            for j in range(len(res[0])):
                if res[i][j] > 0:
                    cl.append(i)
                    break
                else:
                    continue
        if not fileid in fileid2content:
            fileid2content[fileid] = res
            checkline[fileid] = cl
        else:
            print("Duplicate results {}".format(fileid))
    return fileid2content, checkline


def splitDataset(circuit, fault_types):
    # 按比例划分数据集
    allchips = []
    for fault in fault_types:
        root = os.path.join("pic/", circuit, fault)
        if not os.path.exists(root):
            continue
        perchip =os.listdir(root)
        for chip in perchip:
            allchips.append(os.path.join(root, chip))
    random.seed(10)
    random.shuffle(allchips)
    index = int(0.8*len(allchips))
    trainset = allchips[:index]
    testset = allchips[index:]

    # print(len(trainset))
    # print(len(testset))
    # print(testset)
    return trainset, testset

# chip = "test"
# matirx2bmp(matrix, saveto="./pic/" + chip + "/" + "2/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="get label ma")
    parser.add_argument("-c", type=str, default=["ctrl"], nargs="+", help="circuits/chips")
    parser.add_argument("--type", type=str, default=["and", "or", "fe", "dom", "ssl", "msl"], nargs="+", help="fault types")
    args = parser.parse_args()
    print(args)

    chips = args.c
    faults = args.type
    # faults = ["and", "or", "fe", "dom", "ssl", "msl"]
    for chip in chips:
        for fault in faults:
            # if not os.path.exists(f"../{chip}/{fault}/diagnosis_report/"):
            #     os.makedirs(f"../{chip}/{fault}/diagnosis_report")
            #     cmd = f"unzip ../{chip}/diagnosis_report_{fault}.zip -d ../{chip}/{fault}/diagnosis_report/"
            #     os.system(cmd)
            # r存储矩阵
            # checkline储存需要切分的行数
            print("runing...")
            r, checkline = getRESP(chip=chip, fault=fault)
            # print(r)
            # print("saving...")
            # with open("./data/" + "{}.json".format(chip), "w") as f:
            #     json.dump(checkline, f)
            # f.close()
            print("generating...")
            generateBMP(fileid2content=r, chip=chip, fault=fault)
            print("------------------{}----------------------".format(fault))
        print("*****************{}*****************".format(chip))
