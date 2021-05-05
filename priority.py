from routing import *
from scipy.signal import lfilter
from datetime import datetime, timedelta


def filter_data(fillingLevel,plot=False):
    n = 5  # the larger n is, the smoother curve will be
    b = [1.0 / n] * n
    a = 1
    filterData = lfilter(b,a,fillingLevel)
    if(plot):
        plt.plot(range(len(fillingLevel)), fillingLevel)
        plt.plot(range(len(filterData)), filterData)
        plt.show()  
    return(filterData[-1])

def myparser(x):
    return datetime.strptime(x, '%b %d, %Y @ %H:%M:%S.%f')

def main3():
    now = datetime.now()
    now= now - timedelta(days=365)
    print(now)
    df = (pd.read_csv("csv/data.csv",  parse_dates=['timestamp'], date_parser=myparser)[lambda x: x['deviceId'] == "2F5B40"])
    print(type(df['timestamp'].iloc[0]))
    print(df['timestamp'].iloc[0])
    dates=df['timestamp'].tolist()
    charges = df['fillingLevel'].tolist()
    print(dates)
    dates.reverse()
    charges.reverse()
    # print(dates[500],"----",dates[2])
    # if(dates[500]>dates[2]):
    #     print("1")


if __name__ == "__main__":
    main3()