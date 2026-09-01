"""Petit cache en memoire pour les appels a l'API."""

import time
from functools import wraps


def avec_cache(duree_vie_seconde=300):
    """Décorateur simple : mémorise le résultat d'une méthode pendant N secondes."""

    def decorateur(methode):
        """Cree un cache propre a la methode decoree."""
        memoire = {}

        @wraps(methode)
        def enveloppe(self, *args, **kwargs):
            """Retourne une valeur en cache ou execute la methode."""
            cle = (
                methode.__name__,
                args,
                tuple(sorted(kwargs.items())),
            )
            if cle in memoire:
                valeur, horodatage = memoire[cle]
                if time.time() - horodatage <= duree_vie_seconde:
                    return valeur
                del memoire[cle]

            resultat = methode(self, *args, **kwargs)
            memoire[cle] = (resultat, time.time())
            return resultat

        return enveloppe

    return decorateur
