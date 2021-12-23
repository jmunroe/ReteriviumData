#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from xml.dom import minidom
import tarfile
from tqdm import tqdm
import numpy as np

import glob
import itertools
import os

from decimal import  Decimal
from numpy import asarray
from numpy import savez_compressed
from numpy import load
import multiprocessing


def GetFileList():
    # Get list of Tar.gz files
    TarFilenames=[]
    # All files ending with .gz
    TarFilenames.append(glob.glob("./TarFiles/*.gz")) 
    TarFilenames = list(itertools.chain.from_iterable(TarFilenames))

    if not os.path.exists('./cmlFiles'):
        os.mkdir('./cmlFiles')
        
    TarFilenamessize=len(TarFilenames)
    for i in range(TarFilenamessize):
        my_tar = tarfile.open(TarFilenames[i])
        my_tar.extractall('./cmlFiles') # specify which folder to extract to
        my_tar.close()      

    Filenames=[]
    # All files ending with .cml
    Filenames.append(glob.glob("./cmlFiles/*.cml")) 
    Filenames = list(itertools.chain.from_iterable(Filenames))

    return Filenames


def delete_cmls():
    '''
    This function remove all the extracted cml files to save resources
    '''
    files = glob.glob('./cmlFiles/*.cml')
    for f in files:
        os.remove(f)


# create a dataframe of AtomTypes
def CreateAtomTypedf(getatomstype, smile, energy, filename):
    lst1=[]
    lst2=[]
    lst3=[]
    lst4=[]
    atom_df=pd.DataFrame()

    for i in range(len(getatomstype)):
        if ('id' in (getatomstype[i].attributes)):
            lst1.append(getatomstype[i].attributes['id'].value)
            lst3.append(getatomstype[i].attributes['type'].value)
            lst4.append(getatomstype[i].attributes['valence'].value)

    df_atomtype=pd.DataFrame() 
    df_atomtype['id']=lst1
    df_atomtype['type']=lst3
    df_atomtype['valence']=lst4       
    df_atomtype['smile']=smile    
    df_atomtype['energy']= energy
    df_atomtype['file_id']=filename


    return df_atomtype   


# This function help to extract cartesian position from cml files
def GetCartesian(mydoc, filename):

    atoms=mydoc.getElementsByTagName('molecule')
    lst1=[]
    lst2=[]
    lst3=[]
    lst4=[]
    lst5=[]
    lst6=[]
    lst7=[]
    checklst=[]
    df_Cart=pd.DataFrame()
    Main_Df=pd.DataFrame()
    flag=True

    for k in range(len(atoms)):

        x=atoms[k].attributes['id'].value
        if(x=='final') & (flag):

            atom=atoms[k].getElementsByTagName('atom')
            for j in range(len(atom)):
                x=atom[j].attributes['id'].value

                if (x not in checklst):
                    checklst.append(x)

                    lst1.append(atom[j].attributes['id'].value)
                    lst2.append(atom[j].attributes['elementType'].value)
                    lst3.append(atom[j].attributes['x3'].value)
                    lst4.append(atom[j].attributes['y3'].value)
                    lst5.append(atom[j].attributes['z3'].value)
                    lst6.append(filename)
                    lst7.append(filename[38:49])

            flag=False          
            df_cartesian=pd.DataFrame()
            df_cartesian['id']=lst1
            df_cartesian['elementType']=lst2
            df_cartesian['x3']=lst3
            df_cartesian['y3']=lst4
            df_cartesian['z3']=lst5
            df_cartesian['file_id']=lst6
            df_cartesian['Formula']=lst7
            df_Cart=pd.concat([Main_Df, df_cartesian]) 

            return df_Cart   


# Function to get Atom types
def GetAtomTypes(mydoc):
    getatomstype=None
    text=None
    smile=None
    flag=True
    atoms=mydoc.getElementsByTagName('property')
    for i in range(len(atoms)):
        x=atoms[i].attributes['dictRef'].value
        if x=='retrievium:atomTypes':
            getatomstype=mydoc.getElementsByTagName('atomType')

        if (x=='retrievium:inputSMILES') & (flag):
            text=atoms[i].getElementsByTagName('scalar')
            for i in range(1):
                smile=text[0].firstChild.data
                flag=False

        if (x=='retrievium:Energy_Total'):
            text=atoms[i].getElementsByTagName('scalar')
            for i in range(1):
                energy=text[0].firstChild.data
                       

    return getatomstype, smile, energy 


def extract(filename):
    
    mydoc=minidom.parse(filename) 

    df_Cart=GetCartesian(mydoc, filename)   

    getatomstype,smile, energy= GetAtomTypes(mydoc)  
    df_atomtypes=CreateAtomTypedf(getatomstype, smile, energy, filename) 
    
    return df_Cart, df_atomtypes


