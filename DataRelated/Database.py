'''
Created on 2017 3 25

@author: Yali
'''
import MySQLdb as mdb
import sys
import time
import Condition
import numpy as np
import MyGetData
import datetime
import copy
import sklearn.preprocessing as prep

con = mdb.connect('localhost', 'root', '', 'nasdaq')  
def CreateDailyTable():
    with con:
        cur = con.cursor()
        cur.execute("SELECT Symbol FROM companylist")
    
        row = cur.fetchall()
        for i in range(len(row)):
            theName = row[i]
            try:
                theSQL = 'create table '+theName[0].lower()+'daily ('\
                'pricedate DATE, open float, close float, high float, low float, volume bigint)'
                print theSQL
                cur.execute(theSQL)
            except:
                print 'error'
            print theName[0]
            
def DeleteDataInAllTable():
    with con:
        cur = con.cursor()
        cur.execute("SELECT Symbol FROM companylist")
        row = cur.fetchall()
        for i in range(len(row)):
            theName = row[i][0].lower()
            try:
                theSQL = "select count(*) from "+theName+'daily'
                cur.execute(theSQL)
                res = cur.fetchall()
                if res[0][0]==0:
                    theSQL = 'drop table '+theName+'daily'
                    cur.execute(theSQL)
                    con.commit()
                    theSQL = 'delete from companylist where Symbol=\''+theName+'\''
                    cur.execute(theSQL)
                    con.commit()
                #theSQL = 'delete from '+theName[0]+'daily'
                #print theSQL
                #cur.execute(theSQL)
                #con.commit()
            except:
                print 'error'
            print theName

def DeleteRemovedCompanyInDatabase():
    with con:
        cur = con.cursor()
        cur.execute("SELECT Symbol FROM companylist")
        row = cur.fetchall()
        for i in range(len(row)):
            theName = row[i][0].lower()
            try:
                theSQL = "select * from "+theName+'daily order by pricedate desc'
                cur.execute(theSQL)
                res = cur.fetchall()
                if res[0][0]<datetime.datetime.strptime('2016-10-01','%Y-%m-%d').date():
                    theSQL = 'drop table '+theName+'daily'
                    cur.execute(theSQL)
                    con.commit()
                    theSQL = 'delete from companylist where Symbol=\''+theName+'\''
                    cur.execute(theSQL)
                    con.commit()
                #theSQL = 'delete from '+theName[0]+'daily'
                #print theSQL
                #cur.execute(theSQL)
                #con.commit()
            except:
                print 'error'
            print theName

def DeleteAllData():
    with con:
        cur = con.cursor()
        cur.execute("SELECT Symbol FROM companylist")
        row = cur.fetchall()
        for i in range(len(row)):
            theName = row[i][0].lower()
            try:
                theSQL = "delete from "+theName+'daily'
                cur.execute(theSQL)
                con.commit()
                
            except:
                print 'error'
            print theName
            
def UpdateDailyDataForATable(tablename):
    '''
    Step 1: Get latest date in the database
    Step 2: Get 1 month data
    Step 3: If the data is newer than the latest date, insert into the database.
    '''

def GetSectors():
    with con:
        cur = con.cursor()
        cur.execute("SELECT distinct(Sector) FROM companylist")
    
        row = cur.fetchall()
        AllNames = []
        for i in range(len(row)):
            theName = row[i][0]
            AllNames.append(theName)
        cur.close()
        return AllNames
    return []

