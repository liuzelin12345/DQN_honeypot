import pandas as pd
import re

port_count=dict()

def select_port(filename):
    data=pd.read_csv('./requests/'+filename)
    dic=dict()
    for i in range(len(data)):
        try:
            port=re.search(':(.*)',eval(data.iloc[i,1])['Host']).group(1)
        except:
            port='None'
        if port in dic.keys():
            dic[port]=dic[port]+1
        else:
            dic[port]=1
    sorted_dic=sorted(dic.items(),key=lambda x: x[1],reverse=True)
    for i in range(len(sorted_dic)):
        if sorted_dic[i][0] in port_count.keys():
            port_count[sorted_dic[i][0]]= port_count[sorted_dic[i][0]] + sorted_dic[i][1]
        else:
            port_count[sorted_dic[i][0]]=sorted_dic[i][1]


if __name__ == "__main__":
    select_port('普通访问请求.csv')
    select_port('默认规则.csv')
    select_port('海康IPC访问尝试.csv')
    select_port('海康IPC_WEB端登陆尝试.csv')
    select_port('海康旧版设备密码接口扫描.csv')
    select_port('路径爆破行为(攻击).csv')
    select_port('海康IPC权限绕过（抓取视频）(攻击).csv')
    select_port('海康IPC权限绕过(攻击).csv')
    select_port('海康多语言CVE-2021-36260(攻击).csv')
    pop_key_list=[]
    for key in port_count.keys():
        if port_count[key] < 10:
            pop_key_list.append(key)
    for key in pop_key_list:
        port_count.pop(key)
    sorted_port_count=sorted(port_count.items(),key=lambda x: x[1],reverse=True)
    print(sorted_port_count)

#  device selected port: ['8080','8081','9000','84','85','8060','8000','81','8086','83']
#   honeypot selected port: ['82','9000','8009','8060','88','84','8000','8008','8087','8080']
#final selected port: ['80','8080','9000','8081','84','8060','8000','81','8086','83']