const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const percent = new Intl.NumberFormat("en-US", {
  style: "percent",
  maximumFractionDigits: 2,
});

const statusText = document.getElementById("statusText");
const refreshButton = document.getElementById("refreshButton");

function pickCard(pick, open = false) {
  return `
    <article class="pick-card ${open ? "open" : ""}">
      <div class="pick-rank">Rank ${pick.rank}</div>
      <div class="pick-ticker">${pick.ticker}</div>
      <div class="pick-score">Momentum ${percent.format(Number(pick.momentum_score || 0))}</div>
    </article>
  `;
}

function renderDashboard(payload) {
  const openPicks = payload.open_picks || [];
  const nextPicks = payload.next_picks || [];
  const history = payload.last_year || [];
  const comparison = payload.comparison || [];

  document.getElementById("openDate").textContent =
    openPicks[0]?.rebalance_date || "Unavailable";
  document.getElementById("nextDate").textContent =
    nextPicks[0]?.rebalance_date || "Unavailable";
  document.getElementById("windowText").textContent =
    `${payload.config.start_date} to ${payload.config.end_date}`;

  document.getElementById("openPicks").innerHTML =
    openPicks.map((pick) => pickCard(pick, true)).join("");
  document.getElementById("nextPicks").innerHTML =
    nextPicks.map((pick) => pickCard(pick, false)).join("");

  const strategyFinal = comparison.find((row) => row.metric === "Final equity");
  const cagr = comparison.find((row) => row.metric === "CAGR");
  const sharpe = comparison.find((row) => row.metric === "Sharpe ratio");
  const drawdown = comparison.find((row) => row.metric === "Max drawdown");
  const cards = [
    ["Strategy equity", currency.format(Number(strategyFinal?.strategy || 0)), "Current backtest terminal value"],
    ["Strategy CAGR", percent.format(Number(cagr?.strategy || 0)), "Realized backtest annualized return"],
    ["Sharpe ratio", Number(sharpe?.strategy || 0).toFixed(2), "Monthly-return Sharpe"],
    ["Max drawdown", percent.format(Number(drawdown?.strategy || 0)), "Largest realized peak-to-trough loss"],
  ];
  document.getElementById("performanceCards").innerHTML = cards.map(([label, value, note]) => `
    <article class="metric-card">
      <div class="metric-label">${label}</div>
      <div class="metric-value">${value}</div>
      <div class="metric-note">${note}</div>
    </article>
  `).join("");

  document.getElementById("historyRows").innerHTML = history.map((row) => `
    <tr>
      <td>${row.rebalance_date}</td>
      <td>${row.pick_1 || ""}</td>
      <td>${row.pick_2 || ""}</td>
      <td>${row.pick_3 || ""}</td>
      <td>${percent.format(Number(row.avg_momentum_score || 0))}</td>
      <td><span class="status-pill ${row.holding_status || "closed"}">${row.holding_status || "closed"}</span></td>
    </tr>
  `).join("");

  const cacheBust = Date.now();
  document.getElementById("rotationChart").src =
    `/outputs/charts/last_12_month_pick_rotation.png?${cacheBust}`;
}

async function refreshDashboard() {
  refreshButton.disabled = true;
  statusText.textContent = "Refreshing market data and rebuilding picks...";
  try {
    const response = await fetch("/api/refresh", { method: "POST" });
    if (!response.ok) {
      throw new Error(`Refresh failed: ${response.status}`);
    }
    const payload = await response.json();
    renderDashboard(payload);
    statusText.textContent = `Updated through ${payload.config.end_date}.`;
  } catch (error) {
    statusText.textContent = error.message;
  } finally {
    refreshButton.disabled = false;
  }
}

async function loadCachedDashboard() {
  try {
    const response = await fetch("/api/dashboard");
    if (!response.ok) {
      throw new Error(`Initial load failed: ${response.status}`);
    }
    const payload = await response.json();
    renderDashboard(payload);
    statusText.textContent = "Loaded cached dashboard. Refreshing latest market data...";
  } catch (error) {
    statusText.textContent = error.message;
  }
}

refreshButton.addEventListener("click", refreshDashboard);
loadCachedDashboard().finally(refreshDashboard);