def GenerateFeatureForMachineLearning(SectorName):
    print SectorName
    TheSectorName = SectorName.replace(' ','')
    featurefile = './ML/'+TheSectorName+'.csv'
    testFeatureFile = './ML/'+TheSectorName+'_test.csv'
    ftest = open(testFeatureFile,'w')

    with con:
        cur = con.cursor()
        cur.execute("SELECT Symbol FROM companylist where Sector='"+SectorName+"'")
    
        row = cur.fetchall()
        writeTitle = False
        f = open(featurefile,'w')
        for i in range(len(row)):
            theName = row[i][0]
            if theName.find('^')>0:
                continue
            AllFeature = GenerateFeatureForATable(theName+'daily')
            if len(AllFeature)==0:
                continue
            BadDates = AllFeature[-1]
            Labels = AllFeature[-2]
            AllFeature = AllFeature[0:len(AllFeature)-2]
            #####################
            featureLength = len(AllFeature)
            context = 4
            if not writeTitle:
                for i in range(featureLength*context):
                    f.write('Col'+str(i)+',')
                f.write('Label\n')
                writeTitle = True
            for i in range(len(Labels)):
                if i in BadDates:
                    continue
                bad = False
                for k in range(context):
                    if i-k in BadDates:
                        bad = True
                        break
                if bad:
                    continue
                if i<context:
                    continue
                thestr = ''
                for k in range(i-context,i+1):
                    for m in range(featureLength):
                        #print 'k='+str(k)
                        #print 'm='+str(m)
                        thestr += str(AllFeature[m][k])+','
                thestr = thestr+str(Labels[i])
                f.write(thestr+'\n')
                thestr = thestr[0:thestr.rfind(',')]
            ftest.write(theName+',,,'+datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d')+',,,'+thestr.replace(',',' ')+'\n')
    ftest.close()
    f.close()
    
def LocalNormalizeForATable(Input):
    Input = prep.normalize(np.array(Input).reshape(len(Input),1),axis=0)
    Input = np.array(Input).reshape(1,len(Input))[0]
    return Input
    
def GenerateFeatures(Dates,OpenPrices,ClosePrices,HighPrices,LowPrices,Volumes):
    if len(ClosePrices)<=15:
        return []
    if np.mean(Volumes)<800000:
        return []
    #Get SMA
    SMA5 = Condition.Condition.mymovingaverage(ClosePrices,5)
    SMA10 = Condition.Condition.mymovingaverage(ClosePrices,10)
    VolSMA5 = Condition.Condition.mymovingaverage(Volumes,5)
    VolSMA10 = Condition.Condition.mymovingaverage(Volumes,10)
    RatioSMA5 = np.divide(np.subtract(ClosePrices,SMA5),SMA5)
    RatioSMA10 = np.divide(np.subtract(ClosePrices,SMA10),SMA10)
    RatioVolSMA5 = np.divide(np.subtract(Volumes, VolSMA5),VolSMA5)
    RatioVolSMA10 = np.divide(np.subtract(Volumes, VolSMA10),VolSMA10)
    # Get Close and High relationship
    CloseHigh = np.subtract(ClosePrices, HighPrices)
    CloseHigh = LocalNormalizeForATable(CloseHigh)
    #RSI
    RSI5 = Condition.Condition.myrsiFunc(ClosePrices, 5)
    RSI10 = Condition.Condition.myrsiFunc(ClosePrices, 10)
    #Open, close, high, and low relationship
    IsIncreaseToday = []
    OpenToClose = []
    for i in range(len(OpenPrices)):
        if OpenPrices[i]>ClosePrices[i]:
            IsIncreaseToday.append(-1)
        else:
            IsIncreaseToday.append(1)
        OpenToClose.append(OpenPrices[i]-ClosePrices[i])
    OpenToClose = LocalNormalizeForATable(OpenToClose)
    
    HighToOpen = np.subtract(HighPrices,OpenPrices)
    HighToOpen = LocalNormalizeForATable(HighToOpen)
    
    LowToOpen = np.subtract(LowPrices,OpenPrices)
    LowToOpen = LocalNormalizeForATable(LowToOpen)
    
    LowToClose = np.subtract(LowPrices,ClosePrices)
    LowToClose = LocalNormalizeForATable(LowToClose)
    
    HighToLow = np.subtract(HighPrices, LowPrices)
    HighToLow = LocalNormalizeForATable(HighToLow)
    
    HigherHigh7 = np.zeros(len(HighPrices))
    for i in range(14,len(HighPrices)-1):
        HigherHigh7[i] = max(HighPrices[i-7:i+1])-max(HighPrices[i-14:i-7])
    HigherHigh7 = LocalNormalizeForATable(HigherHigh7)
    
    HigherHigh5 = np.zeros(len(HighPrices))
    for i in range(10,len(HighPrices)-1):
        HigherHigh5[i] = max(HighPrices[i-5:i+1])-max(HighPrices[i-10:i-5])
    HigherHigh5 = LocalNormalizeForATable(HigherHigh5)
    
    HigherHigh3 = np.zeros(len(HighPrices))
    for i in range(6,len(HighPrices)-1):
        HigherHigh3[i] = max(HighPrices[i-3:i+1])-max(HighPrices[i-6:i-3])
    HigherHigh3 = LocalNormalizeForATable(HigherHigh3)
    
    HigherHigh14to21 = np.zeros(len(HighPrices))
    for i in range(21,len(HighPrices)-1):
        HigherHigh14to21[i] = max(HighPrices[i-14:i-7])-max(HighPrices[i-21:i-14])
    HigherHigh14to21 = LocalNormalizeForATable(HigherHigh14to21)
    
    HigherHigh10to15 = np.zeros(len(HighPrices))
    for i in range(15,len(HighPrices)-1):
        HigherHigh10to15[i] = max(HighPrices[i-10:i-5])-max(HighPrices[i-15:i-10])
    HigherHigh10to15 = LocalNormalizeForATable(HigherHigh10to15)
    
    HigherHigh6to9 = np.zeros(len(HighPrices))
    for i in range(9,len(HighPrices)-1):
        HigherHigh6to9[i] = max(HighPrices[i-6:i-3])-max(HighPrices[i-9:i-6])
    HigherHigh6to9 = LocalNormalizeForATable(HigherHigh6to9)
    
    HigherLow7 = np.zeros(len(LowPrices))
    for i in range(14,len(LowPrices)-1):
        HigherLow7[i] = min(LowPrices[i-7:i+1])-min(LowPrices[i-14:i-7])
    HigherLow7 = LocalNormalizeForATable(HigherLow7)
    
    HigherLow5 = np.zeros(len(LowPrices))
    for i in range(10,len(LowPrices)-1):
        HigherLow5[i] = min(LowPrices[i-5:i+1])-min(LowPrices[i-10:i-5])
    HigherLow5 = LocalNormalizeForATable(HigherLow5)
    
    HigherLow3 = np.zeros(len(LowPrices))
    for i in range(6,len(LowPrices)-1):
        HigherLow3[i] = min(LowPrices[i-3:i+1])-min(LowPrices[i-6:i-3])
    HigherLow3 = LocalNormalizeForATable(HigherLow3)
    
    HigherLow14to21 = np.zeros(len(LowPrices))
    for i in range(21,len(LowPrices)-1):
        HigherLow14to21[i] = min(LowPrices[i-14:i-7])-min(LowPrices[i-21:i-14])
    HigherLow14to21 = LocalNormalizeForATable(HigherLow14to21)
    
    HigherLow10to15 = np.zeros(len(LowPrices))
    for i in range(15,len(LowPrices)-1):
        HigherLow10to15[i] = min(LowPrices[i-10:i-5])-min(LowPrices[i-15:i-10])
    HigherLow10to15 = LocalNormalizeForATable(HigherLow10to15)
    
    HigherLow6to9 = np.zeros(len(LowPrices))
    for i in range(9,len(LowPrices)-1):
        HigherLow6to9[i] = min(LowPrices[i-6:i-3])-min(LowPrices[i-9:i-6])
    HigherLow6to9 = LocalNormalizeForATable(HigherLow6to9)
    
    tempClose = copy.copy(ClosePrices)
    tempClose.insert(0, OpenPrices[0])
    tempClose = tempClose[0:len(tempClose)-1]
    OpenToYesterdayClose = np.subtract(OpenPrices,tempClose)
    OpenToYesterdayClose = LocalNormalizeForATable(OpenToYesterdayClose)
    
    IsUpTrend = np.zeros(len(ClosePrices))
    for i in range(7,len(ClosePrices)):
        if ClosePrices[i]>ClosePrices[i-3] and ClosePrices[i]>ClosePrices[i-7]:
            IsUpTrend[i] = 1.0
            if ClosePrices[i-3]>ClosePrices[i-7]:
                IsUpTrend[i]=2.0
    
    OpenVolumeCorr = np.zeros(len(OpenPrices))
    for i in range(10,len(OpenPrices)):
        a = np.corrcoef(OpenPrices[i-10:i+1],Volumes[i-10:i+1])
        OpenVolumeCorr[i] = a[0,1]
    CloseVolumeCorr = np.zeros(len(ClosePrices))
    for i in range(10,len(ClosePrices)):
        a = np.corrcoef(ClosePrices[i-10:i+1],Volumes[i-10:i+1])
        CloseVolumeCorr[i] = a[0,1]
    HighVolumeCorr = np.zeros(len(HighPrices))
    for i in range(10,len(HighPrices)):
        a = np.corrcoef(HighPrices[i-10:i+1],Volumes[i-10:i+1])
        HighVolumeCorr[i] = a[0,1]
    CloseVolumeOneDayBefore = np.zeros(len(ClosePrices))
    for i in range(1,len(ClosePrices)):
        a = np.sign(Volumes[i]-Volumes[i-1])
        CloseVolumeOneDayBefore[i] = a*-1*(ClosePrices[i]-ClosePrices[i-1])/ClosePrices[i]
    #Label
    Labels = []
    BadDates = []
    for i in range(len(HighPrices)):
        if i+2<=len(HighPrices):
            if Dates[i+1] - Dates[i]>datetime.timedelta(days=4):
                BadDates.append(i)
            Next3High = max(HighPrices[i+1:i+2])
            res = (Next3High - ClosePrices[i])/(ClosePrices[i]+0.0001)
            
            if res>=0.015:
                Labels.append(1)
            else:
                Labels.append(-1)
            
            #Labels.append((Next3High - ClosePrices[i])/ClosePrices[i])
        else:
            Labels.append(-1)
    return [RatioSMA5,RatioSMA10,RatioVolSMA5,RatioVolSMA10,CloseHigh,\
            RSI5,RSI10,IsIncreaseToday,IsUpTrend,HigherHigh5,HigherLow5,HigherHigh10to15,HigherLow10to15,\
            HigherHigh3,HigherHigh6to9,HigherLow3,HigherLow6to9,\
            HigherHigh7,HigherHigh14to21,HigherLow7,HigherLow14to21,\
            OpenToClose,HighToOpen,LowToOpen,LowToClose,HighToLow,OpenToYesterdayClose,\
            OpenVolumeCorr,CloseVolumeCorr,HighVolumeCorr,CloseVolumeOneDayBefore,\
            Labels,BadDates]    
def GenerateFeatureForATable(tablename):
    '''
    Step 1: select data from the table
    Step 2: Get Simple Moving Average 5 and 10 of prices and volumes.
    Step 3: Compute the ration: (x_{i} - average_{i})/average_{i}
    Step 4: Generate the label: (The highest price in next 3 days - The close price today)/The close price today
    '''    
    with con:
        cur = con.cursor()
        try:
            cur.execute("SELECT * FROM "+tablename+" group by pricedate order by pricedate ")
        except:
            return []
        row = cur.fetchall()
        if len(row)==0:
            return []
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
        #####################
        #####################
        features = GenerateFeatures(Dates, OpenPrices, ClosePrices, HighPrices, LowPrices, Volumes)
        return features

def UpdateData():
    '''
    Get all company symbols
    Update one by one
    '''
    cur = con.cursor()
    cur.execute("SELECT Symbol FROM companylist")

    row = cur.fetchall()
    cur.close()
    for i in range(len(row)):
        theName = row[i][0]
        theName = theName.lower()
        print theName
        UpdateDataForATable(theName)
        
def UpdateDataForATable(symbol):
    ''''
    Step 1: Get data
    Step 2: Get latest date in the database
    Step 3: Insert into the database
    '''
    # Get data
    gd = MyGetData.GetData()
    res = gd.GetStockHistoryChartAPI(36, symbol)
    # Get latest date
    cur = con.cursor()
    
    try:
        cur.execute("select pricedate from "+symbol+"daily order by pricedate desc limit 1")
        row = cur.fetchall()
        if len(row)==0:
            thedate = datetime.datetime.strptime('2000-02-02','%Y-%m-%d').date()
        else:
            thedate = row[0][0]
    except:
        print 'Error at get latest date in UpdateDataForATable'
        return
    # compare date
    values = []
    for i in range(len(res[0])):
        curdate = res[0][i]
        if datetime.datetime.strptime(curdate,'%Y-%m-%d').date()<=thedate:
            continue
        else:
            values.append((curdate,res[4][i],res[1][i],res[2][i],res[3][i],int(res[5][i])))
    
    #insert values'
    try:
        theSQL = 'insert into '+symbol+'daily values('
        a = cur.executemany(theSQL+'%s,%s,%s,%s,%s,%s)',values)
        con.commit()
    except:
        cur.close()
        return
    cur.close() 
    

def GetDataForPrediction():
    '''
    Get all symbols
    Get latest date for this symbol
    Get features
    '''  
if __name__=='__main__':
    '''
    Step 1: Create table for all companies. Use daily data first
    '''
    #CreateDailyTable()
    '''
    Step 2: Insert the old data
    '''
    #DeleteDataInAllTable()
    #InsertOldData_Daily('us24.pkl') This function is removed here. Use old StockStrategy to do it if needed.
    #DeleteRemovedCompanyInDatabase()
    #DeleteAllData()
    '''
    Step 4: Update data
    '''
    Step=''
    Step = 'UpdateData'
    if Step=='UpdateData':
        UpdateData()
    ##DeleteDataInAllTable()
    '''
    Step 3: Generate features for training and testing
    '''
    #Step = 'GenerateFeatures'
    if Step=='GenerateFeatures':
        AllNames = GetSectors()
        for aname in AllNames:
            GenerateFeatureForMachineLearning(aname)