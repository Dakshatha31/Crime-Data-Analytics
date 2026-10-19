/**
 * Main Application Logic & Event Handlers
 */
let currentAreas = [];

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  setupTabs();
  loadOverviewKPIs();
  loadAreas();
  loadHotspots();
  loadComplaints();
  loadTrends();
  loadTimePatterns();
  loadAreaComparison();
  loadForecast();
  loadBenchmark();
  loadHdfsFiles();
  setupEventHandlers();
});

// Tab Switching Controller
function setupTabs() {
  const tabBtns = document.querySelectorAll(".portal-tab-btn, .tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".portal-pane, .tab-content").forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add("active");

      // Invalidate map size if switching back to landing map tab
      if (targetId === "tab-landing" && map) {
        setTimeout(() => map.invalidateSize(), 150);
      }
    });
  });
}

// -------------------------------------------------------------------------
// Overview KPIs
// -------------------------------------------------------------------------
async function loadOverviewKPIs() {
  try {
    const res = await fetch("/api/summary");
    const data = await res.json();
    document.getElementById("kpi-total-crimes").innerText = (data.total_historical_crimes || 20000).toLocaleString();
    document.getElementById("kpi-hotspots").innerText = data.active_hotspot_areas || 10;
    document.getElementById("kpi-complaints").innerText = (data.mongodb_complaints || 500).toLocaleString();
    document.getElementById("kpi-hdfs-files").innerText = `${data.hdfs_files_count || 13} Files`;
  } catch (err) {
    console.error("Failed to load KPIs:", err);
  }
}

// -------------------------------------------------------------------------
// Areas List
// -------------------------------------------------------------------------
async function loadAreas() {
  try {
    const res = await fetch("/api/areas");
    currentAreas = await res.json();

    const fromSelect = document.getElementById("route-from-area");
    const toSelect = document.getElementById("route-to-area");
    const complaintArea = document.getElementById("complaint-area");
    const reportArea = document.getElementById("report-area");

    fromSelect.innerHTML = "";
    toSelect.innerHTML = "";
    complaintArea.innerHTML = "";
    reportArea.innerHTML = '<option value="ALL">All Areas / City-Wide</option>';

    currentAreas.forEach((a, idx) => {
      const optFrom = new Option(`${a.area_name} (${a.area_id})`, a.area_id);
      const optTo = new Option(`${a.area_name} (${a.area_id})`, a.area_id);
      const optComp = new Option(`${a.area_name} (${a.district_name})`, a.area_id);
      const optRep = new Option(a.area_name, a.area_name);

      fromSelect.add(optFrom);
      toSelect.add(optTo);
      complaintArea.add(optComp);
      reportArea.add(optRep);
    });

    if (currentAreas.length >= 3) {
      fromSelect.value = currentAreas[0].area_id; // Central
      toSelect.value = currentAreas[2].area_id;   // South
    }
  } catch (err) {
    console.error("Failed to load areas:", err);
  }
}

// -------------------------------------------------------------------------
// Feature 5: Crime Hotspot Detection
// -------------------------------------------------------------------------
async function loadHotspots() {
  const crimeType = document.getElementById("map-filter-type").value;
  const year = document.getElementById("map-filter-year").value;

  try {
    const res = await fetch(`/api/hotspots?crime_type=${crimeType}&year=${year}`);
    const data = await res.json();

    renderHotspotsOnMap(data.hotspots);

    // Populate Sidebar Hotspot List
    const listEl = document.getElementById("hotspot-rank-list");
    listEl.innerHTML = "";

    if (!data.hotspots || data.hotspots.length === 0) {
      listEl.innerHTML = '<p style="color:#64748b; font-size:13px;">No hotspots match the selected filter.</p>';
      return;
    }

    data.hotspots.forEach(h => {
      const li = document.createElement("li");
      li.className = "hotspot-item";
      li.innerHTML = `
        <div class="hotspot-info">
          <h4>#${h.rank} ${h.area_name}</h4>
          <span>${h.incident_count.toLocaleString()} Crimes (${h.percentage_of_total}%) | Top: ${h.top_crime_type}</span>
        </div>
        <div class="risk-badge ${h.risk_tier.toLowerCase().includes('high') ? 'high' : (h.risk_tier.toLowerCase().includes('mod') ? 'moderate' : 'low')}">
          ${h.risk_tier.split(' ')[0]}
        </div>
      `;
      li.addEventListener("click", () => {
        if (map) {
          map.setView([h.latitude, h.longitude], 14);
        }
      });
      listEl.appendChild(li);
    });
  } catch (err) {
    console.error("Failed to load hotspots:", err);
  }
}

