import json
import pandas as pd


file = open("Hikvision-data.json", 'r', encoding='utf-8')
data_list = []
ips=[]
count=0
for line in file.readlines():
    dic = json.loads(line)
    data_list.append(dic)
    try:
        a=dict([('ip',dic['ip_str']),('port',dic['port']),('tag',len(dic['tags']))])
    except KeyError:
        a=dict([('ip',dic['ip_str']),('port',dic['port']),('tag','None')])
    ips.append(pd.DataFrame(a,index=[str(count)]))
    count=count+1
file.close()
df=pd.DataFrame()
df=ips[0]
for i in range(1,len(ips)):
    df=df.append(ips[i])
print(df)
df.to_csv('ips.csv')

print(data_list[3].keys())

