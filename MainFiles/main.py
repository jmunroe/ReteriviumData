import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from xml.dom import minidom
import tarfile
from tqdm import tqdm
import numpy as np
import warnings
warnings.filterwarnings("ignore")

import glob
import itertools
import os
import CreateAtomTypedf
import GetCartesian
import GetAtomTypes
import Collect_Final_Matrix
import generate_dzfiles
import GetFileList
import delete_cmls





# Main func to extract all necessary items from cml files and then saving in a dataframe
def main(Formula):
    # get list of cml files and extract it in cmlfiles folder
    Filenames=GetFileList.GetFileList()
    filesize=len(Filenames)
    
    dframes=[]
    dfcarts=[]
    
    for i in tqdm(range(filesize)):
        mydoc=minidom.parse(Filenames[i]) 

        df_Cart=GetCartesian.GetCartesian(mydoc, Filenames[i], Formula)   
        if df_Cart is not None: 
            dfcarts.append(df_Cart)
            df_cartesian=pd.concat(dfcarts)

        getatomstype,smile, energy= GetAtomTypes.GetAtomTypes(mydoc)  
        df_atomtypes=CreateAtomTypedf.CreateAtomTypedf(getatomstype,smile,energy, Filenames[i],Formula )
        if df_atomtypes is not None:
           dframes.append(df_atomtypes)
           df_atomt=pd.concat(dframes)
           df_atomt.drop_duplicates(inplace=True)
    
    return  df_cartesian, df_atomt    


if __name__ == "__main__":
     
    df_cartesian, df_atomt= main('C9H13NO')
    # df_cartesian, df_atomt= main()
    df_atomt.sort_values(by=['file_id','id'], inplace=True)
    df_cartesian.sort_values(by=['file_id','id'], inplace=True)
    df_final=df_cartesian.merge(df_atomt, on=['file_id','id'])
    df_final=df_final.astype({'type': int, 'valence':int, 'energy':float})
    # replace element type with atomic number
    replace_atoms = {"elementType": {"C": 6, "N": 7, "O": 8, "H": 1}}  
    df_final=df_final.replace(replace_atoms)
    df_final=df_final.astype({'x3': np.float64, 'y3':np.float64, 'z3':np.float64})
    for i in range(len(df_final)):
       df_final['id'][i]=int(df_final['id'][i][1:])
    df_final.to_csv('Final_Ret.csv')

    Matrix_overall= Collect_Final_Matrix.Collect_Final_Matrix(df_final)
    data, label=generate_dzfiles.generate_dzfiles(Matrix_overall,df_final) 

    delete_cmls.delete_cmls()

