import requests
import pandas as pd
import os
import signal
import re

#allowed_ports = ['80','8080','9000','8081','84','8060','8000','81','8086','83']
allowed_ports = ['80','8080','9000','84','8000','81','83']

def load_ip(filepath):
    data=pd.read_csv(filepath)
    data=ip_filter(data)
    return data

def ip_filter (data):
    list=[]
    for i in range(len(data)):
        if str(data.iloc[i,2]) not in allowed_ports:
            list.append(i)
    data=data.drop(list)
    return data
        
def load_request(filepath):
    data=pd.read_csv(filepath)
    return data

def scan(filename,ip_data,request_data):
    try:
        response_list=[]
        for port in allowed_ports:
            global df,i
            df=pd.DataFrame(columns=['addr','response'])
            for i in range(len(ip_data)):
                if str(ip_data.iloc[i,2]) == port:
                    for j in range(int(len(request_data)/10)):
                        print(str('port:'+port+str()+' ip:{}/{}'+' request:{}/{}').format(i,len(ip_data),j,int(len(request_data)/10)),end='\r')
                        req=eval(request_data.iloc[j,1])
                        method=req['Method']
                        url='http://'+str(ip_data.iloc[i,1])+':'+str(ip_data.iloc[i,2])+req['Document']
                        req.pop('Method',None)
                        req.pop('Document',None)
                        req['Host']=str(ip_data.iloc[i,1])+':'+str(ip_data.iloc[i,2])
                        header=req
                        try:
                            if method == 'GET':
                                response=requests.get(url=url,headers=header,timeout=3)

                            elif method == 'POST':
                                key_list= list(header.keys())
                                str1=header[key_list[len(key_list)-1]]
                                try:
                                    header[key_list[len(key_list)-1]]=re.search(r'(.*)\s\s(.*)',str1).group(1)
                                    body=re.search(r'(.*)\s\s(.*)',str1).group(2)
                                    response=requests.post(url=url,headers=header,data=body,timeout=3)
                                except:
                                    response=requests.post(url=url,headers=header,timeout=3)

                            elif method == 'HEAD':
                                    response=requests.head(url=url,headers=header,timeout=3)

                            elif method == 'PUT':
                                key_list= list(header.keys())
                                str2=header[key_list[len(key_list)-1]]
                                try:
                                    header[key_list[len(key_list)-1]]=re.search(r'(.*)\s\s(.*)',str2).group(1)
                                    body=re.search(r'(.*)\s\s(.*)',str2).group(2)
                                    response=requests.put(url=url,headers=header,data=body,timeout=3)
                                except:
                                    response=requests.put(url=url,headers=header,timeout=3)

                            df = df.append(pd.DataFrame([(str(ip_data.iloc[i,1])+':'+str(ip_data.iloc[i,2]),response.text)], columns=df.columns,index=[str(j)])) 
                        except:
                            df = df.append(pd.DataFrame([(str(ip_data.iloc[i,1])+':'+str(ip_data.iloc[i,2]),'Connection refused')], columns=df.columns,index=[str(j)]))
            df.to_csv('./responses/{}/response_{}.csv'.format(filename,port))
            print('\n')
            print('data saved: /{}/response_{}.csv'.format(filename,port))
            response_list.append(df)
    except KeyboardInterrupt:
        df.to_csv('./responses/response_{}.csv'.format(i))
        print('ending...')
        os._exit(1)

def scan_all_port(filename):
    ip_data=load_ip('./ips/ips_selected_1.csv')
    request_data=load_request('./requests/'+filename+'.csv')
    scan(filename,ip_data,request_data)


def exit():
    df.to_csv('./responses/response{}.csv'.format(i))
    print('ending...')
    os._exit(1)

if __name__ == "__main__":
    # scan_all_port('普通访问请求')
    # scan_all_port('海康IPC访问尝试')
    # scan_all_port('海康旧版设备密码接口扫描')
    # scan_all_port('海康IPC_WEB端登陆尝试')    
    # scan_all_port('默认规则')
    scan_all_port('海康IPC权限绕过（抓取视频）(攻击)')
    scan_all_port('路径爆破行为(攻击)')
    scan_all_port('海康IPC权限绕过(攻击)')
    scan_all_port('海康多语言CVE-2021-36260(攻击)')
    signal.signal(signal.SIGINT,exit)

