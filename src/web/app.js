/* ==========================================================================
   NonoAI: Heterogeneous Personal AI Cluster Control Center - Client Logic
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  loadClusterNodes();
  loadBenchmarkSummary();
});

// ----------------- Tab Navigation -----------------
function switchTab(tabKey) {
  document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

  const targetBtn = document.getElementById(`tab-btn-${tabKey}`);
  const targetContent = document.getElementById(`tab-content-${tabKey}`);

  if (targetBtn && targetContent) {
    targetBtn.classList.add("active");
    targetContent.classList.add("active");
  }
}

// ----------------- Slider Val Updaters -----------------
function updateTokenVals() {
  document.getElementById("val-input-tokens").innerText = document.getElementById("range-in-tokens").value;
  document.getElementById("val-output-tokens").innerText = document.getElementById("range-out-tokens").value;
}

function updateDeadlineVal() {
  const val = document.getElementById("range-deadline").value;
  document.getElementById("val-deadline").innerText = Number(val).toLocaleString() + " ms";
}

// ----------------- Cluster Nodes API -----------------
async function loadClusterNodes() {
  const container = document.getElementById("nodes-container");
  try {
    const res = await fetch("/api/cluster/nodes");
    const data = await res.json();
    renderNodeCards(data.nodes);
    
    const onlineCount = data.nodes.filter(n => n.is_online).length;
    document.getElementById("header-node-count-text").innerText = `${onlineCount} / ${data.total_nodes} 個節點連線中`;
  } catch (err) {
    console.error("載入叢集節點失敗:", err);
    container.innerHTML = `<div class="error-msg">無法連接叢集 API：${err.message}</div>`;
  }
}

function renderNodeCards(nodes) {
  const container = document.getElementById("nodes-container");
  container.innerHTML = "";

  nodes.forEach(node => {
    const isOnline = node.is_online;
    const isLocal = node.is_local;
    const vramPercent = Math.min(100, Math.round((node.used_vram_gb / node.total_vram_gb) * 100));

    const card = document.createElement("div");
    card.className = `glass-card node-card ${isLocal ? 'plane-local' : 'plane-cloud'} ${isOnline ? '' : 'offline'}`;
    card.id = `card-${node.node_id}`;

    card.innerHTML = `
      <div class="node-top">
        <div class="node-title-group">
          <h3>${node.name}</h3>
          <span class="node-sub">${isLocal ? '本地推理平面 (LAN 區域網)' : '隱私授權外部平面 (雲端)'}</span>
        </div>
        <button class="node-toggle-btn" onclick="toggleNode('${node.node_id}')">
          ${isOnline ? '🟢 在線中' : '🔴 離線中'}
        </button>
      </div>

      <div class="vram-meter-box">
        <div class="meter-header">
          <span>視訊記憶體佔用: ${node.used_vram_gb} / ${node.total_vram_gb} GB</span>
          <span><strong>${vramPercent}%</strong></span>
        </div>
        <div class="meter-bar-track">
          <div class="meter-bar-fill" style="width: ${vramPercent}%"></div>
        </div>
      </div>

      <div class="node-stats-grid">
        <div class="stat-pill">
          <span class="stat-lbl">運算能力</span>
          <span class="stat-val">${node.compute_tflops} TFLOPS</span>
        </div>
        <div class="stat-pill">
          <span class="stat-lbl">網路 RTT 時延</span>
          <span class="stat-val">${node.base_latency_ms} ms</span>
        </div>
        <div class="stat-pill">
          <span class="stat-lbl">佇列待處理任務</span>
          <span class="stat-val">${node.active_tasks_count} 個 (${node.queue_delay_ms} ms)</span>
        </div>
        <div class="stat-pill">
          <span class="stat-lbl">動態 KV-Cache 預估</span>
          <span class="stat-val">${node.sample_kv_cache_gb} GB</span>
        </div>
      </div>

      <div class="node-tags">
        ${node.cached_models.map(m => `<span class="model-tag">快取: ${m}</span>`).join('')}
      </div>
    `;

    container.appendChild(card);
  });
}

async function toggleNode(nodeId) {
  try {
    const res = await fetch(`/api/cluster/nodes/${nodeId}/toggle`, { method: "POST" });
    const data = await res.json();
    loadClusterNodes();
  } catch (err) {
    alert("切換節點失敗: " + err.message);
  }
}

// ----------------- Interactive Inference Scheduler -----------------
async function executeScheduleInference() {
  const submitBtn = document.getElementById("btn-submit-inference");
  submitBtn.disabled = true;
  submitBtn.innerHTML = "排程運算中...";

  const prompt = document.getElementById("input-prompt").value;
  const taskType = document.getElementById("select-task-type").value;
  const modelName = document.getElementById("select-model").value;
  const inTokens = parseInt(document.getElementById("range-in-tokens").value, 10);
  const outTokens = parseInt(document.getElementById("range-out-tokens").value, 10);
  const deadline = parseFloat(document.getElementById("range-deadline").value);
  
  const privSelected = document.querySelector('input[name="privacy-level"]:checked');
  const privacyLevel = privSelected ? parseInt(privSelected.value, 10) : 1;

  let modelSize = 5.2;
  if (modelName.includes("1B")) modelSize = 1.2;
  else if (modelName.includes("70B")) modelSize = 40.0;
  else if (modelName === "YOLOv8n") modelSize = 0.05;
  else if (modelName === "YOLOv8x") modelSize = 0.50;

  const payload = {
    task_type: taskType,
    model_name: modelName,
    model_size_gb: modelSize,
    input_tokens: inTokens,
    output_tokens: outTokens,
    privacy_level: privacyLevel,
    deadline_ms: deadline,
    raw_prompt: prompt,
    sensitive_entities: ["user_id_8821", "medical_record"]
  };

  try {
    const res = await fetch("/api/inference/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    renderInferenceResult(result);
    loadClusterNodes(); // Refresh queue and VRAM states
  } catch (err) {
    alert("排程推論失敗: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<span class="btn-icon">⚡</span> 啟動 Dueling DDQN 智慧排程與推論';
  }
}

function renderInferenceResult(res) {
  document.getElementById("result-placeholder").classList.add("hidden");
  const activeContainer = document.getElementById("result-active-container");
  activeContainer.classList.remove("hidden");

  // Summary Banner
  document.getElementById("res-node-name").innerText = res.chosen_node;
  document.getElementById("res-node-type").innerText = res.is_local ? "本地推理平面 (LAN 區域網)" : "隱私授權外部平面 (雲端)";
  
  const modeLabels = {
    "PURE_CLOUD": "完全雲端推論",
    "CLOUD_EDGE_COLLABORATIVE_LDP": "雲邊語義協同推論 (雙層 LDP)",
    "CLOUD_EDGE_SPECULATIVE": "雲邊推測解碼協同 (Speculative)",
    "PURE_LOCAL_EDGE": "完全本地邊緣推論"
  };
  document.getElementById("res-exec-mode").innerText = modeLabels[res.execution_mode] || res.execution_mode;
  document.getElementById("res-latency").innerText = `${res.latency_ms} ms`;
  
  const slaText = res.is_sla_met ? "✔ SLA 期限達標" : "❌ SLA 期限逾期";
  document.getElementById("res-sla-status").innerText = slaText;
  document.getElementById("res-sla-status").className = res.is_sla_met ? "metric-sub text-success" : "metric-sub text-danger";
  document.getElementById("res-kv-cache").innerText = `KV-Cache: ${res.kv_cache_vram_gb} GB`;

  // Two-Layer LDP Box
  const ldpBox = document.getElementById("ldp-details-box");
  if (res.ldp_details && Object.keys(res.ldp_details).length > 0) {
    ldpBox.classList.remove("hidden");
    document.getElementById("ldp-step1-text").innerText = `已辨識敏感標籤並置換為安全佔位符：${Object.keys(res.ldp_details.private_vault).join(', ')}`;
    document.getElementById("ldp-step2-text").innerText = res.ldp_details.semantic_sketch;
    document.getElementById("ldp-step3-text").innerText = res.ldp_details.cloud_skeleton_response;
    document.getElementById("ldp-step4-text").innerText = `本地私有保險庫精確回填結果：${res.ldp_details.final_reconstructed_response}`;
  } else {
    ldpBox.classList.add("hidden");
  }

  // Latency Breakdown Bars
  const tTotal = Math.max(1, res.latency_ms);
  const c = res.components;
  
  const pQueue = Math.min(100, Math.round((c.t_queue_ms / tTotal) * 100));
  const pLoad = Math.min(100, Math.round((c.t_load_ms / tTotal) * 100));
  const pTrans = Math.min(100, Math.round((c.t_trans_ms / tTotal) * 100));
  const pExec = Math.min(100, Math.round((c.t_exec_ms / tTotal) * 100));

  document.getElementById("bar-queue").style.width = `${pQueue}%`;
  document.getElementById("val-tqueue").innerText = `${c.t_queue_ms} ms (${pQueue}%)`;

  document.getElementById("bar-load").style.width = `${pLoad}%`;
  document.getElementById("val-tload").innerText = c.t_load_ms === 0 ? "0.0 ms (快取命中)" : `${c.t_load_ms} ms (${pLoad}%)`;

  document.getElementById("bar-trans").style.width = `${pTrans}%`;
  document.getElementById("val-ttrans").innerText = `${c.t_trans_ms} ms (${pTrans}%)`;

  document.getElementById("bar-exec").style.width = `${pExec}%`;
  document.getElementById("val-texec").innerText = `${c.t_exec_ms} ms (${pExec}%)`;

  // Action Masking Candidates Table
  const tbody = document.getElementById("action-mask-tbody");
  tbody.innerHTML = "";
  res.action_mask_details.forEach(item => {
    const tr = document.createElement("tr");
    if (item.name === res.chosen_node) {
      tr.className = "highlight-row";
    }

    const slaStatusBadge = item.sla_violates 
      ? '<span class="badge badge-danger">逾期違規 (Masked)</span>' 
      : '<span class="badge badge-success">符合時限</span>';

    const privacyBadge = item.privacy_violates 
      ? '<span class="badge badge-danger">機密越界攔截 (Masked)</span>' 
      : '<span class="badge badge-success">授權合規</span>';

    const actionBadge = item.is_valid 
      ? '<span class="badge badge-success">保留候選 (Q值有效)</span>' 
      : '<span class="badge badge-danger">動作遮罩剪除 (Q = -10^9)</span>';

    tr.innerHTML = `
      <td><strong>${item.name}</strong></td>
      <td>${item.estimated_latency_ms} ms</td>
      <td>${item.deadline_ms} ms</td>
      <td>${slaStatusBadge}</td>
      <td>${privacyBadge}</td>
      <td>${actionBadge}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------- Benchmark Gallery & Lightbox -----------------
async function loadBenchmarkSummary() {
  try {
    const res = await fetch("/api/benchmarks/summary");
    const data = await res.json();
    renderFiguresGallery(data.figures);
  } catch (err) {
    console.error("載入實驗圖表失敗:", err);
  }
}

function renderFiguresGallery(figures) {
  const container = document.getElementById("figures-gallery-container");
  container.innerHTML = "";

  figures.forEach(fig => {
    const card = document.createElement("div");
    card.className = "glass-card figure-card";
    card.onclick = () => openLightbox(fig.url, fig.title);

    card.innerHTML = `
      <div class="figure-img-wrap">
        <img src="${fig.url}" alt="${fig.title}" loading="lazy">
      </div>
      <div class="figure-caption">${fig.title}</div>
    `;

    container.appendChild(card);
  });
}

function openLightbox(url, caption) {
  const modal = document.getElementById("image-lightbox");
  document.getElementById("lightbox-img").src = url;
  document.getElementById("lightbox-caption").innerText = caption;
  modal.classList.remove("hidden");
}

function closeLightbox() {
  document.getElementById("image-lightbox").classList.add("hidden");
}

// ----------------- Document Rebuild & Download -----------------
async function recompileWordDoc() {
  try {
    const res = await fetch("/api/plan/rebuild", { method: "POST" });
    const data = await res.json();
    alert(`Word 計畫書重新編譯完成！檔案大小：${(data.file_size_bytes / 1024 / 1024).toFixed(2)} MB`);
  } catch (err) {
    alert("編譯失敗: " + err.message);
  }
}

function downloadWordPlan() {
  window.open("/api/plan/download", "_blank");
}
