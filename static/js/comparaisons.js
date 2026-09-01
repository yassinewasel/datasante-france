// Gere les deux jeux de filtres et les graphiques de comparaison.
const comparisonForm = document.getElementById("comparison-form");
const comparisonStatus = document.getElementById("comparison-status");
const regionA = document.getElementById("compare-region-a");
const regionB = document.getElementById("compare-region-b");
const deptA = document.getElementById("compare-dept-a");
const deptB = document.getElementById("compare-dept-b");
const comparisonTableBody = document.querySelector("#comparison-table tbody");

// Cree un graphique Chart.js pour une mesure de comparaison.
function comparisonChart(id, type, label) {
  const canvas = document.getElementById(id);
  if (!canvas || !window.Chart) return null;
  return new Chart(canvas, {
    type,
    data: { labels: [], datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
      scales: {
        x: { title: { display: true, text: type === "line" ? "Année" : "Série" } },
        y: { beginAtZero: true, title: { display: true, text: label } },
      },
    },
  });
}

const effectifChart = comparisonChart("comparisonEffectif", "bar", "Effectif");
const evolutionChart = comparisonChart("comparisonEvolution", "line", "Effectif");
const sexesChart = comparisonChart("comparisonSexes", "bar", "Effectif");
const agesChart = comparisonChart("comparisonAges", "bar", "Effectif");

// Charge les departements pour une des deux series.
async function loadDepartments(regionSelect, departmentSelect) {
  departmentSelect.innerHTML = '<option value="">Toute la région</option>';
  departmentSelect.disabled = true;
  if (!regionSelect.value) return;
  const response = await fetch(comparisonForm.dataset.departementsUrl.replace(/0$/, regionSelect.value));
  const departments = await response.json();
  for (const department of departments) {
    const option = document.createElement("option");
    option.value = department.id;
    option.textContent = `${department.code} - ${department.libelle}`;
    departmentSelect.appendChild(option);
  }
  departmentSelect.disabled = false;
}

// Met a jour les graphiques complementaires de comparaison.
function updateComparisonCharts(payload) {
  if (effectifChart) {
    effectifChart.data.labels = payload.derniers.map((row) => row.label);
    effectifChart.data.datasets = [{ label: "Effectif", data: payload.derniers.map((row) => row.effectif), backgroundColor: ["#53bd7f", "#63b9eb"], borderRadius: 6 }];
    effectifChart.update();
  }
  if (evolutionChart) {
    evolutionChart.data.labels = payload.annees;
    evolutionChart.data.datasets = payload.series.map((serie, index) => ({
      label: serie.label,
      data: serie.donnees,
      borderColor: index === 0 ? "#0d7a8c" : "#ef8278",
      backgroundColor: "transparent",
      tension: .3,
    }));
    evolutionChart.update();
  }
  const sharedDatasets = (repartition) => payload.series.map((serie, index) => ({
    label: serie.label,
    data: index === 0 ? repartition.a : repartition.b,
    backgroundColor: index === 0 ? "#0d7a8c" : "#ef8278",
    borderRadius: 5,
  }));
  if (sexesChart) {
    sexesChart.data.labels = payload.repartitions.sexes.labels.map((label) => label.charAt(0).toUpperCase() + label.slice(1));
    sexesChart.data.datasets = sharedDatasets(payload.repartitions.sexes);
    sexesChart.update();
  }
  if (agesChart) {
    agesChart.data.labels = payload.repartitions.ages.labels;
    agesChart.data.datasets = sharedDatasets(payload.repartitions.ages);
    agesChart.update();
  }
}

// Affiche les valeurs annuelles des deux series.
function updateComparisonTable(rows) {
  comparisonTableBody.innerHTML = rows.map((row) => `<tr><td>${row.annee}</td><td>${row.effectif_a}</td><td>${row.densite_a}</td><td>${row.effectif_b}</td><td>${row.densite_b}</td></tr>`).join("");
}

// Envoie les deux selections et affiche les resultats.
async function compareSeries(event) {
  event?.preventDefault();
  if (!comparisonForm.reportValidity()) return;
  comparisonStatus.textContent = "Chargement des deux séries Data Ameli...";
  comparisonStatus.classList.remove("error-status");
  const params = new URLSearchParams(new FormData(comparisonForm));
  const response = await fetch(`${comparisonForm.dataset.url}?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok || !payload.pret) {
    comparisonStatus.textContent = payload.message || "Impossible de charger la comparaison.";
    comparisonStatus.classList.add("error-status");
    return;
  }
  updateComparisonCharts(payload);
  updateComparisonTable(payload.table);
  comparisonStatus.textContent = payload.erreur ? "Certaines données sont indisponibles pour cette comparaison." : `Période comparée : ${payload.periode.debut} à ${payload.periode.fin}.`;
  comparisonStatus.classList.toggle("error-status", Boolean(payload.erreur));
}

if (comparisonForm) {
  regionA.addEventListener("change", () => loadDepartments(regionA, deptA));
  regionB.addEventListener("change", () => loadDepartments(regionB, deptB));
  comparisonForm.addEventListener("submit", compareSeries);
  Promise.all([loadDepartments(regionA, deptA), loadDepartments(regionB, deptB)]).then(() => compareSeries());
}
