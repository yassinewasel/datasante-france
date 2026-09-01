// Met a jour l'apercu de l'accueil sans quitter la page.
const homeSearchForm = document.getElementById("home-search-form");
const professionInput = document.getElementById("profession");
const yearInput = document.getElementById("annee");
const previewEffectif = document.getElementById("preview-effectif");
const previewDensite = document.getElementById("preview-densite");
const previewTerritory = document.getElementById("preview-territory");
const previewVariation = document.getElementById("preview-variation");
const previewVariationPct = document.getElementById("preview-variation-pct");
const previewAverage = document.getElementById("preview-average");
const previewSummary = document.getElementById("preview-summary");
const needProfession = document.getElementById("need-profession");
const needTerritory = document.getElementById("need-territory");
const needYear = document.getElementById("need-year");
const previewCanvas = document.getElementById("previewChart");
const selectionTable = document.getElementById("selection-table");
const statsTable = document.getElementById("stats-table");
const historyTable = document.getElementById("history-table");
const selectionPoints = document.getElementById("selection-points");
const historyPoints = document.getElementById("history-points");

let previewChart = null;
let previewRequestId = 0;

// Formate un nombre pour son affichage en francais.
function formatNumber(value, decimals = 0) {
  const number = Number(value);
  if (value === null || value === undefined || Number.isNaN(number)) return "N/A";
  return new Intl.NumberFormat("fr-FR", {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  }).format(number);
}

// Ajoute un signe explicite aux variations.
function formatSigned(value, decimals = 0, suffix = "") {
  const number = Number(value);
  if (value === null || value === undefined || Number.isNaN(number)) return "N/A";
  const sign = number > 0 ? "+" : "";
  return `${sign}${formatNumber(number, decimals)}${suffix}`;
}

// Produit le HTML d'un tableau de resultats.
function tableMarkup(name, headers, rows) {
  if (!rows.length) return '<p class="empty">Aucune donnée disponible pour cette sélection.</p>';
  const head = headers.map((header) => `<th>${header}</th>`).join("");
  const body = rows
    .map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`)
    .join("");
  return `<table class="data-table" data-table-name="${name}"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

// Active le tri et l'export sur les tableaux generes.
function enhanceHomeTables() {
  document.querySelectorAll("#home-results table").forEach((table) => {
    if (typeof ajouterOutilsTable === "function") ajouterOutilsTable(table);
  });
}

// Indique visuellement les filtres deja renseignes.
function setRequirementState() {
  needProfession?.classList.toggle("complete", Boolean(professionInput.value));
  needTerritory?.classList.toggle("complete", Boolean(regionSelect.value));
  needYear?.classList.toggle("complete", Boolean(yearInput.value));
}

function resetPreview(message = "Complétez les filtres pour afficher la prévisualisation.") {
  previewEffectif.textContent = "-";
  previewDensite.textContent = "-";
  previewTerritory.textContent = "-";
  if (previewVariation) previewVariation.textContent = "-";
  if (previewVariationPct) previewVariationPct.textContent = "-";
  if (previewAverage) previewAverage.textContent = "-";
  previewSummary.textContent = message;
  if (selectionPoints) selectionPoints.textContent = "Année";
  if (historyPoints) historyPoints.textContent = "0 point";
  if (selectionTable) selectionTable.innerHTML = '<p class="empty">Aucune donnée à afficher pour le moment.</p>';
  if (statsTable) statsTable.innerHTML = '<p class="empty">Les repères seront calculés après sélection.</p>';
  if (historyTable) historyTable.innerHTML = '<p class="empty">Aucun historique chargé.</p>';
  if (previewChart) {
    previewChart.data.labels = [];
    previewChart.data.datasets[0].data = [];
    previewChart.data.datasets[1].data = [];
    previewChart.update();
  }
}

// Cree le graphique Chart.js une seule fois.
function ensurePreviewChart() {
  if (!previewCanvas || !window.Chart) return null;
  if (previewChart) return previewChart;
  previewChart = new Chart(previewCanvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: "Effectif",
        data: [],
        borderColor: "#0d7a8c",
        backgroundColor: "rgba(83, 189, 127, .16)",
        fill: true,
        tension: .3,
      }, {
        label: "Densité",
        data: [],
        borderColor: "#ef8278",
        backgroundColor: "rgba(239, 130, 120, .12)",
        fill: false,
        tension: .3,
        yAxisID: "y1",
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
      scales: {
        y: { beginAtZero: true },
        y1: {
          beginAtZero: true,
          position: "right",
          grid: { drawOnChartArea: false },
        },
      },
    },
  });
  return previewChart;
}

