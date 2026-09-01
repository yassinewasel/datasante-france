// Cree les graphiques definis par chaque page de tableau de bord.
function renderDashboardCharts(configs) {
  if (!window.Chart || !Array.isArray(configs)) return;

  for (const config of configs) {
    const canvas = document.getElementById(config.id);
    if (!canvas) continue;
    new Chart(canvas, {
      type: config.type,
      data: config.data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: config.legend || "bottom" },
        },
        scales: config.scales || {},
      },
    });
  }
}

renderDashboardCharts(window.dashboardCharts);
