from routing import *
from scipy.signal import lfilter,filtfilt
from datetime import datetime, timedelta
from fbprophet import*
import plotly

def filter_data(fillingLevel,plot=False):
    n = 3  # the larger n is, the smoother curve will be
    b = [1.0 / n] * n
    a = 1
    filterData = lfilter(b,a,fillingLevel)
    if(plot):
        plt.plot(range(len(fillingLevel)), fillingLevel)
        plt.plot(range(len(filterData)), filterData)
        plt.show()  
    return(filterData[-1])

def predict(fillingLevel, dates):
    df=pd.DataFrame(list(zip(dates, fillingLevel)),
               columns =['ds', 'y'])
    prophet = Prophet(changepoint_prior_scale=0.15)
    prophet.fit(df)
    future = prophet.make_future_dataframe(periods=1,freq='D')
    forecast=prophet.predict(future)
    forecast[['ds','yhat_lower','yhat_upper','yhat']]
    prophet.plot(forecast, xlabel = 'Date', ylabel = 'f rate')
    plt.show()

def myparser(x):
    return datetime.strptime(x, '%b %d, %Y @ %H:%M:%S.%f')

def get_data_n_day_from_now(csvName, nbrOfDayFromNow):
    now = datetime.now()
    dateLimit= now - timedelta(days=nbrOfDayFromNow)
    times = []
    fillLvl = []
    devicesIds = []
    for chunk in  pd.read_csv(csvName, chunksize=constant.CHUNKSIZE, parse_dates=['timestamp'], date_parser=myparser):
        for i in range(chunk.shape[0]):
            if chunk['timestamp'].iloc[i] >= dateLimit:
                times.append(chunk['timestamp'].iloc[i])
                fillLvl.append(chunk['fillingLevel'].iloc[i])
                devicesIds.append(chunk['deviceId'].iloc[i])
    return [devicesIds,fillLvl,times]


def update_charge(nodesTab, data,fillThreshold):
    nodesToRemove=[]
    for node in nodesTab.tab[:nodesTab.nbrBubbles]:
        node.charge=0
        highEnough=False
        for deviceId in node.deviceId:
            toPop=[]
            fillLvlDeviceId=[]
            dates=[]
            for i in range(len(data[0])):
                if deviceId == data[0][i]:
                    toPop.append(i)      
            for i in range(len(toPop)):
                data[0].pop(toPop[i]-i)
                fillLvlDeviceId.append(data[1].pop(toPop[i]-i))
                dates.append(data[2].pop(toPop[i]-i))
            if(fillLvlDeviceId):
                fillLvlDeviceId.reverse()
                dates.reverse()
                filteredLvl=filter_data(fillLvlDeviceId)

                if(filteredLvl>fillThreshold):
                    highEnough=True

                node.charge+= int(filteredLvl*constant.BUBBLE_MAX_CHARGE/100 )
                
                

            else:
                print("Warning ! No data for device",deviceId)
        if(not highEnough):
            nodesToRemove.append(node.id)
    return nodesToRemove
            
        


def main3():
    tab=get_data_n_day_from_now('csv/data.csv',365)
    nodesTab = build_nodesTab_from_csv('csv/nodes.csv')
    update_charge(nodesTab,tab,50)
        
    
    # print(type(df['timestamp'].iloc[0]))
    # print(df['timestamp'].iloc[0])
    # dates=df['timestamp'].tolist()
    # charges = df['fillingLevel'].tolist()
    # print(dates)
    # dates.reverse()
    # charges.reverse()
    # print(dates[500],"----",dates[2])
    # if(dates[500]>dates[2]):
    #     print("1")


if __name__ == "__main__":
    main3()