// -------------------------------------------------------------------------
// Feature 1: Safe-Route Suggestion
// -------------------------------------------------------------------------
async function handleSafeRouteSubmit(e) {
  if (e) e.preventDefault();
  const fromArea = document.getElementById("route-from-area").value;
  const toArea = document.getElementById("route-to-area").value;
  const hour = parseInt(document.getElementById("route-hour").value || 20);

  const container = document.getElementById("routes-cards-container");
  container.innerHTML = '<p style="color:#64748b;">Computing candidate paths and calculating crime-exposure scores across road network...</p>';

  try {
    const res = await fetch(`/api/safe-route?from_area=${fromArea}&to_area=${toArea}&hour=${hour}`);
    const data = await res.json();

    if (data.status === "error") {
      container.innerHTML = `<p style="color:#ef4444;">${data.message}</p>`;
      return;
    }

    // Render Routes on Leaflet Map
    renderRoutesOnMap(data.routes);

    // Switch focus back to map view
    const landingBtn = document.querySelector('.portal-tab-btn[data-tab="tab-landing"], .tab-btn[data-tab="tab-landing"]');
    if (landingBtn) landingBtn.click();
    window.scrollTo({ top: document.getElementById("landing-map").offsetTop - 80, behavior: "smooth" });

    // Render comparison cards in safe route tab
    container.innerHTML = "";
    data.routes.forEach(r => {
      const isRec = r.recommendation.includes("Recommended");
      const card = document.createElement("div");
      card.className = `route-card ${isRec ? 'recommended' : ''}`;
      card.innerHTML = `
        <div class="route-header">
          <span style="font-weight:700; color:${r.color}; font-size:14px;">${r.route_id} (${r.badge})</span>
          <span class="route-score" style="color:${r.color};">${r.risk_score} Risk Pts</span>
        </div>
        <p style="font-size:13px; color:#334155; margin-bottom:4px;"><b>Distance:</b> ${r.distance_km} km</p>
        <p style="font-size:13px; color:#334155; margin-bottom:4px;"><b>Crime Exposure:</b> ${r.historical_crime_exposure} incidents</p>
        <p style="font-size:12px; color:#64748b; margin-bottom:8px;"><b>Traversed Areas:</b> ${r.area_sequence}</p>
        <div style="font-size:11px; padding:4px 8px; border-radius:4px; background:${isRec ? '#ecfdf5' : '#f1f5f9'}; color:${isRec ? '#065f46' : '#475569'};">
          ${r.recommendation}
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = `<p style="color:#ef4444;">Error evaluating routes: ${err.message}</p>`;
  }
}

// -------------------------------------------------------------------------
// Feature 2: Add New Complaint (MongoDB)
// -------------------------------------------------------------------------
async function handleComplaintSubmit(e) {
  e.preventDefault();
  const aid = document.getElementById("complaint-area").value;
  const areaObj = currentAreas.find(a => a.area_id === aid) || { area_name: "Central", lat: 13.0827, lng: 80.2707 };

  const payload = {
    incident_date: document.getElementById("complaint-date").value,
    incident_time: document.getElementById("complaint-time").value,
    crime_type: document.getElementById("complaint-type").value,
    area_id: aid,
    area_name: areaObj.area_name,
    latitude: areaObj.lat,
    longitude: areaObj.lng,
    description: document.getElementById("complaint-desc").value,
    submission_channel: "Citizen Web Portal"
  };

  const statusMsg = document.getElementById("complaint-status-msg");
  statusMsg.innerHTML = '<span style="color:#4f46e5;">Saving complaint document into MongoDB collection...</span>';

  try {
    const res = await fetch("/api/complaints", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.status === "success") {
      statusMsg.innerHTML = `
        <div class="alert-success">
          <b>✓ Complaint Submitted Successfully to MongoDB!</b><br/>
          Reference Number: <b style="font-size:15px; color:#065f46;">${data.complaint.complaint_id}</b><br/>
          Storage Tier: <code>MongoDB NoSQL (crime_db.complaints)</code> | Verified police records remain separate.
        </div>
      `;
      document.getElementById("complaint-form").reset();
      loadComplaints();
      loadOverviewKPIs();
    }
  } catch (err) {
    statusMsg.innerHTML = `<p style="color:#ef4444;">Failed to submit complaint: ${err.message}</p>`;
  }
}

async function loadComplaints() {
  try {
    const res = await fetch("/api/complaints?limit=15");
    const data = await res.json();
    const tbody = document.getElementById("complaints-table-body");
    tbody.innerHTML = "";

    if (!data.complaints || data.complaints.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#64748b;">No complaints submitted yet.</td></tr>';
      return;
    }

    data.complaints.forEach(c => {
      const dateStr = c.incident_date || c.timestamp || (c.created_at ? c.created_at.substring(0, 10) : '2026-10-13');
      const timeStr = c.incident_time || (c.created_at ? c.created_at.substring(11, 16) : '');
      const fullDateTime = timeStr ? `${dateStr} ${timeStr}` : dateStr;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code class="font-mono text-sm">${c.complaint_id}</code></td>
        <td style="font-variant-numeric: tabular-nums;">${fullDateTime}</td>
        <td><span style="font-weight:600; color: #0f172a;">${c.complaint_category}</span></td>
        <td>${c.area_name}</td>
        <td><span class="badge-status under-review">${c.complaint_status || 'Under Review'}</span></td>
        <td><small style="color:#64748b;">${c.description ? c.description.substring(0, 50) + '...' : 'Verified incident submission'}</small></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load complaints:", err);
  }
}

async function syncMongoHdfs() {
  const btn = document.getElementById("btn-sync-hdfs");
  const oldText = btn.innerHTML;
  btn.innerHTML = "Syncing batch to HDFS...";
  try {
    const res = await fetch("/api/complaints/sync-hdfs", { method: "POST" });
    const data = await res.json();
    alert(`Sync Successful! Exported ${data.total_records} complaints to HDFS /crime/raw/mongodb/`);
  } catch (err) {
    alert("Sync error: " + err.message);
  } finally {
    btn.innerHTML = oldText;
  }
}

// -------------------------------------------------------------------------
// Feature 3: Analytical Reports & PDF Export
// -------------------------------------------------------------------------
async function handleReportSummary(e) {
  if (e) e.preventDefault();
  const cType = document.getElementById("report-type").value;
  const aName = document.getElementById("report-area").value;
  const yr = document.getElementById("report-year").value;

  const resultsDiv = document.getElementById("report-results-container");
  resultsDiv.innerHTML = '<p style="color:#64748b;">Aggregating Hive tables and HDFS records...</p>';

  try {
    const res = await fetch(`/api/reports/summary?crime_category=${cType}&area_name=${aName}&year=${yr}`);
    const data = await res.json();

    if (data.status === "warning") {
      resultsDiv.innerHTML = `<p style="color:#f59e0b;">${data.message}</p>`;
      return;
    }

    const m = data.metrics;
    resultsDiv.innerHTML = `
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:1rem; margin-bottom:1rem;">
        <div style="background:#f8fafc; padding:0.75rem; border-radius:6px; border:1px solid #e2e8f0;">
          <small style="color:#64748b;">Incidents in Filter</small>
          <h3 style="color:#4f46e5; font-size:1.3rem;">${m.total_incidents.toLocaleString()}</h3>
        </div>
        <div style="background:#f8fafc; padding:0.75rem; border-radius:6px; border:1px solid #e2e8f0;">
          <small style="color:#64748b;">Total Arrests</small>
          <h3 style="color:#059669; font-size:1.3rem;">${m.arrests_made.toLocaleString()}</h3>
        </div>
        <div style="background:#f8fafc; padding:0.75rem; border-radius:6px; border:1px solid #e2e8f0;">
          <small style="color:#64748b;">Clearance Rate</small>
          <h3 style="color:#7c3aed; font-size:1.3rem;">${m.arrest_rate_pct}%</h3>
        </div>
        <div style="background:#f8fafc; padding:0.75rem; border-radius:6px; border:1px solid #e2e8f0;">
          <small style="color:#64748b;">Covered Sectors</small>
          <h3 style="color:#d97706; font-size:1.3rem;">${m.distinct_areas}</h3>
        </div>
      </div>
      <h4 style="margin: 0.5rem 0; font-size:13px; color:#0f172a;">Sample Extracted Records (First 5):</h4>
      <div class="table-responsive">
        <table class="custom-table">
          <thead>
            <tr>
              <th>ID</th><th>Datetime</th><th>Type</th><th>Area</th><th>Location</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${data.sample_records.slice(0, 5).map(r => `
              <tr>
                <td><code>${r.crime_id}</code></td>
                <td>${r.crime_datetime}</td>
                <td><b>${r.crime_type}</b></td>
                <td>${r.area_name}</td>
                <td>${r.location_type || 'Street'}</td>
                <td>${r.case_status}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (err) {
    resultsDiv.innerHTML = `<p style="color:#ef4444;">Error generating report: ${err.message}</p>`;
  }
}

function downloadReport(format) {
  const cType = document.getElementById("report-type").value;
  const aName = document.getElementById("report-area").value;
  const yr = document.getElementById("report-year").value;
  const endpoint = format === 'pdf' ? '/api/reports/download-pdf' : '/api/reports/download-csv';
  window.open(`${endpoint}?crime_category=${cType}&area_name=${aName}&year=${yr}`, '_blank');
}

// -------------------------------------------------------------------------
// Feature 4: Crime Trends & Growth
// -------------------------------------------------------------------------
async function loadTrends() {
  try {
    const res = await fetch("/api/trends");
    const data = await res.json();
    renderTrendChart(data.monthly_trends);

    // Populate YoY Table
    const tbody = document.getElementById("yearly-trends-body");
    if (tbody) {
      tbody.innerHTML = "";
      data.yearly_trends.forEach(y => {
        const tr = document.createElement("tr");
        const isUp = y.yoy_pct_change > 0;
        tr.innerHTML = `
          <td><b>${y.year}</b></td>
          <td>${y.count.toLocaleString()}</td>
          <td style="color:${isUp ? '#ef4444' : '#10b981'}; font-weight:700;">
            ${y.yoy_pct_change > 0 ? '+' : ''}${y.yoy_pct_change}%
          </td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error("Failed to load trends:", err);
  }
}

// -------------------------------------------------------------------------
// Feature 6: Time-Pattern Analysis
// -------------------------------------------------------------------------
async function loadTimePatterns() {
  try {
    const res = await fetch("/api/time-patterns");
    const data = await res.json();
    renderTimePatternsChart(data.hourly_distribution, data.day_of_week_distribution);

    document.getElementById("peak-hour-text").innerText = `${data.peak_risk_hours[0].label} (${data.peak_risk_hours[0].count.toLocaleString()} incidents)`;
    document.getElementById("lowest-hour-text").innerText = `${data.lowest_risk_hours[0].label} (${data.lowest_risk_hours[0].count.toLocaleString()} incidents)`;
    document.getElementById("weekday-vs-weekend-text").innerText = `Weekday Avg: ${data.weekday_avg} / day | Weekend Avg: ${data.weekend_avg} / day`;

    // Render Matrix Table
    const tbody = document.getElementById("heatmap-matrix-body");
    if (tbody && data.heatmap_matrix) {
      tbody.innerHTML = "";
      data.heatmap_matrix.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><b>${row.day}</b></td>
          <td>${row['00:00-04:00']}</td>
          <td>${row['04:00-08:00']}</td>
          <td>${row['08:00-12:00']}</td>
          <td>${row['12:00-16:00']}</td>
          <td>${row['16:00-20:00']}</td>
          <td>${row['20:00-24:00']}</td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error("Failed to load time patterns:", err);
  }
}

// -------------------------------------------------------------------------
// Feature 7: Area & Demographics Comparison
// -------------------------------------------------------------------------
async function loadAreaComparison() {
  try {
    const res = await fetch("/api/area-comparison");
    const data = await res.json();
    const tbody = document.getElementById("area-comparison-body");
    tbody.innerHTML = "";

    data.area_comparison_data.forEach(a => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><b>${a.area_name}</b></td>
        <td>${a.population.toLocaleString()}</td>
        <td>${a.total_crimes.toLocaleString()}</td>
        <td><b style="color:#4f46e5;">${a.crime_rate_per_100k}</b></td>
        <td>${a.arrest_rate_pct}%</td>
        <td><small>${a.police_station.station_name} (${a.police_station.contact_number})</small></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load area comparisons:", err);
  }
}

// -------------------------------------------------------------------------
// Feature 8: Multi-Source Integration
// -------------------------------------------------------------------------
async function runIntegration() {
  const btn = document.getElementById("btn-run-integration");
  const oldText = btn.innerHTML;
  btn.innerHTML = "Executing Pipeline...";
  const outBox = document.getElementById("integration-console-box");
  outBox.innerHTML = "[*] Commencing multi-source ETL & deduplication...";

  try {
    const res = await fetch("/api/integration/run", { method: "POST" });
    const data = await res.json();

    outBox.innerHTML = `
[SUCCESS] Multi-Source Integration Pipeline Complete
------------------------------------------------------
Raw Records Read Across Sources : ${data.raw_records_imported.toLocaleString()}
Duplicates Identified & Removed: ${data.duplicates_removed.toLocaleString()}
Final Unified Analytical Corpus : ${data.clean_integrated_records.toLocaleString()} records

Data Provenance Breakdown:
  • Datacenter Historical CSV   : ${data.source_breakdown.datacenter_historical_csv || 0} records
  • MongoDB Citizen Complaints  : ${data.source_breakdown.mongodb_citizen_complaints || 0} records

HDFS Destination: ${data.hdfs_destination}
Status: Master analytical corpus synchronized to Hadoop HDFS warehouse!
    `;
    loadOverviewKPIs();
  } catch (err) {
    outBox.innerHTML = `[ERROR] Integration failed: ${err.message}`;
  } finally {
    btn.innerHTML = oldText;
  }
}

// -------------------------------------------------------------------------
// Feature 9: Crime Trend Forecasting
// -------------------------------------------------------------------------
async function loadForecast() {
  try {
    const res = await fetch("/api/forecasting?horizon=6");
    const data = await res.json();

    document.getElementById("forecast-scope-text").innerText = data.scope;
    document.getElementById("forecast-trend-text").innerText = data.model_metadata.estimated_trend_direction;

    renderForecastChart(data.historical_data, data.forecast_data);

    const tbody = document.getElementById("forecast-table-body");
    tbody.innerHTML = "";
    data.forecast_data.forEach(f => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><b>${f.period}</b></td>
        <td><b style="color:#4f46e5;">${f.predicted_count}</b></td>
        <td>${f.lower_bound_80pct}</td>
        <td>${f.upper_bound_80pct}</td>
        <td><span class="risk-badge low">Statistical Estimate</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load forecast:", err);
  }
}

// -------------------------------------------------------------------------
// Feature 10: Scalability Benchmark (100K, 500K, 1M)
// -------------------------------------------------------------------------
async function loadBenchmark() {
  try {
    const res = await fetch("/api/benchmark");
    const data = await res.json();
    renderBenchmarkChart(data.results);

    const tbody = document.getElementById("benchmark-table-body");
    tbody.innerHTML = "";
    data.results.forEach(b => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><b>${b.label}</b></td>
        <td>${b.local_processing.execution_time_sec}s (${b.local_processing.throughput_records_per_sec.toLocaleString()} rec/s)</td>
        <td><b style="color:#4f46e5;">${b.distributed_hadoop_mapreduce.execution_time_sec}s</b> (${b.distributed_hadoop_mapreduce.throughput_records_per_sec.toLocaleString()} rec/s)</td>
        <td><span class="risk-badge low">${b.speedup_factor}x Speedup</span></td>
        <td><b style="color:#059669;">${b.efficiency_gain_pct}%</b></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load benchmark:", err);
  }
}

async function runLiveBenchmark() {
  const size = parseInt(document.getElementById("live-benchmark-size").value);
  const logBox = document.getElementById("benchmark-live-log");
  logBox.innerHTML = `[*] Allocating worker pool and streaming ${size.toLocaleString()} records from chicago_crimes_1m.csv...`;

  try {
    const res = await fetch("/api/benchmark/live", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sample_size: size })
    });
    const data = await res.json();
    const item = data.results[0];

    logBox.innerHTML = `
[SUCCESS] Live Scalability Execution Completed
------------------------------------------------------
Slice Evaluated: ${item.label} (${item.dataset_size_records.toLocaleString()} records)

Mode 1 (Single-Core Sequential Baseline):
  • Latency   : ${item.local_processing.execution_time_sec} seconds
  • Throughput: ${item.local_processing.throughput_records_per_sec.toLocaleString()} records / sec

Mode 2 (Distributed MapReduce / Multi-Worker Pipeline):
  • Latency   : ${item.distributed_hadoop_mapreduce.execution_time_sec} seconds
  • Throughput: ${item.distributed_hadoop_mapreduce.throughput_records_per_sec.toLocaleString()} records / sec
  • Workers   : ${item.distributed_hadoop_mapreduce.containers_workers} worker processes

Speedup Achieved: ${item.speedup_factor}x faster (${item.efficiency_gain_pct}% time reduction)
    `;
  } catch (err) {
    logBox.innerHTML = `[ERROR] Live test error: ${err.message}`;
  }
}

// -------------------------------------------------------------------------
// Big Data Console (HDFS, Pig, Hive)
// -------------------------------------------------------------------------
async function loadHdfsFiles() {
  try {
    const res = await fetch("/api/hdfs/files");
    const files = await res.json();
    const tbody = document.getElementById("hdfs-files-body");
    tbody.innerHTML = "";

    if (!files || files.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" style="color:#64748b;">No files in HDFS namespace yet.</td></tr>';
      return;
    }

    files.forEach(f => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code class="font-mono text-xs">${f.hdfs_path}</code></td>
        <td style="font-variant-numeric: tabular-nums;">${(f.size_bytes / 1024).toFixed(1)} KB</td>
        <td><code>TEXT / CSV</code></td>
        <td><span class="sys-badge active">Stored</span></td>
        <td>
          <button class="btn-action btn-secondary" style="padding: 0.25rem 0.65rem; font-size: 0.7rem; font-weight: 700;" onclick="inspectHdfsFile('${f.hdfs_path}')">View Raw Lines</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load HDFS files:", err);
  }
}

async function inspectHdfsFile(hdfsPath) {
  const box = document.getElementById("pipeline-terminal");
  box.innerHTML = `[*] Reading raw records from HDFS location: ${hdfsPath}...`;
  try {
    const res = await fetch(`/api/hdfs/cat?path=${encodeURIComponent(hdfsPath)}&limit=30`);
    const data = await res.json();
    if (data.status === "success") {
      box.innerHTML = `[HDFS FILE INSPECTOR] Location: ${data.hdfs_path}\n` +
        `[METADATA] Displaying first ${data.total_lines_previewed} lines:\n` +
        `================================================================================\n` +
        data.preview_text + `\n` +
        `================================================================================\n` +
        `[END OF PREVIEW] Full file stored persistently on HDFS namespace.`;
      box.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
      box.innerHTML = `[ERROR] Unable to preview file: ${data.detail || 'File not found'}`;
    }
  } catch (err) {
    box.innerHTML = `[ERROR] Failed to fetch HDFS file: ${err.message}`;
  }
}

async function runPigCleaning() {
  const box = document.getElementById("pipeline-terminal");
  box.innerHTML = "[*] Dispatching Pig Latin Job: clean_crimes.pig...";
  try {
    const res = await fetch("/api/pig/run-clean", { method: "POST" });
    const data = await res.json();
    box.innerHTML = data.execution_log;
    loadHdfsFiles();
    loadOverviewKPIs();
  } catch (err) {
    box.innerHTML = `[ERROR] Pig Job Failed: ${err.message}`;
  }
}

async function runPigHotspots() {
  const box = document.getElementById("pipeline-terminal");
  box.innerHTML = "[*] Dispatching Apache Pig Latin script: hotspot_analysis.pig\n[*] Aggregating crime frequencies by Sector & Crime Type on HDFS...";
  try {
    const res = await fetch("/api/pig/run-hotspots", { method: "POST" });
    const data = await res.json();

    let sampleTable = "RANK | SECTOR       | CLASSIFICATION | INCIDENTS | CENTROID COORDS\n" +
      "-----+--------------+----------------+-----------+--------------------\n";
    (data.sample_results || []).forEach((row, idx) => {
      const rank = String(idx + 1).padStart(4, " ");
      const area = String(row.area_name || "").padEnd(12, " ");
      const type = String(row.crime_type || "").padEnd(14, " ");
      const cnt = String(row.incident_count || "").padStart(9, " ");
      const lat = row.avg_latitude ? row.avg_latitude.toFixed(4) : "0.0000";
      const lng = row.avg_longitude ? row.avg_longitude.toFixed(4) : "0.0000";
      sampleTable += `${rank} | ${area} | ${type} | ${cnt} | ${lat}° N, ${lng}° E\n`;
    });

    box.innerHTML = `[SUCCESS] Apache Pig Hotspot Analysis Completed in ${data.execution_time_seconds}s\n` +
      `Total Hotspot Clusters Identified: ${data.total_hotspot_clusters}\n` +
      `HDFS Destination: ${data.hdfs_destination}/part-r-00000\n\n` +
      `TOP IDENTIFIED HOTSPOT CLUSTERS (PIG LATIN MAPREDUCE OUTPUT):\n` +
      `================================================================================\n` +
      sampleTable +
      `================================================================================\n` +
      `[NOTE] These clusters are geographically mapped on the "Patrol Sector Map" tab with proportional risk radii.\n` +
      `You can inspect the raw HDFS part-r-00000 file in the HDFS Storage Ledger below.`;
    loadHdfsFiles();
  } catch (err) {
    box.innerHTML = `[ERROR] Pig Job Failed: ${err.message}`;
  }
}

async function executeHiveQuery() {
  const query = document.getElementById("hive-query-input").value;
  const box = document.getElementById("pipeline-terminal");
  box.innerHTML = `[*] Executing HiveQL query against HDFS warehouse:\n${query}`;
  try {
    const res = await fetch("/api/hive/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    });
    const data = await res.json();
    if (data.status === "error") {
      box.innerHTML = `[HIVE ERROR] ${data.error}`;
    } else {
      box.innerHTML = `[SUCCESS] Query returned ${data.row_count} rows in ${data.execution_time_seconds}s.\n\nSample Output:\n${JSON.stringify(data.data.slice(0, 5), null, 2)}`;
    }
  } catch (err) {
    box.innerHTML = `[ERROR] Query execution failed: ${err.message}`;
  }
}

// -------------------------------------------------------------------------
// Event Handlers Setup
// -------------------------------------------------------------------------
function setupEventHandlers() {
  document.getElementById("map-filter-type").addEventListener("change", loadHotspots);
  document.getElementById("map-filter-year").addEventListener("change", loadHotspots);
  document.getElementById("safe-route-form").addEventListener("submit", handleSafeRouteSubmit);
  document.getElementById("complaint-form").addEventListener("submit", handleComplaintSubmit);
  document.getElementById("btn-sync-hdfs").addEventListener("click", syncMongoHdfs);
  document.getElementById("report-filter-form").addEventListener("submit", handleReportSummary);
  document.getElementById("btn-export-pdf").addEventListener("click", () => downloadReport('pdf'));
  document.getElementById("btn-export-csv").addEventListener("click", () => downloadReport('csv'));
  document.getElementById("btn-run-integration").addEventListener("click", runIntegration);
  document.getElementById("btn-run-live-benchmark").addEventListener("click", runLiveBenchmark);
  document.getElementById("btn-run-pig-clean").addEventListener("click", runPigCleaning);
  document.getElementById("btn-run-pig-hotspot").addEventListener("click", runPigHotspots);
  document.getElementById("btn-execute-hive").addEventListener("click", executeHiveQuery);
}
