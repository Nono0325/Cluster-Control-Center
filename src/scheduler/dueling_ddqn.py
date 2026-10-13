import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
from typing import Tuple, List, Optional

class DuelingQNetwork(nn.Module):
    """
    Dueling Double Deep Q-Network (Dueling DDQN) Architecture:
    Decouples state value V(s) and advantage A(s, a) to enhance
    learning stability and speed in heterogeneous edge scheduling.
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super(DuelingQNetwork, self).__init__()
        
        # Shared feature extractor
        self.feature_network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU()
        )
        
        # State-Value Stream V(s)
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
        # Advantage Stream A(s, a)
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        features = self.feature_network(state)
        values = self.value_stream(features)
        advantages = self.advantage_stream(features)
        
        # Dueling aggregation: Q(s, a) = V(s) + (A(s, a) - mean(A(s, a')))
        q_values = values + (advantages - advantages.mean(dim=-1, keepdim=True))
        return q_values

class ReplayBuffer:
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state: np.ndarray, action: int, reward: float, 
             next_state: np.ndarray, done: bool, mask: np.ndarray):
        self.buffer.append((state, action, reward, next_state, done, mask))

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        state, action, reward, next_state, done, mask = zip(*batch)
        return (
            torch.FloatTensor(np.array(state)),
            torch.LongTensor(action),
            torch.FloatTensor(reward),
            torch.FloatTensor(np.array(next_state)),
            torch.FloatTensor(done),
            torch.FloatTensor(np.array(mask))
        )

    def __len__(self):
        return len(self.buffer)

class DuelingDDQNAgent:
    """
    Dueling DDQN Agent with Action-Masking for SLA & Privacy guarantees.
    """
    def __init__(self, state_dim: int, action_dim: int,
                 lr: float = 1e-3, gamma: float = 0.95,
                 tau: float = 0.005, buffer_capacity: int = 10000):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.tau = tau

        self.policy_net = DuelingQNetwork(state_dim, action_dim)
        self.target_net = DuelingQNetwork(state_dim, action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.buffer = ReplayBuffer(buffer_capacity)
        self.loss_fn = nn.SmoothL1Loss()

    def select_action(self, state: np.ndarray, action_mask: np.ndarray, 
                      epsilon: float = 0.05) -> int:
        """
        Selects action using epsilon-greedy policy with SLA Action Masking.
        Pruned actions are masked to -infinity.
        """
        valid_actions = np.where(action_mask)[0]
        if len(valid_actions) == 0:
            valid_actions = np.array([0]) # Emergency fallback

        if random.random() < epsilon:
            return int(random.choice(valid_actions))

        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            q_values = self.policy_net(state_tensor).squeeze(0).numpy()

        # Apply Action Masking
        masked_q_values = np.copy(q_values)
        masked_q_values[~action_mask] = -1e9

        return int(np.argmax(masked_q_values))

    def update(self, batch_size: int = 32) -> Optional[float]:
        if len(self.buffer) < batch_size:
            return None

        states, actions, rewards, next_states, dones, next_masks = self.buffer.sample(batch_size)

        # 1. Compute current Q values: Q(s, a)
        curr_q = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # 2. Double DQN target computation:
        with torch.no_grad():
            # Policy net selects best action a* on next state (with action masking)
            next_q_policy = self.policy_net(next_states)
            # Mask invalid next actions
            masked_next_q = next_q_policy + (1.0 - next_masks) * -1e9
            best_next_actions = masked_next_q.argmax(dim=1, keepdim=True)
            
            # Target net evaluates value of best_next_actions
            next_q_target = self.target_net(next_states).gather(1, best_next_actions).squeeze(1)
            expected_q = rewards + (1 - dones) * self.gamma * next_q_target

        # 3. Optimize policy network
        loss = self.loss_fn(curr_q, expected_q)
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=5.0)
        self.optimizer.step()

        # 4. Soft update target network (Polyak averaging)
        for target_param, param in zip(self.target_net.parameters(), self.policy_net.parameters()):
            target_param.data.copy_(self.tau * param.data + (1.0 - self.tau) * target_param.data)

        return float(loss.item())
