# ASTRA DEEP GEO Ω — Exploitation de l'avis OOI / HITL (17 novembre 2026)

## Réponse scientifique exploitée

Michael F. Vardaro (OOI, réponse Gmail du 17/11/2026) recommande de ne **pas** considérer un code QARTOD=1 comme une preuve de validité suffisante si les annotations humaines (*HITL*, human-in-the-loop) signalent une défaillance de capteur, une fluctuation de puissance, un bruit anormal ou un défaut de déploiement.

Source officielle à récupérer et conserver avec empreinte SHA-256 (ne pas inventer le contenu) :
https://dataexplorer.oceanobservatories.org/#metadata/104335/station/2004/sensor/annotations?start=2014-09-27T06:46:00Z&end=2026-11-17T11:43:00Z&leg_clim_max=false&leg_clim_min=false&leg_minmax=false

Instrument ciblé : **Escargot RS03INT1-MJ03C-10-TRHPHA301**, et non Diva TRHPHA302.

## Implémentation et contrôle négatif

- `validation/ooi_hitl_gate.py` **réutilise** `validation/ooi_axial_hydrothermal.py` existant, sans dupliquer le moteur de QARTOD ou de calcul des anomalies.
- Exporte une fenêtre de temps de l'annotation en UTC, en imposant le format epoch-millisecondes ou horodatage ISO avec fuseau.
- Compare l'identité du capteur, refuse les identifiants étrangers, et exclut les points QARTOD=1 recouverts par une annotation de QC 2/3/4/9 ou sans QC explicite.
- Un exemple synthétique d'une annotation en échec chevauchant 3 échantillons initialement QARTOD PASS retire **les 3 échantillons**.
- Refuse la déclaration de résultat scientifique si les annotations réelles ou le NetCDF réel sont absents.
- Rapporte séparément les empreintes de la mesure originale et du fichier d'annotations ; aucune attribution volcanique.

## Preuves à ne pas confondre

- `python -m unittest discover -s tests -p 'test_ooi_hitl_gate.py' -q` exécuté localement : **14 tests / 14 PASS** (données synthétiques, tests de fonction).
- GitHub readback des deux fichiers nouveaux : empreintes Git blob vérifiées.
- NetCDF public original et annotations humaines authentiques : **NON TÉLÉCHARGÉS dans cette session**, empêchés par un problème d'accès réseau/DNS.
- Fonctionnement complet sur échantillon réel, événements thermiques/volcaniques : **UNVERIFIED**.

## Protocole exact du prochain contrôle réel

1. Exporter le JSON officiel des annotations de l'instrument 301, en incluant plages `beginDT/endDT`, `qcFlag`, métadonnées et provenance.
2. Exécuter `python validation/ooi_hitl_gate.py --input <fichier_original_epingle.nc> --annotations <export_officiel.json> --annotation-source-url https://dataexplorer.oceanobservatories.org/ --out reports/factory/OOI-ESCARGOT-HITL-QC.json`.
3. Conserver le reçu comprenant les empreintes SHA, le nombre d'exclusions HITL et les candidats statistiques; vérifier les contrôles négatifs, jamais de nouvelle éruption affirmée sans corroboration physique.

**Statut : PASS logiciel local / PARTIAL intégration / UNVERIFIED mesures réelles.**
