'''
Created on 2017 7 26

@author: Yali
'''
import sys
sys.path.append('../')
sys.path.append('../DataRelated')

import os
from data import PrepareData
from Predict import MyPredictDB
from MyPlot import PlotClass as myplt
from datetime import timedelta
import matplotlib.dates as mdates
import numpy as np

KnownDays = 90

def _fix_zero_data(AnArray):
    '''
    Some data is zero due to google error. 
    Here we fix it with previous number.
    '''
    leng = len(AnArray)
    if leng<3:
        return AnArray
    if AnArray[0]==0.0:
        AnArray[0] = (AnArray[1]+AnArray[2])/2.0
    for i in range(1,leng):
        if AnArray[i]==0.0:
            AnArray[i] = AnArray[i-1]
    return AnArray

def GetPicturesAndLabels(AllData,KnownDays=100,PredictDays=10,StepDays=5,UpThreshold=0.04):
    '''
    @param StepDays: The number of days jump for every image
    '''
    plt = myplt()
    convert = mdates.strpdate2num('%Y-%m-%d %H:%M:%S')
    '''
    '''
    # get all data
    
    #BigLists = ['AAPL']
    #print BigLists
    #AllData = MyPredictDB.GetAllDataFromAList(BigLists, '2017-07-21', 400)
    dir = './data/Stock/train'
    TotalSymbolNumber = len(AllData)
    CurrentSymbolNumber = 0
    for asymbol in AllData:
        print(asymbol+'\t'+str(CurrentSymbolNumber)+'/'+str(TotalSymbolNumber))
        TheData = AllData[asymbol]
        dates = []
        for anitem in TheData[0]:
            dates.append(convert(anitem.strftime('%Y-%m-%d %H:%M:%S')))
        dates.reverse()
        TheData[0].reverse()
        TheData[1].reverse()
        TheData[2].reverse()
        TheData[3].reverse()
        TheData[4].reverse()
        TheData[5].reverse()
        
        TheData[1] = _fix_zero_data(TheData[1])
        TheData[2] = _fix_zero_data(TheData[2])
        TheData[3] = _fix_zero_data(TheData[3])
        TheData[4] = _fix_zero_data(TheData[4])
        
        i = 0
        TotalNum = len(dates)
        f=open(os.path.join(dir,asymbol+'.txt'),'w')
        while i+KnownDays+PredictDays<TotalNum:
            KnownDates = dates[i:i+KnownDays]
            KnownOpen = TheData[1][i:i+KnownDays]
            KnownClose = TheData[2][i:i+KnownDays]
            KnownHigh = TheData[3][i:i+KnownDays]
            KnownLow = TheData[4][i:i+KnownDays]
            KnownVolume = TheData[5][i:i+KnownDays]
            savename = os.path.join(dir,asymbol+'_'+TheData[0][i+KnownDays-1].strftime('%Y-%m-%d')+'.png')
            plt.drawData(KnownDates, KnownOpen, KnownClose,KnownHigh,KnownLow,KnownVolume,True,savename)
            # here should be close. but to my case, i use open price
            lastClose = KnownOpen[-1]
            NextHigh = np.max(TheData[3][i+KnownDays:i+KnownDays+PredictDays])
            if lastClose==0.0:
                print ('Something is wrong')
                print (asymbol)
                print (KnownOpen)
                print (KnownDates)
                return
            increase = NextHigh/lastClose
            if increase>=1+UpThreshold:
                f.write(asymbol+'_'+TheData[0][i+KnownDays-1].strftime('%Y-%m-%d')+':::1:::'+str(increase)+'\n')
            else:
                f.write(asymbol+'_'+TheData[0][i+KnownDays-1].strftime('%Y-%m-%d')+':::-1:::'+str(increase)+'\n')
            i+=StepDays
        f.close()
        CurrentSymbolNumber+=1

def PrepareLearningData(StockFile):
    alist = PrepareData.GetBigCompany(StockFile)
    #alist = ['aapl','aap','orcl','f','azo']
    AllData = MyPredictDB.GetAllDataFromAList(alist, '2018-02-22', 600)
    GetPicturesAndLabels(AllData,KnownDays=KnownDays,PredictDays=10,StepDays=20,UpThreshold=0.05)

def PreparePredictData(StockFile,TheDate):
    '''
    @param TheDate: 2018-02-02
    '''
    ###
    #   delete the old predict files first
    ###
    thedir = './data/Stock/predict/'
    for root, subdir, files in os.walk(thedir):
        for afile in files:
            os.remove(os.path.join(thedir,afile))
            
    alist = PrepareData.GetBigCompany(StockFile)
    #alist = ['aapl']
    AllData = MyPredictDB.GetAllDataFromAList(alist, TheDate, KnownDays+1)
    plt = myplt()
    convert = mdates.strpdate2num('%Y-%m-%d %H:%M:%S')
    '''
    '''
    # get all data
    
    #BigLists = ['AAPL']
    #print BigLists
    #AllData = MyPredictDB.GetAllDataFromAList(BigLists, '2017-07-21', 400)
    TotalSymbolNumber = len(AllData)
    CurrentSymbolNumber = 0
    for asymbol in AllData:
        print(asymbol+'\t'+str(CurrentSymbolNumber)+'/'+str(TotalSymbolNumber))
        TheData = AllData[asymbol]
        dates = []
        for anitem in TheData[0]:
            dates.append(convert(anitem.strftime('%Y-%m-%d %H:%M:%S')))
        dates.reverse()
        TheData[0].reverse()
        TheData[1].reverse()
        TheData[2].reverse()
        TheData[3].reverse()
        TheData[4].reverse()
        TheData[5].reverse()
        
        TheData[1] = _fix_zero_data(TheData[1])
        TheData[2] = _fix_zero_data(TheData[2])
        TheData[3] = _fix_zero_data(TheData[3])
        TheData[4] = _fix_zero_data(TheData[4])
        
        i = 0
        TotalNum = len(dates)
        f=open(os.path.join(thedir,asymbol+'.txt'),'w')
        while i+KnownDays<TotalNum:
            KnownDates = dates[i:i+KnownDays]
            KnownOpen = TheData[1][i:i+KnownDays]
            KnownClose = TheData[2][i:i+KnownDays]
            KnownHigh = TheData[3][i:i+KnownDays]
            KnownLow = TheData[4][i:i+KnownDays]
            KnownVolume = TheData[5][i:i+KnownDays]
            savename = os.path.join(thedir,asymbol+'_'+TheData[0][i+KnownDays-1].strftime('%Y-%m-%d')+'.png')
            plt.drawData(KnownDates, KnownOpen, KnownClose,KnownHigh,KnownLow,KnownVolume,True,savename)
            lastClose = KnownClose[-1]
            
            if lastClose==0.0:
                print ('Something is wrong')
                print (asymbol)
                print (KnownClose)
                print (KnownDates)
                return
            f.write(asymbol+'_'+TheData[0][i+KnownDays-1].strftime('%Y-%m-%d')+':::1:::0.0\n')
            i+=1
        f.close()
        CurrentSymbolNumber+=1
    
if __name__=='__main__':
    PrepareLearningData('../data/BigCompany.txt')
    #PreparePredictData('../data/BigCompany.txt','2018-02-09')