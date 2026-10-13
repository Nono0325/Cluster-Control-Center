import numpy as np
from typing import Dict, List, Any
from ..cluster.registry import CapabilityRegistry
from ..workload.request import InferenceRequest
from ..workload.generator import WorkloadGenerator
from ..scheduler.environment import ClusterSchedulingEnv
from ..scheduler.dueling_ddqn import DuelingDDQNAgent
from ..scheduler.baselines import (
    HomogeneousMeanSlotScheduler,
    StaticBinaryRouter,
    GreedyEarliestDeadlineScheduler
)

class BenchmarkEvaluator:
    """
    Comprehensive experimental evaluation suite:
    - Compares Proposed Dueling DDQN with Baselines
    - Measures TTFT, TPOT, P50/P95 Latency, SLA Miss Rate, Privacy Breaches
    - Executes Ablation Studies (w/o Action Masking)
    - Executes Outage Test (WAN Network Disconnection)
    """
    def __init__(self, num_requests: int = 300, seed: int = 42):
        self.num_requests = num_requests
        self.seed = seed
        self.generator = WorkloadGenerator(seed=seed)
        self.workload = self.generator.generate_trace(num_requests=num_requests)

    def train_ddqn_agent(self, env: ClusterSchedulingEnv, episodes: int = 15) -> DuelingDDQNAgent:
        """Trains the Dueling DDQN agent on representative workload batches."""
        agent = DuelingDDQNAgent(state_dim=env.state_dim, action_dim=env.action_dim)
        
        train_trace = self.generator.generate_trace(num_requests=150)
        epsilon = 0.4
        epsilon_decay = 0.95
        min_epsilon = 0.02

        print(f"[*] Training Dueling DDQN Agent ({episodes} episodes)...")
        for ep in range(episodes):
            env.reset()
            total_reward = 0.0
            for req in train_trace:
                state = env.get_state_vector(req)
                mask = env.action_masker.generate_mask(req, env.nodes)
                action = agent.select_action(state, mask, epsilon=epsilon)
                next_state, reward, done, info = env.step(req, action)
                next_mask = env.action_masker.generate_mask(req, env.nodes)
                agent.buffer.push(state, action, reward, next_state, done, next_mask)
                agent.update(batch_size=32)
                total_reward += reward

            epsilon = max(min_epsilon, epsilon * epsilon_decay)
        
        print("[*] Training completed.")
        return agent

    def evaluate_scheduler(self, scheduler_name: str, scheduler_fn) -> Dict[str, Any]:
        """Runs the benchmark trace on a specific scheduler policy."""
        env = ClusterSchedulingEnv()
        env.reset()

        latencies = []
        ttfts = []
        tpots = []
        deadline_misses = 0
        privacy_violations = 0
        costs = []

        for req in self.workload:
            state = env.get_state_vector(req)
            action = scheduler_fn(env, req, state)
            _, reward, _, info = env.step(req, action)

            latencies.append(info["latency_ms"])
            ttfts.append(info["ttft_ms"])
            tpots.append(info["tpot_ms"])
            costs.append(info["resource_cost"])

            if info["deadline_miss"]:
                deadline_misses += 1
            if info["privacy_violated"]:
                privacy_violations += 1

        total = len(self.workload)
        return {
            "name": scheduler_name,
            "total_requests": total,
            "ttft_mean": float(np.mean(ttfts)),
            "tpot_mean": float(np.mean(tpots)),
            "latency_p50": float(np.percentile(latencies, 50)),
            "latency_p95": float(np.percentile(latencies, 95)),
            "latency_mean": float(np.mean(latencies)),
            "deadline_miss_rate": float((deadline_misses / total) * 100.0),
            "privacy_violation_rate": float((privacy_violations / total) * 100.0),
            "avg_cost": float(np.mean(costs)),
            "raw_latencies": latencies
        }

    def run_full_suite(self) -> Dict[str, Dict[str, Any]]:
        """Executes full evaluation comparing all methods."""
        env = ClusterSchedulingEnv()
        trained_agent = self.train_ddqn_agent(env)

        # 1. Proposed Method: Dueling DDQN + SLA Action Masking
        def policy_ddqn(env_inst, req, state):
            mask = env_inst.action_masker.generate_mask(req, env_inst.nodes)
            return trained_agent.select_action(state, mask, epsilon=0.0)

        # 2. Ablation: Dueling DDQN WITHOUT Action Masking
        def policy_no_mask(env_inst, req, state):
            all_true_mask = np.ones(env_inst.num_nodes, dtype=bool)
            return trained_agent.select_action(state, all_true_mask, epsilon=0.0)

        # 3. Greedy Shortest Latency
        greedy = GreedyEarliestDeadlineScheduler()
        def policy_greedy(env_inst, req, state):
            return greedy.select_node(req, env_inst.nodes)

        # 4. Homogeneous Mean Slot (Traditional LAS)
        mean_slot = HomogeneousMeanSlotScheduler()
        def policy_mean_slot(env_inst, req, state):
            return mean_slot.select_node(req, env_inst.nodes)

        # 5. Static Binary Router
        binary_router = StaticBinaryRouter()
        def policy_binary(env_inst, req, state):
            return binary_router.select_node(req, env_inst.nodes)

        results = {}
        print("[*] Evaluating Proposed Dueling DDQN (w/ SLA Masking)...")
        results["Proposed_Dueling_DDQN"] = self.evaluate_scheduler("Proposed (Dueling DDQN + SLA Masking)", policy_ddqn)

        print("[*] Evaluating Ablation: DDQN without Action Masking...")
        results["Ablation_No_Masking"] = self.evaluate_scheduler("Ablation (w/o SLA Action Masking)", policy_no_mask)

        print("[*] Evaluating Baseline: Greedy Latency...")
        results["Greedy_Latency"] = self.evaluate_scheduler("Greedy Earliest Latency", policy_greedy)

        print("[*] Evaluating Baseline: Homogeneous Mean Slot...")
        results["Homogeneous_Mean_Slot"] = self.evaluate_scheduler("Homogeneous Mean Slot (LAS)", policy_mean_slot)

        print("[*] Evaluating Baseline: Static Binary Router...")
        results["Static_Binary_Router"] = self.evaluate_scheduler("Static Binary Router", policy_binary)

        return results

    def run_outage_test(self) -> Dict[str, Any]:
        """
        Executes Network Outage Test (斷線與容錯測試):
        Simulates sudden WAN cloud disconnect at request #50 to verify
        the 'Never Silently Leak' privacy and fail-safe scheduling guarantee.
        """
        print("[*] Running WAN Network Outage & Fail-Safe Test...")
        env = ClusterSchedulingEnv()
        agent = self.train_ddqn_agent(env, episodes=5)
        
        test_requests = self.workload[:120]
        outage_at_req = 40
        recovered_at_req = 90

        latencies = []
        privacy_violations = 0
        local_dispatches = 0

        for idx, req in enumerate(test_requests):
            # Inject cloud disconnect event
            if outage_at_req <= idx < recovered_at_req:
                cloud_node = env.registry.get_node("node_cloud")
                if cloud_node:
                    cloud_node.is_online = False
            else:
                cloud_node = env.registry.get_node("node_cloud")
                if cloud_node:
                    cloud_node.is_online = True

            state = env.get_state_vector(req)
            mask = env.action_masker.generate_mask(req, env.nodes)
            action = agent.select_action(state, mask, epsilon=0.0)
            _, _, _, info = env.step(req, action)

            latencies.append(info["latency_ms"])
            if info["is_local"]:
                local_dispatches += 1
            if info["privacy_violated"]:
                privacy_violations += 1

        outage_period_requests = recovered_at_req - outage_at_req
        return {
            "total_tested": len(test_requests),
            "outage_duration_requests": outage_period_requests,
            "privacy_violations": privacy_violations,
            "privacy_leak_rate_percent": (privacy_violations / len(test_requests)) * 100.0,
            "fallback_success_rate": 100.0 if privacy_violations == 0 else 0.0,
            "local_dispatch_ratio": (local_dispatches / len(test_requests)) * 100.0
        }
