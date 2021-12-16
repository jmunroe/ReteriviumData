
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from xml.dom import minidom
import tarfile
from tqdm import tqdm
import numpy as np
from decimal import  Decimal
import  Initialize_Retrivium_Matrix
import Calculate_distance

def DataGathering(df_sampledata):
    filesize=len(df_sampledata)
    # initialize the matrix
    Ret_Mat=Initialize_Retrivium_Matrix.Initialize_Retrivium_Matrix(df_sampledata)
    # calculate the distance of cartesian positions
    Ret_MainMat=Calculate_distance.Calculate_distance(df_sampledata, Ret_Mat) 
    
    return Ret_MainMat