'''
Created on 2016 11 13

@author: Yali
'''
from Predict import MyPredictDB
import datetime
import random
import math
import numpy as np
from datetime import timedelta
#Get a date, 
#Get all data, 
#Get Predict, 
#Set situation, 
#Get Result

def BuyStockAtADay(initMoney,theDate):
    AllData = {}
    adate = datetime.datetime.strptime(theDate,'%Y-%m-%d')
    while True:
        AllData = MyPredictDB.GetAllData(theDate)
        if len(AllData.items())>0:
            break
        else:
            adate += timedelta(days=1)
            theDate = datetime.datetime.strftime(adate,'%Y-%m-%d')
    IsUpList = []
    for anitem in AllData:
        data = AllData[anitem]
        isup = MyPredictDB.IsUpTrend(data)
        if isup:
            IsUpList.append(anitem)
    if len(IsUpList)==0:
        return [0,0,0,initMoney]
    #buy 
    NumberHold = 0
    RemainMoney = initMoney-10
    
    theindex = random.randint(0,len(IsUpList)-1)
    print IsUpList
    print theindex
    TheStock = IsUpList[theindex]
    BuyPrice = AllData[TheStock][2][0]
    if BuyPrice>0.0:
        NumberHold = math.floor(RemainMoney/BuyPrice)
        RemainMoney -= NumberHold*BuyPrice
        return [TheStock,NumberHold,BuyPrice,RemainMoney,adate]
    else:
        print 'error.'
        print TheStock
        return [0,0,0,0,None]



def SellAStock(CurrentHold,SellPrice):
    SellMoney = CurrentHold[1]*SellPrice
    return CurrentHold[3]+SellMoney-10

def RunAStrategy(initMoney,startDate,endDate):
    '''
    startDate: 2016-01-01, string
    '''
    #Get data of that date
    theStartDate = datetime.datetime.strptime(startDate,'%Y-%m-%d')
    theEndDate = datetime.datetime.strptime(endDate,'%Y-%m-%d')
    currentDate = theStartDate
    isBuy = False
    RemainMoney = initMoney
    while currentDate<=theEndDate:
        if not isBuy:
            CurrentHold = BuyStockAtADay(RemainMoney, datetime.datetime.strftime(currentDate,'%Y-%m-%d'))
            if CurrentHold[1]>0:
                isBuy = True
                currentDate = CurrentHold[4]
            print CurrentHold
            print currentDate
            if currentDate>=theEndDate:
                break
        else:
            while True:
                theSMA = MyPredictDB.GetSMAAtADate(CurrentHold[0],10,datetime.datetime.strftime(currentDate,'%Y-%m-%d'))
                print theSMA
                print currentDate
                if theSMA[0]==-1:
                    currentDate += timedelta(days=1)
                else:
                    break
            if currentDate>=theEndDate:
                break
            if theSMA[0]==float('inf'):
                print CurrentHold
                return
            if theSMA[0]>theSMA[1]:
                RemainMoney = SellAStock(CurrentHold,theSMA[1])
                isBuy = False
        currentDate = currentDate + timedelta(days=1)
    
    print CurrentHold
    theSMA = MyPredictDB.GetSMAAtADate(CurrentHold[0],10,datetime.datetime.strftime(theEndDate,'%Y-%m-%d'))
    print CurrentHold[1]*theSMA[1]+CurrentHold[3]
    
if __name__=='__main__':
    RunAStrategy(3500,'2016-04-02','2016-07-01')