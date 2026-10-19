/**
 * Chart.js Visualizations Controller
 */
let trendChart = null;
let timeChart = null;
let benchmarkChart = null;
let forecastChart = null;
let areaCompChart = null;

function renderTrendChart(monthlyTrends) {
  const ctx = document.getElementById('trend-chart');
  if (!ctx || !monthlyTrends) return;

  const labels = monthlyTrends.map(m => m.year_month);
  const data = monthlyTrends.map(m => m.count);
  const momPct = monthlyTrends.map(m => m.mom_pct_change);

  if (trendChart) trendChart.destroy();

  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Monthly Crime Count',
          data: data,
          borderColor: '#4f46e5',
          backgroundColor: 'rgba(79, 70, 229, 0.08)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 2,
          yAxisID: 'y'
        },
        {
          label: 'MoM % Change',
          data: momPct,
          borderColor: '#f59e0b',
          borderDash: [5, 5],
          tension: 0.2,
          borderWidth: 1.5,
          pointRadius: 0,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: { display: true, text: 'Recorded Incidents' },
          grid: { color: '#f1f5f9' }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: { display: true, text: 'MoM % Change' },
          grid: { drawOnChartArea: false }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

function renderTimePatternsChart(hourlyData, dowData) {
  const ctx = document.getElementById('diurnal-chart');
  if (!ctx || !hourlyData) return;

  const labels = hourlyData.map(h => h.label);
  const counts = hourlyData.map(h => h.count);

  if (timeChart) timeChart.destroy();

  timeChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Incidents by Hour (24-Hour Cycle)',
        data: counts,
        backgroundColor: hourlyData.map(h => (h.hour >= 21 || h.hour <= 4) ? 'rgba(239, 68, 68, 0.75)' : 'rgba(59, 130, 246, 0.75)'),
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { title: { display: true, text: 'Incident Frequency' }, grid: { color: '#f1f5f9' } },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderBenchmarkChart(benchmarkData) {
  const ctx = document.getElementById('benchmark-chart');
  if (!ctx || !benchmarkData) return;

  const labels = benchmarkData.map(b => b.label);
  const localTimes = benchmarkData.map(b => b.local_processing.execution_time_sec);
  const distTimes = benchmarkData.map(b => b.distributed_hadoop_mapreduce.execution_time_sec);

  if (benchmarkChart) benchmarkChart.destroy();

  benchmarkChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Local Sequential Processing (s)',
          data: localTimes,
          backgroundColor: '#94a3b8',
          borderRadius: 6
        },
        {
          label: 'Hadoop MapReduce / Distributed (s)',
          data: distTimes,
          backgroundColor: '#4f46e5',
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { title: { display: true, text: 'Execution Latency (Seconds, lower is faster)' }, grid: { color: '#f1f5f9' } },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderForecastChart(historicalData, forecastData) {
  const ctx = document.getElementById('forecast-chart');
  if (!ctx || !historicalData || !forecastData) return;

  const histLabels = historicalData.map(d => d.period);
  const foreLabels = forecastData.map(d => d.period);
  const allLabels = [...histLabels, ...foreLabels];

  const histValues = historicalData.map(d => d.count);
  const nullPadding = new Array(historicalData.length - 1).fill(null);

  // Link last historical to first forecast
  const lastHistVal = histValues[histValues.length - 1];
  const foreValues = [...nullPadding, lastHistVal, ...forecastData.map(d => d.predicted_count)];
  const upperBounds = [...nullPadding, lastHistVal, ...forecastData.map(d => d.upper_bound_80pct)];
  const lowerBounds = [...nullPadding, lastHistVal, ...forecastData.map(d => d.lower_bound_80pct)];

  if (forecastChart) forecastChart.destroy();

  forecastChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        {
          label: 'Historical Aggregates',
          data: [...histValues, ...new Array(forecastData.length).fill(null)],
          borderColor: '#0284c7',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 2.5
        },
        {
          label: 'Forecast Estimate (Holt-Winters)',
          data: foreValues,
          borderColor: '#4f46e5',
          borderDash: [5, 5],
          backgroundColor: 'transparent',
          borderWidth: 2.5,
          pointRadius: 3
        },
        {
          label: '80% Upper Bound',
          data: upperBounds,
          borderColor: 'transparent',
          backgroundColor: 'rgba(79, 70, 229, 0.12)',
          fill: '+1',
          pointRadius: 0
        },
        {
          label: '80% Lower Bound',
          data: lowerBounds,
          borderColor: 'transparent',
          backgroundColor: 'rgba(79, 70, 229, 0.12)',
          fill: false,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: { title: { display: true, text: 'Aggregate Monthly Incidents' }, grid: { color: '#f1f5f9' } },
        x: { grid: { display: false } }
      }
    }
  });
}
