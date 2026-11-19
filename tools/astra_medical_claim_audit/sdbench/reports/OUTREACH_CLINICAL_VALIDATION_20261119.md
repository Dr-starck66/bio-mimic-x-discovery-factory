# ASTRA MEDICAL Ω — registre de contacts scientifiques

**Date de l'action :** 19 novembre 2026. **Statut :** six envois Gmail confirmés par l'API (libellé `SENT`). La réception effective, la réponse et l'accord des destinataires ne sont **PAS confirmés**. Aucun dossier patient transféré. Les messages présentent les résultats négatifs et distinguent essais logiciel/synthétiques, étude exploratoire de cas publiés et validation clinique non démontrée.

| Contact vérifié | Adresse | Rôle demandé | ID Gmail envoyé | Confirmation |
|---|---|---|---|---|
| Direction Recherche et Innovation, CHU Montpellier | sec-recherche@chu-montpellier.fr | Recherche d'investigateur et étude sous autorisation | `1a1f16b46b973e68` | SENT |
| URCE méthodologie, CHU Montpellier | consulmethodo@chu-montpellier.fr | Plan d'étude, revue statistique et cadre éthique | `1a1f16b4ceefeb09` | SENT |
| Équipe scientifique MedCaseReasoning, Stanford | stanfordmedeval@gmail.com | Relecture des équivalences diagnostiques | `1a1f16b50385f934` | SENT |
| Professeur James Zou, Stanford | jamesz@stanford.edu | Conseils de validation indépendante / collaboration | `1a1f16b57b5f79bb` | SENT |
| Harsha Nori, Microsoft Research | hanori@microsoft.com | Protocole réel SDBench, juges, données et revue clinique | `1a1f16c7ad896f32` | SENT |
| Service de médecine interne, Centre hospitalier de Perpignan (à l'attention du Dr Rodérau Outh) | consultation.medecineinterne@ch-perpignan.fr | Double lecture clinique des 64 cas publics et investigateur local | `1a1f16c8142d2751` | SENT |

## Sources publiques pour vérifier les adresses

- CHU Montpellier, DRI : https://www.chu-montpellier.fr/fr/recherche-et-innovation/notre-organisation/structures-support/dri
- CHU Montpellier, URCE : https://www.chu-montpellier.fr/fr/recherche-et-innovation/notre-organisation/structures-support/unite-de-recherche-clinique-et-epidemiologie-urce
- Stanford MedCaseReasoning : https://github.com/kevinwu23/Stanford-MedCaseReasoning
- Stanford James Zou : https://dbds.stanford.edu/people/james-zou/
- Microsoft Harsha Nori : https://www.microsoft.com/en-us/research/people/hanori/
- Centre hospitalier de Perpignan, médecine interne : https://www.ch-perpignan.fr/annuaires/annuaire-des-services-137/medecine-interne-90.html

## Limites et suites de l'action

- **Envoi : PASS** via Gmail, étiquette `SENT` et identifiants de messages ci-dessus.
- **Délivrabilité effective / accusé de lecture : UNVERIFIED**.
- **Réponse, partenariat, accès aux données cliniques ou avis médical : UNVERIFIED**.
- **Financement, contrat, autorisation réglementaire et validation clinique : NON ACQUIS**.
- Aucun envoi supplémentaire automatique créé. Éviter les relances multiples non souhaitées et préserver l'indépendance des évaluateurs.

**Résultats communiqués sans embellissement :** 128 inférences de Qwen sur 64 cas publiés, deux variantes de prompt avec chacune 2 concordances textuelles strictes sur 64, 6 abstentions dans la variante à garde, 0 amélioration diagnostique mesurée, limites d'une comparaison lexicale. L'agent séquentiel ASTRA reste non validé sur des données cliniques réelles.
