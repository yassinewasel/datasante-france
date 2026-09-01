// Gere les pages d'analyse alimentes par les endpoints Data Ameli.
const analysisForm = document.getElementById("analysis-form");
const analysisConfig = window.analysisConfig || {};
const analysisRegion = document.getElementById("analysis-region");
const analysisDepartment = document.getElementById("analysis-departement");
const analysisStatus = document.getElementById("analysis-status");
const analysisTable = document.getElementById("analysis-table");
let analysisChart = null;

// Formate un nombre selon la convention francaise.
function formatValue(value, options = {}) {
  const number = Number(value);
  if (value === null || value === undefined || Number.isNaN(number)) return "N/A";
  return new Intl.NumberFormat("fr-FR", options).format(number);
}

// Affiche le statut de chargement ou une erreur.
function setAnalysisMessage(message, isError = false) {
  if (!analysisStatus) return;
  analysisStatus.textContent = message;
  analysisStatus.classList.toggle("error-status", isError);
}

// Recharge les departements apres un changement de region.
async function loadAnalysisDepartments() {
  if (!analysisRegion || !analysisDepartment) return;
  analysisDepartment.innerHTML = '<option value="">Toute la région</option>';
  analysisDepartment.disabled = true;
  if (!analysisRegion.value) return;

  const url = analysisForm.dataset.departementsUrl.replace(/0$/, analysisRegion.value);
  const response = await fetch(url);
  const departments = await response.json();
  for (const department of departments) {
    const option = document.createElement("option");
    option.value = department.id;
    option.textContent = `${department.code} - ${department.libelle}`;
    analysisDepartment.appendChild(option);
  }
  analysisDepartment.disabled = false;
}

// Cree une seule instance du graphique principal.
function createAnalysisChart() {
  const canvas = document.getElementById("analysis-chart");
  if (!canvas || !window.Chart) return null;
  if (analysisChart) return analysisChart;
  analysisChart = new Chart(canvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: analysisConfig.chartLabel || "Valeur",
        data: [],
        borderColor: "#0d7a8c",
        backgroundColor: "rgba(83, 189, 127, .16)",
        fill: true,
        tension: .3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom" },
        title: { display: true, text: analysisConfig.chartTitle || "Évolution" },
      },
      scales: {
        x: { title: { display: true, text: "Année" } },
        y: { beginAtZero: true, title: { display: true, text: analysisConfig.axisLabel || "Valeur" } },
      },
    },
  });
  return analysisChart;
}

// Injecte les donnees recues dans le graphique.
function updateAnalysisChart(rows) {
  const chart = createAnalysisChart();
  if (!chart) return;
  chart.data.labels = rows.map((row) => row.annee);
  chart.data.datasets[0].data = rows.map((row) => row[analysisConfig.chartField]);
  chart.update();
}

// Met a jour les indicateurs de synthese.
function updateAnalysisKpis(payload) {
  document.getElementById("analysis-total").textContent = analysisConfig.kind === "pathologies"
    ? formatValue(payload.personnes)
    : `${formatValue(payload.montant_total)} €`;
  document.getElementById("analysis-average").textContent = analysisConfig.kind === "pathologies"
    ? `${formatValue(payload.prevalence, { maximumFractionDigits: 3 })} %`
    : `${formatValue(payload.montant_moyen)} €`;
  document.getElementById("analysis-territory").textContent = payload.territoire || "-";
  document.getElementById("analysis-period").textContent = `${payload.periode.debut} - ${payload.periode.fin}`;
}

// Construit le tableau de resultats puis active ses outils.
function updateAnalysisTable(rows) {
  const headers = analysisConfig.kind === "pathologies"
    ? ["Année", "Personnes concernées", "Population", "Prévalence (%)"]
    : ["Année", "Montant total", "Montant moyen"];
  const body = rows.length
    ? rows.map((row) => analysisConfig.kind === "pathologies"
      ? `<tr><td>${row.annee}</td><td>${formatValue(row.personnes)}</td><td>${formatValue(row.population)}</td><td>${formatValue(row.prevalence, { maximumFractionDigits: 3 })}</td></tr>`
      : `<tr><td>${row.annee}</td><td>${formatValue(row.montant_total)} €</td><td>${formatValue(row.montant_moyen)} €</td></tr>`
    ).join("")
    : `<tr><td colspan="${headers.length}">Aucune donnée disponible pour cette sélection.</td></tr>`;
  analysisTable.innerHTML = `<thead><tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr></thead><tbody>${body}</tbody>`;
  const toolbar = analysisTable.previousElementSibling;
  if (toolbar?.classList.contains("table-toolbar")) toolbar.remove();
  delete analysisTable.dataset.enhanced;
  if (typeof ajouterOutilsTable === "function") ajouterOutilsTable(analysisTable);
}

// Envoie les filtres et affiche la reponse de l'API.
async function submitAnalysis(event) {
  event?.preventDefault();
  if (!analysisForm.reportValidity()) return;
  setAnalysisMessage("Chargement des données Data Ameli...");
  const params = new URLSearchParams(new FormData(analysisForm));
  const response = await fetch(`${analysisForm.dataset.url}?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok || !payload.pret) {
    setAnalysisMessage(payload.message || "Impossible de charger les données.", true);
    return;
  }

  updateAnalysisKpis(payload);
  updateAnalysisChart(payload.donnees);
  updateAnalysisTable(payload.donnees);
  const label = analysisConfig.kind === "pathologies" ? payload.pathologie : payload.poste || payload.type_honoraire;
  setAnalysisMessage(`${payload.profession ? `${payload.profession} - ` : ""}${label} - ${payload.territoire}.`);
  if (payload.erreur) setAnalysisMessage("Certaines données Data Ameli sont indisponibles pour cette sélection.", true);
}

if (analysisForm) {
  analysisRegion?.addEventListener("change", () => loadAnalysisDepartments().catch(() => setAnalysisMessage("Impossible de charger les départements.", true)));
  analysisForm.addEventListener("submit", submitAnalysis);
  loadAnalysisDepartments()
    .then(() => submitAnalysis())
    .catch(() => setAnalysisMessage("Impossible de charger les départements.", true));
}