// Dessine un graphique canvas si Chart.js est indisponible.
function drawFallbackChart(chart) {
  const canvas = chart.canvas;
  const context = canvas.getContext("2d");
  const width = canvas.clientWidth || 640;
  const height = canvas.clientHeight || 280;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, width, height);

  const labels = chart.data.labels;
  const effectifs = chart.data.datasets[0].data.map(Number);
  const densites = chart.data.datasets[1].data.map(Number);
  const values = [...effectifs, ...densites].filter((value) => !Number.isNaN(value));
  if (!labels.length || !values.length) return;

  const padding = { top: 20, right: 24, bottom: 42, left: 48 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const max = Math.max(...values, 1);

  context.strokeStyle = "#dfe7f2";
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(padding.left, padding.top);
  context.lineTo(padding.left, height - padding.bottom);
  context.lineTo(width - padding.right, height - padding.bottom);
  context.stroke();

  // Calcule les coordonnees d'un point sur le canvas.
  function point(index, value) {
    const x = padding.left + (labels.length === 1 ? innerWidth / 2 : (index / (labels.length - 1)) * innerWidth);
    const y = height - padding.bottom - (Number(value || 0) / max) * innerHeight;
    return { x, y };
  }

  // Trace une serie et ses points.
  function drawLine(valuesLine, color) {
    context.strokeStyle = color;
    context.lineWidth = 3;
    context.beginPath();
    valuesLine.forEach((value, index) => {
      const current = point(index, value);
      if (index === 0) context.moveTo(current.x, current.y);
      else context.lineTo(current.x, current.y);
    });
    context.stroke();

    context.fillStyle = color;
    valuesLine.forEach((value, index) => {
      const current = point(index, value);
      context.beginPath();
      context.arc(current.x, current.y, 3, 0, Math.PI * 2);
      context.fill();
    });
  }

  drawLine(effectifs, "#0d7a8c");
  drawLine(densites, "#ef8278");

  context.fillStyle = "#6781a8";
  context.font = "700 12px Inter, sans-serif";
  context.textAlign = "center";
  labels.forEach((label, index) => {
    if (index % Math.ceil(labels.length / 6) === 0 || index === labels.length - 1) {
      context.fillText(label, point(index, 0).x, height - 16);
    }
  });

  context.textAlign = "left";
  context.fillStyle = "#0d7a8c";
  context.fillText("Effectif", padding.left, 16);
  context.fillStyle = "#ef8278";
  context.fillText("Densité", padding.left + 78, 16);
}

// Cree la version canvas de secours du graphique.
function ensureFallbackChart() {
  if (!previewCanvas) return null;
  if (previewChart) return previewChart;
  previewChart = {
    canvas: previewCanvas,
    data: {
      labels: [],
      datasets: [
        { data: [] },
        { data: [] },
      ],
    },
    update() {
      drawFallbackChart(this);
    },
  };
  return previewChart;
}

// Choisit Chart.js ou le rendu canvas de secours.
function ensureChart() {
  return window.Chart ? ensurePreviewChart() : ensureFallbackChart();
}