# Initialize the Reterivium Matrix
def Initialize_Retrivium_Matrix(df_file):
    filesize=len(df_file)
    Mat_Init=np.zeros((filesize+4,filesize+4))
   
    rowcounter=0
    colcounter=0
    for row in range(filesize+4):
        if (row>3):
            Mat_Init[row][0]= df_file.iloc[rowcounter]['id']
            Mat_Init[row][1]= df_file.iloc[rowcounter]['elementType']
            Mat_Init[row][2]= df_file.iloc[rowcounter]['type']
            Mat_Init[row][3]= df_file.iloc[rowcounter]['valence']
            rowcounter+=1
    for col in range(filesize+4):
        if (col>3):
            Mat_Init[0][col]= df_file.iloc[colcounter]['id']
            Mat_Init[1][col]= df_file.iloc[colcounter]['elementType']
            Mat_Init[2][col]= df_file.iloc[colcounter]['type']
            Mat_Init[3][col]= df_file.iloc[colcounter]['valence']
            colcounter+=1

    return Mat_Init  


# Calculate the distance for the retrivium Matrix
def Calculate_distance(df_file, Ret_Mat):
    filesize=len(df_file)
    for row in range(4, filesize+4):
        id_temp=Ret_Mat[row][0]
        df_temp=df_file[df_file['id']==id_temp]

        distance=0

        # print('*************************')
        for col in range (4, filesize+4):
            id_col=Ret_Mat[0][col]
            df_col=df_file[df_file['id']==id_col]
            if id_col!=id_temp:
                distance=np.sqrt((df_col.iloc[0]['x3']-df_temp.iloc[0]['x3'])**2 + (df_col.iloc[0]['y3']-df_temp.iloc[0]['y3'])**2 + (df_col.iloc[0]['x3']-df_temp.iloc[0]['z3'])**2)
            else:
                distance=0  

            Ret_Mat[row][col]= distance
    return Ret_Mat 


def DataGathering(filename):
    df_final = pd.read_csv('Final_Ret.csv')
    
    df_sampledata=df_final[df_final['file_id']==filename]
    df_sampledata.reset_index(inplace=True)
    
    filesize=len(df_sampledata)
    
    # initialize the matrix
    Ret_Mat=Initialize_Retrivium_Matrix(df_sampledata)
    # calculate the distance of cartesian positions
    Ret_MainMat=Calculate_distance(df_sampledata, Ret_Mat) 
    
    return Ret_MainMat


def Collect_Final_Matrix(df_final):
    filesize=len(df_final.file_id.unique())
    files=df_final['file_id'].unique().tolist()
    
    sample_size=len(df_final[df_final['file_id']==files[0]])

    with multiprocessing.Pool() as p:
        results = list(tqdm( p.imap(DataGathering, files), total=filesize))
        
    Main_Array = np.stack(results)

    return Main_Array


def energy_label_generation(df_final):

    energy_files=df_final.file_id.unique()
    energy_label=df_final[df_final.file_id.isin(energy_files)]
    energy_label=energy_label[['file_id','energy']]
    df_energy=energy_label.drop_duplicates(subset='file_id', keep='first')
    df_energy=df_energy['energy']
    # Magnify the difference in energy values
    df_energy_magnify=(df_energy-min(df_energy))*2625.5
    energy_target=df_energy_magnify.to_numpy()

    return energy_target, df_energy


def generate_dzfiles(Matrix_overall, df_final):
    data_all = Matrix_overall
    # save to npz file format
    savez_compressed('data.npz', data_all)
    energy_label, df_energy=energy_label_generation(df_final)
    savez_compressed('label_data.npz', energy_label)
    savez_compressed('energydf_data.npz', df_energy)
    # extract the data samples
    samples_data = load('data.npz')
    data=samples_data['arr_0']

    # extract the labels
    engdata = load('label_data.npz')
    label=engdata['arr_0']

    return data,label


# Main func to extract all necessary items from cml files and then saving in a dataframe
def build_dataframe(Formula):
    # get list of cml files and extract it in cmlfiles folder
    Filenames=GetFileList()
    Filenames = [filename for filename in Filenames if Formula in filename]
    dframes=[]
    dfcarts=[]
    
    with multiprocessing.Pool() as p:
        r = list(tqdm( p.imap(extract, Filenames), total=len(Filenames)))
                
    for df_cart, df_atomtypes in r:
        dfcarts.append(df_cart)
        dframes.append(df_atomtypes)
    
    df_cartesian=pd.concat(dfcarts)
    df_atomt=pd.concat(dframes)
    df_atomt.drop_duplicates(inplace=True)
    
    
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
    
    return  df_final


def main():
    df_final = build_dataframe('C9H13NO')

    Matrix_overall= Collect_Final_Matrix(df_final)

    data, label = generate_dzfiles(Matrix_overall, df_final) 

    delete_cmls() 


if __name__ == "__main__":
    main()
