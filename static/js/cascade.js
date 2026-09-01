// Gere la liste des departements apres le choix d'une region.
const regionSelect = document.getElementById("region");
const departementSelect = document.getElementById("departement");

window.regionSelect = regionSelect;
window.departementSelect = departementSelect;

async function chargerDepartements(regionId) {
  // Charge les departements de la region choisie dans le select.
  departementSelect.innerHTML = '<option value="">Toute la région</option>';
  departementSelect.disabled = true;

  if (!regionId) {
    departementSelect.innerHTML = '<option value="">-- Choisir une région --</option>';
    return;
  }

  const modeleUrl = regionSelect.dataset.departementsUrl;
  const url = modeleUrl.replace(/0$/, regionId);
  const reponse = await fetch(url);
  const departements = await reponse.json();

  for (const departement of departements) {
    const option = document.createElement("option");
    option.value = departement.id;
    option.dataset.code = departement.code;
    option.dataset.regionId = departement.region_id;
    option.textContent = `${departement.code} - ${departement.libelle}`;
    departementSelect.appendChild(option);
  }

  departementSelect.disabled = false;
  departementSelect.dispatchEvent(new CustomEvent("departements:loaded", {
    detail: { regionId, departements },
  }));
  return departements;
}

if (regionSelect && departementSelect) {
  departementSelect.disabled = true;
  regionSelect.addEventListener("change", (event) => {
    chargerDepartements(event.target.value).catch(() => {
      departementSelect.innerHTML = '<option value="">Erreur de chargement</option>';
    });
  });
}

window.chargerDepartements = chargerDepartements;
