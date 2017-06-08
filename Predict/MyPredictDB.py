'''
Created on 2016 11 6

@author: Yali
'''
import MySQLdb as mdb
import numpy as np
from DataRelated import Condition, Database
import operator
import datetime
from datetime import timedelta
import time

con = mdb.connect('localhost', 'root', '', 'nasdaq')
TheVolume = 100000
def GetDataFromATable(thesql):
    #read recent data 15 days
    with con:
        cur = con.cursor()
        try:
            cur.execute(thesql)
        except:
            return [[],[],[],[],[],[]]
        row = cur.fetchall()
        if len(row)==0:
            return [[],[],[],[],[],[]]
        Dates = []
        OpenPrices = []
        ClosePrices = []
        HighPrices = []
        LowPrices = []
        Volumes = []
        for i in range(len(row)):
            theName = row[i]
            try:
                if theName[5]==0:
                    continue
                Dates.append(theName[0])
                OpenPrices.append(theName[1])
                ClosePrices.append(theName[2])
                HighPrices.append(theName[3])
                LowPrices.append(theName[4])
                Volumes.append(theName[5])
            except:
                print 'error'
        return [Dates,OpenPrices,ClosePrices,HighPrices,LowPrices,Volumes]

def GetSMAAtADate(theStock,dayNumber,theDate):
    data = GetDataFromATable('select * from '+theStock+'daily where pricedate<=\''+theDate+'\' order by pricedate desc limit '+str(dayNumber))
    if data[0][0]!=datetime.datetime.strptime(theDate,'%Y-%m-%d').date():
        return [-1,-1]      
    if len(data[0])<dayNumber:
        return [float('inf'),float('inf')]
    else:
        return [np.mean(data[2]),data[2][0]]
    
#find up trend
def IsUpTrend(data):
    if len(data)==0:
        return False
    #Dates = list(reversed(data[0]))
    #OpenPrices = list(reversed(data[1]))
    #ClosePrices = list(reversed(data[2]))
    #HighPrices = list(reversed(data[3]))
    #LowPrices = list(reversed(data[4]))
    #Volumes = list(reversed(data[5]))
    
    Dates = data[0]
    OpenPrices = data[1]
    ClosePrices = data[2]
    HighPrices = data[3]
    LowPrices = data[4]
    Volumes = data[5]
    
    DayRange = 10
    SMARange = 100
    if len(Dates)==len(OpenPrices)==len(ClosePrices)==len(HighPrices)==len(LowPrices)==len(Volumes):
        # volume
        if np.mean(Volumes)<TheVolume:
            return False
        if len(Dates)<SMARange+DayRange+1:
            return False
        SMALong = []
        for i in range(DayRange):
            SMALong.append(np.mean(ClosePrices[i:SMARange+i]))
        
        for i in range(DayRange/3):
            if SMALong[i]>ClosePrices[i]:
                return False
        for i in range(DayRange/3+1,len(SMALong)):
            if SMALong[i]<ClosePrices[i]:
                return False
        return True
        '''if ClosePrices[0]<np.mean(ClosePrices[0:11]):
            return False
        if HighPrices[3]>max(HighPrices[4:4+DayRange-1]) \
        and LowPrices[3]>max(LowPrices[4:4+DayRange-1])\
        and HighPrices[0]>HighPrices[1]:
            return True
        else:
            return False'''
       

def GetUpTrendStocks(StartDate):
    AllDic = {}
    with con:
        cur = con.cursor()
        cur.execute("SELECT Symbol FROM companylist")
    
        row = cur.fetchall()
        for i in range(len(row)):
            theName = row[i][0]
            if theName.find('^')>0:
                continue 
            #print theName
            thesql = 'select * from '+theName+'daily where pricedate<=\''+StartDate+'\' order by pricedate desc limit 250'
            data = GetDataFromATable(thesql)
            if len(data[0])==0:
                continue
            isUp = IsUpTrend(data)
            if isUp:
                AllDic[theName] = np.mean(data[-1])
    
    sorted_x = sorted(AllDic.items(), key=operator.itemgetter(1))
    for anitem in sorted_x:
        print anitem

def GetAllData(theDate,datanumber=25):
    '''
    @param theDate: string format 2015-01-01
    @return: A dictionary. The Symbols are keys. Values are arrays. [price date,open,close,high,low,volume] order by date desc
    '''
    AllDic = {}
    with con:
        cur = con.cursor()
        cur.execute("SELECT Symbol FROM companylist")
    
        row = cur.fetchall()
        for i in range(len(row)):
            theName = row[i][0]
            if theName.find('^')>0:
                continue 
            #print theName
            data = []
            thesql = 'select * from '+theName+'daily where pricedate<=\''+theDate+'\' order by pricedate desc limit '+str(datanumber)
            data = GetDataFromATable(thesql)
            if len(data[0])==0:
                continue
            if data[0][0]!=datetime.datetime.strptime(theDate,'%Y-%m-%d').date():
                continue
            AllDic[theName] = data
    return AllDic

def GetPotentialStocks(StartDate,DateNumber=40):
    '''
    StartDate: 2016-01-01
    '''
    # Get all data
    AllDic = {}
    with con:
        cur = con.cursor()
        cur.execute("SELECT Symbol FROM companylist")
    
        row = cur.fetchall()
        for i in range(len(row)):
            theName = row[i][0]
            if theName.find('^')>0:
                continue 
            #print theName
            thesql = 'select * from '+theName+'daily where pricedate<=\''+StartDate+'\' order by pricedate desc limit '+str(DateNumber)
            data = GetDataFromATable(thesql)
            if len(data[0])==0:
                continue
            isUp = IsPotential(data)
            if isUp:
                AllDic[theName] = np.mean(data[-1])
    
    sorted_x = sorted(AllDic.items(), key=operator.itemgetter(1))
    for anitem in sorted_x:
        print anitem
        
def IsPotential(data):
    # find those price increases more than decreases
    # find those volume grow
    if len(data)==0:
        return False
    #Dates = list(reversed(data[0]))
    #OpenPrices = list(reversed(data[1]))
    #ClosePrices = list(reversed(data[2]))
    #HighPrices = list(reversed(data[3]))
    #LowPrices = list(reversed(data[4]))
    #Volumes = list(reversed(data[5]))
    
    Dates = data[0]
    OpenPrices = data[1]
    ClosePrices = data[2]
    HighPrices = data[3]
    LowPrices = data[4]
    Volumes = data[5]
    
    DayRange = 10
    if len(Dates)<DayRange:
        return False
    if ClosePrices[0]<max(HighPrices[1:DayRange]):
        return False
    for i in range(1,DayRange-1):
        if ClosePrices[i]>max(HighPrices[i+1:DayRange]):
            return False
    recentVariance = np.var(ClosePrices[0:20])
    oldVariance = np.var(ClosePrices[20:]) 
    if recentVariance>oldVariance*0.5:
        return False
    return True
    
if __name__=='__main__':
    todaystring = time.strftime('%Y-%m-%d')
    #todaystring = '2017-01-17'
    print todaystring
    print ('Get Up Trend Stocks')
    GetUpTrendStocks(todaystring)
    print('\n=======================================================\nGet Breakout Stocks')
    GetPotentialStocks(todaystring,70)