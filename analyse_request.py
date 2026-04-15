import pandas as pd
import re

def analyse(filepath):
    df=pd.read_csv('./海康请求数据/'+filepath)
    data=pd.DataFrame(columns=['request'])
    for i in range(df.__len__()):
        req_str=df.iloc[i,0]
        print(i)
        dic=convert(req_str)
        #data[len(data)]=str(dic)
        data = data.append(pd.DataFrame([str(dic)], columns=data.columns,index=[str(i)]))  
    print(data)
    data.to_csv('./requests/'+filepath)
    print("Successfully saved"+filepath)

def convert(req_str):
    dic=dict()
    line_key=['Method','Document']
    header_key=re.findall(r'([a-z,A-Z,-]*):\s',req_str)
    request_line=re.match(r'^[A-Z]{3,4}\s.*\sHTTP/1.[0-9]',req_str).group().split(' ')
    if (header_key != list([])):
        request_header=find_header(req_str,header_key)
    else:
        request_header=[]
    dic['Method']=request_line[0]
    dic['Document']=request_line[1]
    for i in range(len(request_header)):
        dic[header_key[i]]=request_header[i]
    return dic
   

def find_header(req_str,header_key):
    slist=[]
    print(header_key)
    if (len(header_key)>=2):
        for i in range(len(header_key)-1):
            try:
                slist.append(re.search(r'{}:\s(.*)\s{}:'.format(header_key[i],header_key[i+1]),req_str).group(1))
            except:
                slist.append('error')
    try:
        slist.append(re.search(r'{}:\s(.*)'.format(header_key[len(header_key)-1]),req_str).group(1))
    except:
        slist.append('error')
    return slist


if __name__ == "__main__":
    analyse('默认规则.csv')
