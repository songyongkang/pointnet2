# -*- coding: utf-8 -*-
# @Author  : LG

from Data.Dataset import indoor3d_Dataset
from torch.utils.data import DataLoader
from Model.Pointnet2 import PointnetMSG
from torch import nn
import torch
from torch.nn import DataParallel
from Utils.visdom_op import setup_visdom, visdom_line
import numpy as np
import pandas

def cal_iou(pred, label):
    iou_dic = {}
    classes = np.unique(label)
    for classe in classes:
        I = np.sum(np.logical_and(pred == classe, label == classe))
        U = np.sum(np.logical_or(pred == classe, label == classe))
        if U ==0:
            IOU = 1
        else:
            IOU = I / float(U)
        iou_dic[classe] = IOU
    return iou_dic


def Eval(model, loader):
    eval_dic = {}
    for step, (xyzs, points, labels, file_names) in enumerate(loader):
        xyzs, points = xyzs.transpose(1, 2), points.transpose(1, 2)

        preds = model(xyz=xyzs, points=points)
        preds = preds.max(-1)[1].cpu().numpy()
        labels = labels.numpy()

        for pred, label, file_name in zip(preds, labels, file_names):
            # print('pred:',pred)
            # print('label:',label)
            eval_dic[file_name] = cal_iou(pred, label)

        if step ==2:
            break

    df = pandas.DataFrame(eval_dic)
    print(df)

    df.to_csv('eval_result.csv')
    ap = np.array(df.mean(axis = 1))
    map = np.mean(ap)
    return map, ap


if __name__ == '__main__':

    eval_data = indoor3d_Dataset(is_train=False, data_root='Data', test_area=5)
    eval_loader = DataLoader(eval_data, batch_size=2, shuffle=True, num_workers=4)

    model = PointnetMSG(xyz_channel=3, data_channel=4, num_classes=6)
    model = model.double().to('cuda')
    model = DataParallel(model,device_ids=[0,1])
    map, ap = Eval(model, eval_loader)
    print(map)
    print(ap)
