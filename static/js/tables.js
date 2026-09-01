// Transforme une cellule en nombre ou texte comparable.
function normaliserValeur(valeur) {
  const texte = valeur.trim().replace(/\s/g, "").replace(",", ".");
  const nombre = Number(texte);
  return Number.isNaN(nombre) ? valeur.trim().toLocaleLowerCase("fr") : nombre;
}

// Compare deux cellules pour le tri ascendant ou descendant.
function comparerCellules(a, b, direction) {
  const valeurA = normaliserValeur(a);
  const valeurB = normaliserValeur(b);
  if (typeof valeurA === "number" && typeof valeurB === "number") {
    return direction * (valeurA - valeurB);
  }
  return direction * String(valeurA).localeCompare(String(valeurB), "fr", { numeric: true });
}

// Trie les lignes suivant la colonne selectionnee.
function trierTable(table, index) {
  const tbody = table.tBodies[0];
  if (!tbody) return;
  const direction = table.dataset.sortIndex === String(index) && table.dataset.sortDirection === "asc" ? -1 : 1;
  const lignes = Array.from(tbody.rows);

  lignes.sort((ligneA, ligneB) => {
    const a = ligneA.cells[index]?.textContent || "";
    const b = ligneB.cells[index]?.textContent || "";
    return comparerCellules(a, b, direction);
  });

  tbody.append(...lignes);
  table.dataset.sortIndex = String(index);
  table.dataset.sortDirection = direction === 1 ? "asc" : "desc";

  table.querySelectorAll("th").forEach((th, thIndex) => {
    th.removeAttribute("aria-sort");
    th.classList.remove("sorted-asc", "sorted-desc");
    if (thIndex === index) {
      th.setAttribute("aria-sort", direction === 1 ? "ascending" : "descending");
      th.classList.add(direction === 1 ? "sorted-asc" : "sorted-desc");
    }
  });
}

// Convertit le contenu HTML d'un tableau en CSV.
function csvDepuisTable(table) {
  const lignes = Array.from(table.rows).map((row) =>
    Array.from(row.cells)
      .map((cell) => `"${cell.textContent.trim().replace(/"/g, '""')}"`)
      .join(";")
  );
  return lignes.join("\n");
}

// Cree puis telecharge le fichier CSV du tableau.
function telechargerTable(table) {
  const nom = table.dataset.tableName || "tableau";
  const blob = new Blob(["\ufeff" + csvDepuisTable(table)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const lien = document.createElement("a");
  lien.href = url;
  lien.download = `${nom}.csv`;
  document.body.appendChild(lien);
  lien.click();
  lien.remove();
  URL.revokeObjectURL(url);
}

// Ajoute le tri clavier/souris et le bouton d'export.
function ajouterOutilsTable(table) {
  if (table.dataset.enhanced === "true") return;
  table.dataset.enhanced = "true";
  table.classList.add("enhanced-table");

  table.querySelectorAll("thead th").forEach((th, index) => {
    th.tabIndex = 0;
    th.title = "Trier cette colonne";
    th.addEventListener("click", () => trierTable(table, index));
    th.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        trierTable(table, index);
      }
    });
  });

  const barre = document.createElement("div");
  barre.className = "table-toolbar";
  const aide = document.createElement("span");
  aide.textContent = "Cliquez sur une colonne pour trier";
  const bouton = document.createElement("button");
  bouton.type = "button";
  bouton.className = "secondary-button table-download";
  bouton.textContent = "Télécharger CSV";
  bouton.addEventListener("click", () => telechargerTable(table));
  barre.append(aide, bouton);
  table.parentNode.insertBefore(barre, table);
}

document.querySelectorAll("main table").forEach(ajouterOutilsTable);
