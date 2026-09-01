// Synchronise la carte Leaflet avec les filtres region et departement.
const mapElement = document.getElementById("france-map");
const mapInfo = document.getElementById("map-info");
const selectedRegionDepts = document.getElementById("selected-region-depts");
const selectedRegionStats = window.regionStats || {};
const selectedDepartmentStats = window.departmentStats || {};

let franceMap = null;
let regionsLayer = null;
let departmentsLayer = null;
let selectedRegionLayer = null;
let selectedDepartmentLayer = null;

// Retourne une couleur stable pour une region.
function regionFill(index) {
  const colors = ["#7cc6d3", "#93bee2", "#78c995", "#71addd", "#a3c9ef"];
  return colors[index % colors.length];
}

// Retourne une couleur stable pour un departement.
function departmentFill(code) {
  const colors = ["#74b7dd", "#73c8d2", "#7acb96", "#9cc5ea", "#62b9c9", "#88bfe0"];
  const index = Number.parseInt(code, 10);
  return colors[Number.isNaN(index) ? 0 : index % colors.length];
}

// Met a jour le panneau de details de la carte.
function setInfoText(title, description, detailValue = "-") {
  if (!mapInfo) return;

  const titleElement = mapInfo.querySelector("strong");
  const descriptionElement = mapInfo.querySelector("small");

  if (titleElement) titleElement.textContent = title;
  if (descriptionElement) descriptionElement.textContent = description;
  if (selectedRegionDepts) selectedRegionDepts.textContent = detailValue;
}

// Affiche les informations de la region survolee ou selectionnee.
function updateRegionInfo(properties, selected = false) {
  const stats = selectedRegionStats[properties?.code] || {};
  const name = stats.libelle || properties?.nom || "Régions françaises";
  const departments = stats.departements ?? "-";
  const description = selected
    ? "La région est synchronisée avec les filtres. Choisissez un département pour affiner les résultats."
    : "Survolez ou sélectionnez une région pour consulter ses informations.";

  setInfoText(name, description, departments);
}

// Affiche les informations du departement survole ou selectionne.
function updateDepartmentInfo(properties, selected = false) {
  const stats = selectedDepartmentStats[properties?.code] || {};
  const code = stats.code || properties?.code || "";
  const name = stats.libelle || properties?.nom || "Département";
  const regionName = stats.region_libelle ? ` Région : ${stats.region_libelle}.` : "";
  const description = selected
    ? `Le département est sélectionné dans les filtres.${regionName}`
    : `Survolez ou sélectionnez ce département.${regionName}`;

  setInfoText(`${code} - ${name}`, description.trim(), code || "-");
}

// Trouve une option de region a partir de son code INSEE.
function findRegionOptionByCode(code) {
  if (!window.regionSelect) return null;
  return Array.from(regionSelect.options).find((option) => option.dataset.code === code);
}

// Trouve une option de region a partir de son identifiant interne.
function findRegionOptionById(id) {
  if (!window.regionSelect) return null;
  return Array.from(regionSelect.options).find((option) => option.value === String(id));
}

// Trouve une option de departement a partir de son code.
function findDepartmentOptionByCode(code) {
  if (!window.departementSelect) return null;
  return Array.from(departementSelect.options).find((option) => option.dataset.code === code);
}

// Retrouve la forme Leaflet d'une region.
function findRegionLayerByCode(code) {
  let match = null;
  regionsLayer?.eachLayer((layer) => {
    if (layer.feature?.properties?.code === code) {
      match = layer;
    }
  });
  return match;
}

// Retrouve la forme Leaflet d'un departement.
function findDepartmentLayerByCode(code) {
  let match = null;
  departmentsLayer?.eachLayer((layer) => {
    if (layer.feature?.properties?.code === code) {
      match = layer;
    }
  });
  return match;
}

// Retablit le style normal de la region precedente.
function clearRegionHighlight() {
  if (selectedRegionLayer && regionsLayer) {
    regionsLayer.resetStyle(selectedRegionLayer);
  }
  selectedRegionLayer = null;
}

// Retablit le style normal du departement precedent.
function clearDepartmentHighlight() {
  if (selectedDepartmentLayer && departmentsLayer) {
    departmentsLayer.resetStyle(selectedDepartmentLayer);
  }
  selectedDepartmentLayer = null;
}

// Met une region en evidence et peut centrer la carte.
function highlightRegionByCode(code, fitToBounds = false) {
  clearRegionHighlight();
  const layer = findRegionLayerByCode(code);
  if (!layer) return;

  selectedRegionLayer = layer;
  layer.setStyle({
    color: "#1f6f8d",
    weight: 3,
    fillOpacity: 0.18,
  });

  if (fitToBounds && franceMap) {
    franceMap.fitBounds(layer.getBounds(), { padding: [28, 28], maxZoom: 8 });
  }
}

// Met un departement en evidence et peut zoomer dessus.
function highlightDepartmentByCode(code, fitToBounds = false) {
  clearDepartmentHighlight();
  const layer = findDepartmentLayerByCode(code);
  if (!layer) return;

  selectedDepartmentLayer = layer;
  layer.setStyle({
    color: "#1f6f8d",
    weight: 3,
    fillColor: "#53bd7f",
    fillOpacity: 0.96,
  });
  layer.bringToFront();

  if (fitToBounds && franceMap) {
    franceMap.fitBounds(layer.getBounds(), { padding: [34, 34], maxZoom: 9 });
  }
}

