from collections import deque
import random
import subprocess as sub

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from transformers import BertTokenizerFast

# DQN超参数
MAX_SEQ_LEN = 128
BUFFER_SIZE = 5000
BATCH_SIZE = 64
GAMMA = 0.9
LEARNING_RATE = 1e-3
TARGET_UPDATE_FREQ = 20
EPSILON_START = 1.0
EPSILON_END = 0.1
EPSILON_DECAY = 0.995


class DQNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
        )

    def forward(self, x):
        return self.model(x)


class DQNAgent:
    def __init__(self, action_dim):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.state_dim = MAX_SEQ_LEN
        self.action_dim = action_dim

        self.policy_net = DQNetwork(self.state_dim, action_dim).to(self.device)
        self.target_net = DQNetwork(self.state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=LEARNING_RATE)
        self.criterion = nn.SmoothL1Loss()
        self.memory = deque(maxlen=BUFFER_SIZE)
        self.learn_step = 0
        self.epsilon = EPSILON_START

    def select_action(self, state_mask):
        if np.random.rand() < self.epsilon:
            return random.randrange(self.action_dim)

        state_tensor = torch.FloatTensor(state_mask).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.policy_net(state_tensor)
        return int(torch.argmax(q_values, dim=1).item())

    def store_transition(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_step(self):
        if len(self.memory) < BATCH_SIZE:
            return

        batch = random.sample(self.memory, BATCH_SIZE)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.device)

        q_values = self.policy_net(states).gather(1, actions)
        with torch.no_grad():
            max_next_q_values = self.target_net(next_states).max(1, keepdim=True)[0]
            q_targets = rewards + (1 - dones) * GAMMA * max_next_q_values

        loss = self.criterion(q_values, q_targets)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.learn_step += 1
        if self.learn_step % TARGET_UPDATE_FREQ == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        self.epsilon = max(EPSILON_END, self.epsilon * EPSILON_DECAY)


class BertRequestEncoder:
    def __init__(self):
        self.tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")

    def encode_request(self, request_data):
        if isinstance(request_data, bytes):
            text = request_data.decode("utf-8", errors="ignore")
        else:
            text = str(request_data)

        encoded = self.tokenizer(
            text,
            max_length=MAX_SEQ_LEN,
            truncation=True,
            padding="max_length",
            return_attention_mask=True,
            return_tensors="np",
        )

        input_ids = encoded["input_ids"][0]
        attention_mask = encoded["attention_mask"][0]
        token_list = self.tokenizer.convert_ids_to_tokens(input_ids.tolist())
        position_ids = np.arange(MAX_SEQ_LEN, dtype=np.int64)

        return {
            "tokens": token_list,  # 子词切分结果
            "position_ids": position_ids,  # 位置编码索引
            "attention_mask": attention_mask.astype(np.float32),  # 掩码向量（DQN状态）
        }


class DQNContext:
    def __init__(self, port):
        response_data = pd.read_csv(f"./responses/response_{port}.csv")
        action_dim = len(response_data)
        if action_dim <= 0:
            raise ValueError(f"responses/response_{port}.csv 中没有可用动作。")

        self.port = port
        self.response_data = response_data
        self.agent = DQNAgent(action_dim=action_dim)
        self.encoder = BertRequestEncoder()


_DQN_CONTEXTS = {}


def _get_context(port):
    port = str(port)
    if port not in _DQN_CONTEXTS:
        _DQN_CONTEXTS[port] = DQNContext(port=port)
    return _DQN_CONTEXTS[port]


def _mask_from_request(request_data, port):
    context = _get_context(port)
    encoded = context.encoder.encode_request(request_data)
    return encoded["attention_mask"], encoded


# 兼容原接口：返回上下文对象
def load_Q_table(request_data, port):
    _ = request_data
    return _get_context(port)


def select_action(Q_table, request_data):
    context = Q_table
    state_mask, encoded = _mask_from_request(request_data, context.port)
    context.latest_state_mask = state_mask
    context.latest_encoded = encoded
    return context.agent.select_action(state_mask)


def send_response(port, socket, action_id):
    context = _get_context(port)
    res = str(context.response_data.iloc[int(action_id), 1])
    socket.send(res.encode("utf-8"))
    print("Best response sended\n")


def update_Q_table(Q_table, socket, port, action_id, request_data, communication_count, pcap_path, addr, received_requests):
    context = Q_table
    state_mask, _ = _mask_from_request(request_data, port)
    next_state, communication_count = check_next_state(socket, communication_count, addr, received_requests)
    done = next_state == "end connection"

    if done:
        next_state_mask = np.zeros(MAX_SEQ_LEN, dtype=np.float32)
    else:
        next_state_mask, _ = _mask_from_request(next_state, port)

    r, alert = reward(next_state, communication_count, pcap_path)

    context.agent.store_transition(state_mask, int(action_id), float(r), next_state_mask, float(done))
    context.agent.train_step()
    print("DQN model updated")
    return next_state, communication_count, alert


def check_next_state(socket, communication_count, addr, received_requests):
    try:
        msg_recived = socket.recv(65565)
    except Exception:
        msg_recived = "end connection"
    if msg_recived == b"":
        msg_recived = "end connection"
    if msg_recived != "end connection":
        communication_count = communication_count + 1
    num = -1  # 考虑自身
    for i in list(received_requests.loc[:, "addr"]):
        if str(addr[0]) == i:
            num = num + 1
    communication_count = communication_count + num
    return msg_recived, communication_count


def reward(next_state, communication_count, pcap_path):
    r = 0.0
    alert = "False"
    if next_state != "end connection":
        if communication_count == 2:
            r += 0.1
        if communication_count == 3:
            r += 0.15
        if communication_count == 4:
            r += 0.2
        snort_conf_path = "/etc/snort/snort.conf"
        p = sub.Popen(
            ("sudo", "snort", "-c", str(snort_conf_path), "-A", "console", "-q", "-r", str(pcap_path)),
            stdout=sub.PIPE,
        )
        for _ in p.stdout:
            alert = "True"
        if alert == "True":
            r += 0.3
            print("Alert found\n")
    else:
        if communication_count == 2:
            r -= 0.1
        if communication_count == 3:
            r -= 0.08
        if communication_count == 4:
            r -= 0.05
    return r, alert


