'''
Created on 2017 7 29

@author: zhengchenzhang
'''
import matplotlib.pyplot as plt
import matplotlib.finance as plotf
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import pylab
import numpy as np

class PlotClass(object):
    def drawData(self, date, openp, closep, highp, lowp, volume,SaveImage=False,SaveName=''):
        try:
            plt.close()
            fig = plt.figure(facecolor='#ffffff',figsize=(5,5))
            x = 0
            y = len(date)
            newAr = []
            while x < y:
                appendLine = date[x],openp[x],closep[x],highp[x],lowp[x],volume[x]
                newAr.append(appendLine)
                x+=1
                
            #SP = len(date[MA2-1:])
            SP = 0
            ax1 = plt.subplot2grid((8,4), (1,0), rowspan=4, colspan=4, axisbg='#ffffff')
            plotf.candlestick(ax1, newAr[-SP:], width=.6, colorup='#53c156', colordown='#ff1717')
            #candlestick(ax1, openp[-SP:],closep[-SP:],highp[-SP:],lowp[-SP:], width=.6)
            
            ax1.grid(False)
            ax1.xaxis.set_major_locator(mticker.MaxNLocator(10))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax1.yaxis.label.set_color("b")
            ax1.spines['bottom'].set_color("#5998ff")
            ax1.spines['top'].set_color("#5998ff")
            ax1.spines['left'].set_color("#5998ff")
            ax1.spines['right'].set_color("#5998ff")
            ax1.tick_params(axis='y', colors='b')
            plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(prune='upper'))
            ax1.tick_params(axis='x', colors='b')
            #plt.ylabel('Stock price')
    
            #maLeg = plt.legend(loc=9, ncol=2, prop={'size':7},
            #           fancybox=True, borderaxespad=0.)
            #maLeg.get_frame().set_alpha(0.4)
            #textEd = pylab.gca().get_legend().get_texts()
            #pylab.setp(textEd[0:5], color = 'b')
    
            volumeMin = 0
            
            #ax1v = ax1.twinx()
            ax1v = plt.subplot2grid((8,4), (5,0), sharex=ax1, rowspan=1, colspan=4, axisbg='#ffffff')
            ax1v.fill_between(date[-SP:],volumeMin, volume[-SP:], facecolor='#00ffe8', alpha=.4)
            #ax1v.axes.yaxis.set_ticklabels([])
            
            ax1v.grid(False)
            ax1v.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='upper'))
            ###Edit this to 3, so it's a bit larger
            ax1v.set_ylim(0, 1.1*np.max(volume))
            ax1v.spines['bottom'].set_color("#5998ff")
            ax1v.spines['top'].set_color("#5998ff")
            ax1v.spines['left'].set_color("#5998ff")
            ax1v.spines['right'].set_color("#5998ff")
            ax1v.tick_params(axis='x', colors='b')
            ax1v.tick_params(axis='y', colors='b')
            #plt.ylabel('Volume', color='b')
            
            plt.setp(ax1.get_xticklabels(), visible=False)
            
            '''ax1.annotate('Big news!',(date[510],Av1[510]),
                xytext=(0.8, 0.9), textcoords='axes fraction',
                arrowprops=dict(facecolor='white', shrink=0.05),
                fontsize=14, color = 'w',
                horizontalalignment='right', verticalalignment='bottom')'''
    
            #plt.subplots_adjust(left=.09, bottom=.14, right=.94, top=.95, wspace=.20, hspace=0)
            if not SaveImage:
                plt.show()
            else:
                plt.savefig(SaveName)
            #self.fig.savefig('example.png',facecolor=self.fig.get_facecolor())
               
        except Exception,e:
            print 'main loop',str(e)