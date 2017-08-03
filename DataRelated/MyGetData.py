'''

@author: zhengchenzhang
'''
import pandas as pd
import numpy as np
import urllib2
import datetime as dt
import matplotlib.pyplot as plt
from pandas.tools.plotting import df_ax
import sys

class GetData(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
    def GetDataInADay(self,symbol,market,window=1,period=5*60):
        '''
        return [time open high low close volume]
        '''
        if market!='SGX' and market!='NASD' and market!='NASD_index':
            print 'market value error! '+market
            return [[],[],[],[],[],[]]
        if market=='NASD_index':
            market = 'NASD'
        url_root = 'http://www.google.com/finance/getprices?i='
        url_root += str(period) + '&p=' + str(window)
        url_root += 'd&f=d,o,h,l,c,v&df=cpct&q=' + symbol
        url_root += '&x='+market
        if symbol=='IXIC':
            url_root = url_root[0:-7]
        print url_root
        try:
            response = urllib2.urlopen(url_root)
            data = response.read().split('\n')
        except:
            print sys.exc_info()[0]
            return []
        #print data
        #actual data starts at index = 7
        #first line contains full timestamp,
        #every other line is offset of period from timestamp
        parsed_data = []
        anchor_stamp = ''
        end = len(data)
        if market=='SGX':
            timezoneoffset = 0
        else:
            timezoneoffset = -12*60*60
        
        for i in range(7, end):
            cdata = data[i].split(',')
            if 'a' in cdata[0]:
                #first one record anchor timestamp
                anchor_stamp = cdata[0].replace('a', '')
                cts = int(anchor_stamp) + timezoneoffset
                parsed_data.append((dt.datetime.fromtimestamp(float(cts)), float(cdata[1]), float(cdata[2]), float(cdata[3]), float(cdata[4]), float(cdata[5])))
                #print parsed_data[-1]
            else:
                try:
                    coffset = int(cdata[0])
                    cts = int(anchor_stamp) + (coffset * period) + timezoneoffset
                    parsed_data.append((dt.datetime.fromtimestamp(float(cts)), float(cdata[1]), float(cdata[2]), float(cdata[3]), float(cdata[4]), float(cdata[5])))
                    #print parsed_data[-1]
                except:
                    pass # for time zone offsets thrown into data
        '''df = pd.DataFrame(parsed_data)
        df.columns = ['ts', 'o', 'h', 'l', 'c', 'v']
        df.index = df.ts
        del df['ts']'''
        return parsed_data

    def GetDailyDataFromGoogle(self,window,symbol):
        '''
        we lost the market (NASD or NYSE) info in the database
        So we try two times here...
        '''
        symbol = symbol.upper()
        theres = self._SubGetDailyDataFromGoogle(window, symbol, 'NASD')
        if len(theres[0])==0:
            return self._SubGetDailyDataFromGoogle(window, symbol, 'NYSE')
        else:
            return theres
    
        
    def _SubGetDailyDataFromGoogle(self,window,symbol,market):
        '''
        return [time close high low open volume]
        '''
        period = 86400
        url_root = 'http://www.google.com/finance/getprices?i='
        url_root += str(period)+ '&p=' + str(window)
        url_root += 'd&f=d,c,h,l,o,v&df=cpct&q=' + symbol
        url_root += '&x='+market
        #print url_root
        try:
            response = urllib2.urlopen(url_root)
            data = response.read().split('\n')
        except:
            print sys.exc_info()[0]
            return [[],[],[],[],[],[]]
        #print data
        #actual data starts at index = 7
        #first line contains full timestamp,
        #every other line is offset of period from timestamp
        anchor_stamp = ''
        end = len(data)
        if market=='SGX':
            timezoneoffset = 0
        else:
            timezoneoffset = -12*60*60
        
        thedates = []
        close=[]
        openprice = []
        high = []
        low = []
        volume = []
        
        for i in range(7, end):
            cdata = data[i].split(',')
            if len(cdata)<6:
                #print cdata
                continue
            if 'a' in cdata[0]:
                #first one record anchor timestamp
                anchor_stamp = cdata[0].replace('a', '')
                cts = int(anchor_stamp) + timezoneoffset
            else:
                try:
                    coffset = int(cdata[0])
                    cts = int(anchor_stamp) + (coffset * period) + timezoneoffset
                    #print parsed_data[-1]
                except:
                    continue # for time zone offsets thrown into data
            adate = dt.datetime.fromtimestamp(float(cts)).strftime('%Y-%m-%d')
            thedates.insert(0,adate)
            close.insert(0,cdata[1])
            high.insert(0,cdata[2])
            low.insert(0,cdata[3])
            openprice.insert(0,cdata[4])
            volume.insert(0,cdata[5])   
            #print parsed_data[-1]
            
       
        return [thedates,close,high,low,openprice,volume]
    
    def GetStockHistoryChartAPI(self,monthrange,stockid):
        '''
        return daily price data
        '''
        try:
            print 'Currently Pulling',stockid
            urlToVisit = 'http://chartapi.finance.yahoo.com/instrument/1.1/'+stockid+'/chartdata;type=quote;range='+str(monthrange)+'m/csv'
            stockFile =[]
            try:
                sourceCode = urllib2.urlopen(urlToVisit).read()
                splitSource = sourceCode.split('\n')
                for eachLine in splitSource:
                    if eachLine.find("errorid")>=0:
                        print eachLine
                        return [[],[],[],[],[],[]]
                    splitLine = eachLine.split(',')
                    if len(splitLine)==6:
                        if 'values' not in eachLine and 'labels' not in eachLine:
                            stockFile.append(eachLine)
                if len(stockFile)==0:
                    return [[],[],[],[],[],[]]
                [date, closep, highp, lowp, openp, volume] = np.loadtxt(stockFile,delimiter=',', unpack=True)
                strdate = []
                for k in range(len(date)):
                    thedate = dt.datetime.strptime(str(int(date[k])),'%Y%m%d').strftime('%Y-%m-%d')
                    strdate.append(thedate)
                return [strdate, closep, highp, lowp, openp, volume]
            except Exception, e:
                print str(e), 'failed to organize pulled data.'
                return [[],[],[],[],[],[]]
        except Exception,e:
            print str(e), 'failed to pull pricing data'
            return [[],[],[],[],[],[]]
        
    def GetTodayData(self,stockid):
        '''
        return the latest daily data
        ['2015-12-17', 108.98, 112.25, 108.98, 112.02, 44554400.0]
        '''
        try:
            print 'Currently Pulling',stockid
            urlToVisit = 'http://chartapi.finance.yahoo.com/instrument/1.1/'+stockid+'/chartdata;type=quote;range=1m/csv'
            stockFile =[]
            try:
                sourceCode = urllib2.urlopen(urlToVisit).read()
                splitSource = sourceCode.split('\n')
                for eachLine in splitSource:
                    if eachLine.find("errorid")>=0:
                        print eachLine
                        return [[],[],[],[],[],[]]
                    splitLine = eachLine.split(',')
                    if len(splitLine)==6:
                        if 'values' not in eachLine and 'labels' not in eachLine:
                            stockFile.append(eachLine)
                if len(stockFile)==0:
                    return [[],[],[],[],[],[]]
                [date, closep, highp, lowp, openp, volume] = np.loadtxt(stockFile,delimiter=',', unpack=True)
                strdate = []
                k = len(date) - 1
                thedate = dt.datetime.strptime(str(int(date[k])),'%Y%m%d').strftime('%Y-%m-%d')
                strdate.append(thedate)
                return [strdate[-1], closep[-1], highp[-1], lowp[-1], openp[-1], volume[-1]]
            except Exception, e:
                print str(e), 'failed to organize pulled data.'
                return [[],[],[],[],[],[]]
        except Exception,e:
            print str(e), 'failed to pull pricing data'
            return [[],[],[],[],[],[]]
        
        
if __name__=='__main__':
    gd = GetData()
    df = gd.GetDataInADay('AAPL',window=100)
    print df