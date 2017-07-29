'''
Created on 2017 7 26

@author: Yali
'''
from data import PrepareData
from Predict import MyPredictDB

def GetWeeklyData(KnownWeeks=3,PredictWeek=1,UpThreshold=0.04,Sectors=['XLK']):
    '''
    '''
    # get all data
    #BigLists = []
    #for anitem in Sectors:
    #    alist = PrepareData.GetBigCompany("../data/"+anitem+".txt")
    #    BigLists+=alist
    BigLists = ['AAPL']
    #print BigLists
    AllData = MyPredictDB.GetAllDataFromAList(BigLists, '2017-07-21', 400)
    for asymbol in AllData:
        TheData = AllData[asymbol]
        
    

if __name__=='__main__':
    GetWeeklyData()