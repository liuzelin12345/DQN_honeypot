import pandas as pd


name_list=['普通访问请求','默认规则','海康IPC访问尝试','海康IPC_WEB端登陆尝试','海康旧版设备密码接口扫描','路径爆破行为(攻击)','海康多语言CVE-2021-36260(攻击)','海康IPC权限绕过(攻击)','海康IPC权限绕过（抓取视频）(攻击)']
port_list=['80','8080','9000','84','8000','81','83']
for port in port_list:
    res=pd.DataFrame(columns=['addr','response'])
    for name in name_list:
        data=pd.read_csv('./'+name+'/response_'+port+'.csv')
        res=res.append(data)
    res_list=list(res.loc[:,'response'])
    res_list=list(set(res_list))
    response_data=pd.DataFrame(columns=['response'])
    response_data.loc[:,'response']=pd.Series(res_list)
    response_data.to_csv('response_'+port+'.csv')

