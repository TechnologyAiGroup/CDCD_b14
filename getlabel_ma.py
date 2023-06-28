"""
x.resp <==> x_fail
x.bmp <==> x-1.diag
TEST PATH:
./data/ctrl/ssl/1.resp
./data/ctrl/ctrl.bench
./pic/ctrl/1_resp/1.bmp
./pic/ctrl/1_resp/all.bmp
./report/ctrl/ssl/diagnosis_report/1_fail/0.diag
./report/ctrl/ssl/diagnosis_report/1_fail/all.diag
LABEL:
resp/fail   pic     label
x           y       z
"""
import os
import re
import argparse



def makelabel(chip, fault):
    # root = "./report/" + chip + "/" + fault + "/diagnosis_report/"
    # picroot = "./pic/" + chip + "/" + fault + "/"
    picroot = "./" + chip + "/pic/" + fault + "/"
    root = "./" + chip + "/source/" + fault + "/diagnosis_report/"

    for dictory in os.listdir(root):
        id_resp_fail = int(dictory.split("_")[0])

        # 获取golden candidates
        with open(root + dictory + "/all.diag", "r") as f:
            lines = f.readlines()
        f.close()
        golden = analysis(lines=lines)
        if not golden:
            print("golden has no fault! in {}".format(dictory))
            cmd = f"rm -r ./{chip}/pic/{fault}/{id_resp_fail}_resp"
            os.system(cmd)
            continue
            # exit()

        # 初始化candidates和labels，用于存储每个diag文件的结果和对应图片的标签
        candidates = [-1] * (len(os.listdir(root + dictory)) - 1)
        labels = [-1] * (len(os.listdir(root + dictory)) - 1)
        haveall = 0
        if os.path.exists(os.path.join(picroot + "{}_resp".format(id_resp_fail), f"{fault}-{id_resp_fail}_resp_all.bmp")):
            haveall = 1
            labels.append(1)  # all.bmp

        # 分析非all.diag的diag文件
        for file_name in os.listdir(root + dictory):
            if file_name == "all.diag":
                continue
            else:
                id_diag = int(file_name.split(".")[0])

                # 获取intermediate candidates
                with open(root + dictory + "/" + file_name, "r") as f:
                    lines = f.readlines()
                f.close()
                intermediate = analysis(lines=lines)

                # 存储candidates和labels
                if candidates[id_diag] == -1:
                    candidates[id_diag] = intermediate
                else:
                    print("error1")
                    exit()
                if labels[id_diag] == -1:
                    if len(intermediate) == 0:
                        # 定义之外的情况
                        print(os.path.join(root+dictory, file_name))
                        labels[id_diag] = 0
                    else:
                        labels[id_diag] = get_label(cur=intermediate, golden=golden)
                else:
                    print("error2")
                    exit()

        # 打开pic文件夹存储对应标签
        try:
            with open(picroot + "{}_resp/labels_ma.txt".format(id_resp_fail), "w") as f:
                f.truncate(0)
                for i in range(len(labels)):
                    name = "{}-{}_resp_{}.bmp".format(fault, id_resp_fail, i + 1)
                    if haveall and i == len(labels)-1:
                        name = name.split("_")[0] + "_resp_all.bmp"
                    f.write("{} {}\n".format(name, str(labels[i])))
            f.close()
        except Exception as e:
            print("error in {}_resp".format(id_resp_fail))
            print(e)
        # print("saving labels in {}_resp".format(id_resp_fail))


def get_label(cur, golden):
    n_and = 0
    n_cur = len(cur)
    n_golden = len(golden)
    if n_cur<=n_golden:
        for item in cur:
            if item in golden:
                n_and+=1
    else:
        for item in golden:
            if item in cur:
                n_and+=1
    return (n_and*n_and)/(n_cur*n_golden)


def analysis(lines):
    # 分析diag文件
    matchscore = 0
    res = []
    for line in lines:
        if re.search("match", line):
            score = float(line.split("=")[1].split("%")[0])
            if score >= matchscore:
                matchscore = score
    startans = 0
    for line in lines:
        if re.search("match", line):
            score = float(line.split("=")[1].split("%")[0])
            if score == matchscore:
                startans = 1
            continue
        if re.search("------", line) and startans == 1:
            startans = 0
            continue
        if startans == 1:
            tp = line.split("   ")
            if len(tp) == 4 and tp[2].split("/")[0] not in res:
                res.append(tp[2].split("/")[0])
            else:
                continue
    return res

# chips = ["ctrl", "x1"]
# faults = ["and", "or", "fe", "dom", "ssl", "msl"]
# for chip in chips:
#     for fault in faults:
#         makelabel(chip=chip, fault=fault)
#         print("------------------{}-----------------".format(fault))
#     print("-----------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="get label mb")
    parser.add_argument("-c", type=str, default=["ctrl"], nargs="+", help="circuits/chips")
    parser.add_argument("--type", type=str, default=["and", "or", "fe", "dom", "ssl", "msl"], nargs="+", help="fault types")
    args = parser.parse_args()
    print(args)

    chips = args.c
    faults = args.type
    for chip in chips:
        for fault in faults:
            # if not os.path.exists(f"../{chip}/{fault}/diagnosis_report/"):
            #     os.makedirs(f"../{chip}/{fault}/diagnosis_report")
            #     cmd = f"unzip ../{chip}/diagnosis_report_{fault}.zip -d ../{chip}/{fault}/diagnosis_report/"
            #     os.system(cmd)
            makelabel(chip=chip, fault=fault)
            print("------------------{}-----------------".format(fault))
        print(f"--------------{chip} done---------------")