// Applique le clic sur une region au formulaire.
function selectRegionFromMap(properties) {
  const option = findRegionOptionByCode(properties.code);
  if (!option || !window.regionSelect) {
    updateRegionInfo(properties);
    return;
  }

  regionSelect.value = option.value;
  regionSelect.dispatchEvent(new Event("change", { bubbles: true }));
  clearDepartmentHighlight();
  highlightRegionByCode(properties.code);
  updateRegionInfo(properties, true);
}

// Applique le clic sur un departement aux deux filtres.
async function selectDepartmentFromMap(properties) {
  const stats = selectedDepartmentStats[properties.code];
  if (!stats || !window.regionSelect || !window.departementSelect) {
    updateDepartmentInfo(properties);
    return;
  }

  const regionOption = findRegionOptionById(stats.region_id);
  if (regionOption) {
    regionSelect.value = regionOption.value;
    highlightRegionByCode(stats.region_code);
    await window.chargerDepartements?.(regionOption.value);
  }

  const departmentOption = findDepartmentOptionByCode(stats.code);
  if (departmentOption) {
    departementSelect.value = departmentOption.value;
    departementSelect.dispatchEvent(new Event("change", { bubbles: true }));
  }

  highlightDepartmentByCode(stats.code, true);
  updateDepartmentInfo(properties, true);
}

// Repercute le filtre region vers la carte.
function syncMapFromRegionFilter() {
  if (!window.regionSelect) return;
  const option = regionSelect.selectedOptions[0];
  const code = option?.dataset.code;

  clearDepartmentHighlight();
  if (!code) {
    clearRegionHighlight();
    setInfoText("Aucune sélection", "Le territoire choisi synchronise automatiquement les filtres.", "-");
    return;
  }

  highlightRegionByCode(code, true);
  updateRegionInfo({ code, nom: option.textContent }, true);
}

// Repercute le filtre departement vers la carte.
function syncMapFromDepartmentFilter() {
  if (!window.departementSelect) return;
  const option = departementSelect.selectedOptions[0];
  const code = option?.dataset.code;

  if (!code) {
    return;
  }

  const stats = selectedDepartmentStats[code];
  if (stats?.region_code) {
    highlightRegionByCode(stats.region_code);
  }
  highlightDepartmentByCode(code, true);
  updateDepartmentInfo({ code, nom: option.textContent.replace(/^\d+\s*-\s*/, "") }, true);
}

// Charge les GeoJSON et initialise les interactions Leaflet.
async function initFranceMap() {
  if (!mapElement || !window.L) return;

  franceMap = L.map(mapElement, {
    attributionControl: false,
    zoomControl: true,
    scrollWheelZoom: true,
    doubleClickZoom: true,
  });
  window.franceMap = franceMap;

  const [regionsGeojson, departmentsGeojson] = await Promise.all([
    fetch(mapElement.dataset.geojsonUrl).then((response) => response.json()),
    fetch(mapElement.dataset.departementsGeojsonUrl).then((response) => response.json()),
  ]);

  regionsLayer = L.geoJSON(regionsGeojson, {
    style: (feature) => ({
      color: "#7daac5",
      weight: 1.5,
      fillColor: regionFill(Number(feature.properties.code || 0)),
      fillOpacity: 0.08,
    }),
    onEachFeature: (feature, featureLayer) => {
      const properties = feature.properties;

      featureLayer.on("click", () => {
        selectRegionFromMap(properties);
      });
    },
  }).addTo(franceMap);

  departmentsLayer = L.geoJSON(departmentsGeojson, {
    style: (feature) => ({
      color: "#ffffff",
      weight: 1,
      fillColor: departmentFill(feature.properties.code),
      fillOpacity: 0.84,
    }),
    onEachFeature: (feature, featureLayer) => {
      const properties = feature.properties;

      featureLayer.bindTooltip(`${properties.code} - ${properties.nom}`, {
        direction: "top",
        sticky: true,
        className: "region-tooltip",
      });

      featureLayer.on({
        mouseover: () => {
          if (featureLayer !== selectedDepartmentLayer) {
            featureLayer.setStyle({ fillOpacity: 1, weight: 2 });
          }
          updateDepartmentInfo(properties);
        },
        mouseout: () => {
          if (featureLayer !== selectedDepartmentLayer) {
            departmentsLayer.resetStyle(featureLayer);
          }
        },
        click: () => {
          selectDepartmentFromMap(properties);
        },
      });
    },
  }).addTo(franceMap);

  franceMap.fitBounds(departmentsLayer.getBounds(), { padding: [18, 18] });
  franceMap.setMinZoom(franceMap.getZoom());
  franceMap.setMaxZoom(franceMap.getZoom() + 5);
  franceMap.dragging.enable();
  franceMap.touchZoom.enable();
  franceMap.boxZoom.enable();
  franceMap.keyboard.enable();

  regionSelect?.addEventListener("change", syncMapFromRegionFilter);
  departementSelect?.addEventListener("change", syncMapFromDepartmentFilter);
  departementSelect?.addEventListener("departements:loaded", syncMapFromDepartmentFilter);

  window.selectDepartmentOnMap = selectDepartmentFromMap;
  window.selectRegionOnMap = selectRegionFromMap;
}

initFranceMap().catch(() => {
  if (mapInfo) {
    setInfoText("Carte indisponible", "Les fichiers GeoJSON n'ont pas pu être chargés.", "-");
  }
});
