import pandas as pd

slist=['state']
for i in range(65):
    slist.append(str(i))

data=pd.DataFrame(columns=slist)
data.to_csv('Q_table_80.csv',index=False)