'''
Created on 2017 3 25

@author: Yali
'''
import Database

def AddIndustry(InputFile):
    '''
    we have two company lists, so the inputfile is one of the list.
    '''
    f = open(InputFile)
    # remove the first line
    f.readline()
    for aline in f:
        
        # for the two files, the processing is different
        # for nyse, we need to remove the ""
        aline = aline.strip().split('","')
        thesymble = aline[0][1:]
        theindustry = aline[6]
        # for nasdaq, no need
        '''aline = aline.strip()
        theindex = aline.find(',')
        thesymble = aline[0:theindex]
        aline = aline[theindex+1:]
        theindex = aline.find('$')
        aline = aline[theindex+1:]
        temp = aline.split(',')
        theindustry = temp[-2]
        '''
        cur = Database.con.cursor()
        try:
            cur.execute("update companylist set Industry='"+theindustry+"' where Symbol='"+thesymble+"'")
            Database.con.commit()
        except:
            print 'something is wrong'
            cur.close()
            return
        cur.close() 
    f.close()
    
if __name__=='__main__':
    InputFile = 'G:\\zc\\work\\program\\eclipse\\Stock\\StockStrategy\\NYSE.csv'
    #InputFile = 'G:\\zc\\work\\program\\eclipse\\Stock\\StockStrategy\\USCmpList.csv'
    AddIndustry(InputFile)