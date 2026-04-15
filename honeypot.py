import socket
import random
import pandas as pd
from datetime import datetime
import sys
import time
import subprocess as sub
from threading import Thread
import signal
import os
from Q_learner import *

port_list=['80','81','82','88','443','7547','8080','8081','9999']
count=0

def load_data(filename):
    df=pd.read_csv(filename)
    return df

def store_request(request_data,req_id,addr,msg_recived):
    now = datetime.now()
    df1=pd.DataFrame([[req_id,str(addr[0]),msg_recived,now]],columns=['req_id','addr','request','time'])
    request_data=request_data.append(df1)
    print(df1)
    request_data.to_csv('requests/received_requests.csv',index=False)
    print("Request_stored")
    return request_data

def random_response(socket):
    res='<HTML><HEAD><TITLE>File Not Found</TITLE></HEAD>\r\n<BODY><H1>File Not Found</H1>\r\n</BODY></HTML>'
    socket.send(res.encode("utf-8"))
    print('Random response sended\n')

def best_response(request_data,port, socket,pcap_path,received_requests):
    global count
    count=count+1
    communication_count=1
    next_state= 'empty'
    current_state = request_data
    while next_state != 'end connection':
        Q_table=load_Q_table(current_state,port)
        action_id=select_action(Q_table,current_state)
        if hasattr(Q_table, "latest_encoded"):
            encoded = Q_table.latest_encoded
            print("BERT encoded request:",
                  "tokens=", encoded["tokens"][:12],
                  "position_ids=", encoded["position_ids"][:12].tolist(),
                  "mask=", encoded["attention_mask"][:12].tolist())
        send_response(port,socket,action_id)
        next_state,communication_count,Alert=update_Q_table(Q_table,socket,port,action_id,current_state,communication_count,pcap_path,addr,received_requests)
        if next_state != 'end connection':
            current_state = next_state
    # log_data=pd.DataFrame(columns=['addr','communication count'])
    log_data=pd.read_csv('log_data.csv')
    log_data=log_data.append(pd.DataFrame(columns=log_data.columns,data=[(str(count),str(addr),str(communication_count),str(Alert),str(action_id))]))
    log_data.to_csv('log_data.csv',index=False)
    print('save to log_data.csv:',len(log_data))

#强制退出
def exit(a,b):
    global port          
    print("\nProgram interrupted, storing data and exiting(error).")
    s.close()
    request_data.to_csv('requests/port_' + 'all'+ '_requests.csv',index=False)
    os._exit(1)


#启动密罐
def start_honeypot(port):
    interrupt = False 
    randomResponse = False
    bestResponse = True
    try:
        global s,request_data
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', int(port)))
        s.listen(5)
        request_data = load_data('requests/received_requests.csv')
        print("----------Server started for port " + str(port)+"----------\n")
        try:
            while True:
                #数据抓包
                req_id  = 'req_' + str(len(request_data)+1)+'_p'+str(port)
                pcap_path = "/home/liuzelin/honeypot/pcap/port_" + str(port) + "_pcap/" + req_id + ".pcap"
                p = sub.Popen(("sudo", "tcpdump", "port", str(port), "and", "tcp[tcpflags] == tcp-syn","-Q", "in", "-w", pcap_path, "-Z", "root"), stdout=sub.PIPE)
                #接收请求
                global addr
                c, addr = s.accept()
                c.settimeout(10.0)
                print('----------Got connection from' + str(addr) + '----------\n')
                msg_recived = c.recv(65565) 
                print("Request received")
                request_data=store_request(request_data,req_id,addr,msg_recived)
                #发送响应
                #response_data=load_data("responses/port_" + str(port) + "_responses.csv")
                if randomResponse:
                    random_response(c)
                if bestResponse:
                    best_response(msg_recived,port,c,pcap_path,request_data)
                
                c.close()
                p.terminate()
                print('----------End of Connection----------\n')
        except KeyboardInterrupt:
            print("\nProgram interrupted, storing data and exiting.")
            s.close()
            interrupt = True
            request_data.to_csv('requests/received_requests.csv',index=False)
    except:
        if interrupt:
            sys.exit(1)
        else:
            print("Error with honeypot at port " + str(port))
            time.sleep(50)
            start_honeypot(port)

#选择端口
def port_selection(port):
    if port in port_list:
        start_honeypot(port)
    elif port == 'all':
        for p in port_list:
            t = Thread(target=start_honeypot, args=(p,))
            t.start()
    else:
        print("Error: The port is invalid.")
        sys.exit(1)

#主函数
def main():
    port = str(sys.argv[1])
    port_selection(port)

if __name__ == "__main__":
    main()
    #捕获中断信号
    signal.signal(signal.SIGINT,exit)




