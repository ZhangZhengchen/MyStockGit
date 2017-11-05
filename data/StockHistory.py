'''
Created on 2017 8 7

@author: Yali
'''
import datetime
import os
import collections

class StockHistoryQuote(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.Symbol = ""
        # date,open,close,high,low,volume
        self.Data = [[],[],[],[],[],[]]
        
    
    def ReadFromHistoryCVS(self,FileName,Symbol):
        '''
        '''
        self.Symbol = Symbol
        f= open(FileName)
        AllLines = f.readlines()
        f.close()
        AllLines = AllLines[2:]
        for aline in AllLines:
            aline = aline.strip()
            aline = aline.replace('"','')
            temp = aline.split(',')
            self.Data[0].append(datetime.datetime.strptime(temp[0],'%Y/%m/%d'))
            self.Data[1].append(float(temp[3]))
            self.Data[2].append(float(temp[1]))
            self.Data[3].append(float(temp[4]))
            self.Data[4].append(float(temp[5]))
            self.Data[5].append(float(temp[2]))
            
    def ReadFromHistoryCVSWithDate(self,FileName,Symbol,StartDate,EndDate,AllTimeHighPeriod=200):
        '''
        @param StartDate: string format
        @param EndDate: string format 
        '''
        theStartDate = datetime.datetime.strptime(StartDate,'%Y-%m-%d').date()
        theEndDate = datetime.datetime.strptime(EndDate,'%Y-%m-%d').date()
        totalPeriod = (theEndDate-theStartDate).days+AllTimeHighPeriod
        
        self.Symbol = Symbol
        f= open(FileName)
        AllLines = f.readlines()
        f.close()
        TotalNumber = 0
        AllLines = AllLines[2:]
        for aline in AllLines:
            aline = aline.strip()
            aline = aline.replace('"','')
            temp = aline.split(',')
            CurrentDate = datetime.datetime.strptime(temp[0],'%Y/%m/%d').date()
            if CurrentDate>theEndDate:
                continue
            else:
                self.Data[0].append(CurrentDate)
                self.Data[1].append(float(temp[3]))
                self.Data[2].append(float(temp[1]))
                self.Data[3].append(float(temp[4]))
                self.Data[4].append(float(temp[5]))
                self.Data[5].append(float(temp[2]))
                TotalNumber+=1
                if TotalNumber>totalPeriod:
                    break
        if (self.Data[0][0]-self.Data[0][-1]).days<totalPeriod:
            self.Data = []
 
def ReadStockHistoryFromCSV(StartDate,EndDate,MaxAllTimeHighPeriod,AllData):
    '''
    Read all the data from cvs downloaded from nasdaq
    '''
    HistoryDir = 'G:\\zc\\OneDrive\\Stock\\data\\history'
    for root,subdir,files in os.walk(HistoryDir):
        for afile in files:
            Symbol = afile[0:-4]
            datafile = os.path.join(root,afile)
            AStockHistory = StockHistoryQuote()
            AStockHistory.ReadFromHistoryCVSWithDate(datafile, Symbol, StartDate, EndDate, MaxAllTimeHighPeriod)
            if not AStockHistory.Data==[]:
                AllData[Symbol] = AStockHistory.Data

def GetSPXInfo():
    '''
    If SPY<100 day SMA, will not open new long positions any more
    '''
    SPYHistoryFile = 'G:\\zc\\OneDrive\\Stock\\data\\SPY.csv'
    f = open(SPYHistoryFile)
    AllLines = f.readlines()
    f.close()
    
    AllLines = AllLines[2:]
    SPYData = {}
    for aline in AllLines:
        aline = aline.strip()
        temp = aline.split(',')
        TheDate = datetime.datetime.strptime(temp[0],'%Y/%m/%d')
        Close = float(temp[1])
        SMA100 = float(temp[6])
        SMA200 = float(temp[7])
        SPYData[TheDate] = [Close,SMA100,SMA200]
        SPYData = collections.OrderedDict(sorted(SPYData.items(),reverse=True))
    return SPYData

if __name__=='__main__':
    data = GetSPXInfo()