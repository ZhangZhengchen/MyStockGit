'''
Created on 2017 7 26

@author: Yali
'''
from data import PrepareData
from Predict import MyPredictDB
from MyPlot import PlotClass as myplt
from datetime import timedelta
import matplotlib.dates as mdates
import numpy as np

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
    TotalSymbolNumber = len(AllData)
    CurrentSymbolNumber = 0
    for asymbol in AllData:
        print asymbol+'\t'+str(CurrentSymbolNumber)+'/'+str(TotalSymbolNumber)
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
        i = 0
        TotalNum = len(dates)
        f=open('./data/'+asymbol+'.txt','w')
        while i+KnownDays+PredictDays<TotalNum:
            KnownDates = dates[i:i+KnownDays]
            KnownOpen = TheData[1][i:i+KnownDays]
            KnownClose = TheData[2][i:i+KnownDays]
            KnownHigh = TheData[3][i:i+KnownDays]
            KnownLow = TheData[4][i:i+KnownDays]
            KnownVolume = TheData[5][i:i+KnownDays]
            savename = './data/'+asymbol+'_'+TheData[0][i+KnownDays-1].strftime('%Y-%m-%d')+'.png'
            plt.drawData(KnownDates, KnownOpen, KnownClose,KnownHigh,KnownLow,KnownVolume,True,savename)
            lastClose = KnownClose[-1]
            NextHigh = np.max(TheData[3][i+KnownDays:i+KnownDays+PredictDays])
            if lastClose==0.0:
                print 'Something is wrong'
                print asymbol
                print KnownClose
                print KnownDates
                return
            increase = NextHigh/lastClose
            if increase>=1+UpThreshold:
                f.write(asymbol+'_'+TheData[0][i+KnownDays-1].strftime('%Y-%m-%d')+':::1:::'+str(increase)+'\n')
            else:
                f.write(asymbol+'_'+TheData[0][i+KnownDays-1].strftime('%Y-%m-%d')+':::0:::'+str(increase)+'\n')
            i+=StepDays
        f.close()
        CurrentSymbolNumber+=1

def PrepareLearningData(StockFile):
    alist = PrepareData.GetBigCompany(StockFile)
    AllData = MyPredictDB.GetAllDataFromAList(alist, '2017-07-03', 500)
    GetPicturesAndLabels(AllData,KnownDays=100,PredictDays=10,StepDays=5,UpThreshold=0.04)

if __name__=='__main__':
    PrepareLearningData('../data/XLK.txt')