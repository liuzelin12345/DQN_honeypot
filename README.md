# DQN Honeypot

一个基于强化学习的交互式 HTTP 蜜罐项目。  
系统在接收到攻击/探测请求后，会从预设响应池中选择最优响应，并通过在线学习持续更新策略。

当前版本已将传统 Q-learning 改为 **DQN（Deep Q-Network）**，并在请求到达后引入 **BERT Tokenizer** 处理 HTTP 报文，生成：

- 子词切分结果（tokens）
- 位置编码索引（position ids）
- 掩码向量（attention mask）

其中 `attention mask` 作为 DQN 的状态输入向量。

---

## 功能特性

- 基于多端口监听的蜜罐服务（支持单端口/多端口）
- 基于响应样本库的动作空间（`responses/response_<port>.csv`）
- DQN 在线学习（经验回放 + 目标网络）
- 使用 BERT tokenizer 对请求报文进行编码
- 结合通信轮次与 Snort 告警构造奖励信号
- 自动记录请求日志与交互结果日志

---

## 项目结构

```text
.
├── honeypot.py                 # 入口：启动蜜罐并处理交互
├── Q_learner.py                # DQN智能体 + BERT请求编码
├── ip_scan.py                  # 采集真实设备响应样本
├── select_port.py              # 统计并筛选目标端口
├── requests/                   # 请求样本与接收请求记录
├── responses/                  # 各端口响应池
├── ips/                        # 目标IP及端口数据
├── log_data.csv                # 交互日志
└── Q_table/                    # 历史目录（旧Q表遗留）
```

---

## 运行环境

- Python 3.8+
- Linux（推荐，因依赖 `tcpdump` / `snort`）
- 可选 CUDA（用于 PyTorch 加速）

Python 依赖（建议）：

```bash
pip install pandas numpy torch transformers requests
```

系统工具依赖：

- `tcpdump`（抓包）
- `snort`（告警检测）
- sudo 权限（当前脚本以 `sudo` 调用抓包和 snort）

---

## 快速开始

### 1) 准备数据

- 确保 `requests/received_requests.csv` 存在且格式正确
- 确保目标端口存在对应响应池文件，例如：
  - `responses/response_80.csv`
  - `responses/response_8080.csv`

### 2) 启动蜜罐

```bash
python honeypot.py 80
```

或监听预设全部端口：

```bash
python honeypot.py all
```

---

## 核心流程（DQN + BERT）

1. 蜜罐收到 HTTP 请求报文（bytes）
2. 使用 `BertTokenizerFast` 进行编码：
   - tokenization（子词切分）
   - 生成 `position_ids`
   - 生成 `attention_mask`
3. 将 `attention_mask` 作为状态输入 DQN 网络
4. DQN 按 epsilon-greedy 选择响应动作
5. 发送响应并接收下一状态（下一条请求或连接结束）
6. 根据通信轮次与 snort 告警计算 reward
7. 存储 transition 并执行一次训练（经验回放）
8. 定期同步目标网络参数

---

## 数据与日志说明

- `requests/received_requests.csv`
  - 记录接收到的请求（请求ID、来源地址、原始报文、时间）
- `log_data.csv`
  - 记录每次会话交互统计（通信次数、告警状态、动作编号等）




