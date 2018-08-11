'''
Created on 2017 3 18

@author: Yali
'''
import MyPredictDB as MyDB
import numpy as np
import pickle
import matplotlib.pyplot as plt

TotalNumber = 4
def GetDragonHeads():
    #select distinct sectors
    with MyDB.con:
        cur = MyDB.con.cursor()
        try:
            cur.execute('select * from companylist')
        except:
            return []
        row = cur.fetchall()
        if len(row)==0:
            return []
        Sectors = {}
        for i in range(len(row)):
            theName = row[i]
            try:
                if not theName[4] in Sectors:
                    Sectors[theName[4]] = []
                Sectors[theName[4]].append(theName[0])
            except:
                print 'error'
    for akey in sorted(Sectors.keys()):
        print akey
        thenames = Sectors[akey]
        print 'company number is '+str(len(thenames))
        if len(thenames)<5:
            print '========='+akey+' has a few companies============='
        
    '''
    '''
    #return
    '''
    '''




    #get mean volume and average close prices in half year
    TheValues = {}
    BestCompanies = {}
    for asector in Sectors:
        print asector
        TheValues[asector] = {}
        BestCompanies[asector] = []
        thelist = Sectors[asector]
        for aname in thelist:
            thesql = 'select * from '+aname+'daily order by pricedate desc limit 60'
            data = MyDB.GetDataFromATable(thesql)
            ClosePrices = data[2]
            Volumes = data[5]
            TheValues[asector][aname] = np.sum(np.multiply(ClosePrices,Volumes))
            # get the best ones
            # if there is less then 10, input the name according to the value
            if len(BestCompanies[asector])==0:
                BestCompanies[asector].append(aname)
            elif len(BestCompanies[asector])<TotalNumber:
                bAdd = False
                for i in range(len(BestCompanies[asector])):
                    if TheValues[asector][BestCompanies[asector][i]]<TheValues[asector][aname]:
                        BestCompanies[asector].insert(i,aname)
                        bAdd = True
                        break
                if not bAdd:
                    BestCompanies[asector].append(aname)
                
            else:
                for i in range(len(BestCompanies[asector])):
                    if TheValues[asector][BestCompanies[asector][i]]<TheValues[asector][aname]:
                        BestCompanies[asector].insert(i,aname)
                        break
                if len(BestCompanies[asector])>TotalNumber:
                    BestCompanies[asector] = BestCompanies[asector][0:TotalNumber+1]
    #get best ten for each SECTOR
    
    # save
    for asector in BestCompanies:
        print asector
        for anitem in BestCompanies[asector]:
            print '\t'+anitem
        print '==============\n'
        
    pickle.dump(BestCompanies, open('../data/DragonHeads', "w"))
    
def PrintDragonHeads(BestCompanies,daynumber = 90):
    '''
    input: a dictionary. Key is the sector name, value is a list of company names
    '''
    AllPrices = []
    xnumbers = np.ones(daynumber)
    for i in range(1,daynumber):
        xnumbers[i] = xnumbers[i-1]+1
    for asector in BestCompanies:
        print asector+'============='
        names = BestCompanies[asector]
        SectorPrices = []
        for aname in names:
            thesql = 'select * from '+aname+'daily order by pricedate desc limit '+str(daynumber)
            data = MyDB.GetDataFromATable(thesql)
            ClosePrices = data[2]
            ClosePrices = np.divide(ClosePrices,ClosePrices[-1])
            ClosePrices = ClosePrices.tolist()
            ClosePrices.reverse()
            SectorPrices.append(ClosePrices)
        AllPrices.append(SectorPrices)
        plt.figure()
        theLength = len(SectorPrices[0])
        for i in range(len(names)):
            print names[i]
            if len(SectorPrices[i])!=theLength:
                continue
            if theLength!=daynumber:
                continue
            plt.plot(xnumbers,SectorPrices[i],label=names[i])
        plt.legend(loc=3)    
        plt.show()
    return AllPrices
 
def PrintCurrentDragonHeads():
    BestC = pickle.load(open('../data/DragonHeads','r'))
    PrintDragonHeads(BestC)           

if __name__=='__main__':
    GetDragonHeads()
    PrintCurrentDragonHeads()