// Remplit les tableaux avec les donnees de l'API.
function renderTables(payload) {
  const analyse = payload.analyse || {};
  const selection = analyse.selection || {};
  const max = analyse.max || {};
  const min = analyse.min || {};
  const resultRows = (payload.resultats || []).map((row) => [
    row.annee ?? payload.annee,
    formatNumber(row.effectif),
    formatNumber(row.densite, 2),
  ]);
  const historyRows = (payload.evolution || []).map((row) => [
    row.annee ?? "",
    formatNumber(row.effectif),
    formatNumber(row.densite, 2),
  ]);
  const statRows = [
    ["Moyenne effectif", formatNumber(analyse.moyenne_effectif, 1)],
    ["Moyenne densité", formatNumber(analyse.moyenne_densite, 2)],
    ["Année la plus élevée", max.effectif !== undefined && max.effectif !== null ? `${max.annee} (${formatNumber(max.effectif)})` : "N/A"],
    ["Année la plus faible", min.effectif !== undefined && min.effectif !== null ? `${min.annee} (${formatNumber(min.effectif)})` : "N/A"],
    ["Points historiques", analyse.points ?? 0],
  ];

  if (selectionPoints) selectionPoints.textContent = selection.annee || String(payload.annee);
  if (historyPoints) historyPoints.textContent = `${analyse.points ?? historyRows.length} point${(analyse.points ?? historyRows.length) > 1 ? "s" : ""}`;
  if (selectionTable) selectionTable.innerHTML = tableMarkup("resultat-selection", ["Année", "Effectif", "Densité"], resultRows);
  if (statsTable) statsTable.innerHTML = tableMarkup("reperes-statistiques", ["Repère", "Valeur"], statRows);
  if (historyTable) historyTable.innerHTML = tableMarkup("historique-effectifs", ["Année", "Effectif", "Densité"], historyRows);
  enhanceHomeTables();
}

// Interroge l'API puis actualise les KPI et le graphique.
async function updatePreview() {
  if (!homeSearchForm) return;
  const requestId = ++previewRequestId;
  setRequirementState();
  ensureChart();

  if (!professionInput.value || !regionSelect.value || !yearInput.value) {
    resetPreview("Complétez les filtres pour afficher les résultats.");
    return;
  }

  previewSummary.textContent = "Chargement de la prévisualisation...";
  const params = new URLSearchParams({
    profession_id: professionInput.value,
    region_id: regionSelect.value,
    departement_id: departementSelect.value,
    annee: yearInput.value,
  });
  const response = await fetch(`${homeSearchForm.dataset.previewUrl}?${params.toString()}`);
  const payload = await response.json();
  if (requestId !== previewRequestId) return;

  if (!payload.pret) {
    resetPreview(payload.message);
    return;
  }

  const analyse = payload.analyse || {};
  previewEffectif.textContent = formatNumber(payload.effectif);
  previewDensite.textContent = formatNumber(payload.densite, 2);
  previewTerritory.textContent = payload.departement.code;
  if (previewVariation) previewVariation.textContent = formatSigned(analyse.variation, 0);
  if (previewVariationPct) previewVariationPct.textContent = formatSigned(analyse.variation_pct, 1, " %");
  if (previewAverage) previewAverage.textContent = formatNumber(analyse.moyenne_effectif, 1);
  previewSummary.textContent = `${payload.profession} - ${payload.departement.libelle} - ${payload.annee}`;
  renderTables(payload);

  const chart = ensureChart();
  if (chart) {
    chart.data.labels = payload.evolution.map((row) => row.annee);
    chart.data.datasets[0].data = payload.evolution.map((row) => row.effectif);
    chart.data.datasets[1].data = payload.evolution.map((row) => row.densite);
    chart.update();
  }
}

if (homeSearchForm) {
  ensureChart();
  homeSearchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    updatePreview()
      .then(() => {
        document.querySelector(".preview-card")?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      })
      .catch(() => resetPreview("Impossible de charger la prévisualisation."));
  });
  [professionInput, regionSelect, departementSelect, yearInput].forEach((element) => {
    element?.addEventListener("change", () => updatePreview().catch(() => resetPreview("Impossible de charger la prévisualisation.")));
  });
  setRequirementState();
  resetPreview("Les résultats apparaîtront ici après le choix des filtres.");
}
