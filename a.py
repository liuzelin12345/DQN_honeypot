import requests
import json
import pandas as pd
import re
import numpy as np
import socket



# slist=['state']
# for i in range(65):
#     slist.append(str(i))

# data=pd.DataFrame(columns=slist)
# data.to_csv('Q_table_80.csv',index=False)

# d=['a']
# for i in list(np.random.random(len(list(Q_table.columns))-1)):
#     d.append(i)
# d=tuple(d)
# Q_table=Q_table.append(pd.DataFrame(columns=Q_table.columns,data=[d])
# Q_table.to_csv('Q_table_80.csv',index=False)

Q_table=pd.read_csv('Q_table_80.csv')
print(len(Q_table))
a=tuple((1,2))
print(a)
print(a[0])