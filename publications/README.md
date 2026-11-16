# ASTRA Ω Research — Publications scientifiques

**Auteur : Dr Starck.** Les prépublications ci-dessous sont publiques sous licence **CC BY 4.0 pour le texte original seulement**. Elles ne sont **pas** évaluées par les pairs.

## Catalogue des DOI individuels vérifiés

| Travail scientifique | DOI de version | PDF directement lisible |
|---|---|---|
| SciFact — audit de vérification des affirmations scientifiques (v0.5) | [10.5281/zenodo.24262786](https://doi.org/10.5281/zenodo.24262786) | [Manuscrit source](2026-11-15-scifact-audit-dr-starck.md) ; le dépôt Zenodo d'origine contient uniquement une archive ZIP |
| Quantum Gate Ω — comparaison QAOA / MaxCut (v0.1) | [10.5281/zenodo.24264255](https://doi.org/10.5281/zenodo.24264255) | [PDF GitHub](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/releases/download/astra-quantum-maxcut-preprint-v0.1/preprint.pdf) |
| ANT Robotics Ω — journaux de construction robotisée Stuttgart (v0.1) | [10.5281/zenodo.24264285](https://doi.org/10.5281/zenodo.24264285) | [PDF GitHub](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/releases/download/astra-ant-stuttgart-preprint-v0.1/preprint.pdf) |

### Citations conseillées

- Dr Starck (2026). *Oracle-Free Retrieval and Selective Scientific-Claim Verification: A Reproducible SciFact Development-Set Audit*. Zenodo. https://doi.org/10.5281/zenodo.24262786
- Dr Starck (2026). *Stress-testing idealized QAOA against classical heuristics on 70 seeded weighted MaxCut graphs: a reproducibility and cost-accounting audit*. Zenodo. https://doi.org/10.5281/zenodo.24264255
- Dr Starck (2026). *Limits of retrospective robot-task duration calibration and causal dispatch inference in open collective robotic construction logs*. Zenodo. https://doi.org/10.5281/zenodo.24264285

## IMPORTANT — Un DOI concept commun ne signifie pas un seul travail

Les trois DOI de version ci-dessus sont distincts, **PASS DataCite** (statut `findable`, créateur Dr Starck, titres vérifiés). Mais l'intégration automatique GitHub–Zenodo a attribué à ces trois dépôts de release **le même DOI concept** `10.5281/zenodo.24262785`. Ce DOI concept représente alors incorrectement une lignée de versions regroupant trois travaux scientifiques indépendants, et ses métadonnées peuvent pointer vers le dernier titre publié. **Ne pas citer ce DOI concept pour identifier SciFact, Quantum Gate ou ANT Robotics séparément.**

Pour les **prochaines publications indépendantes**, interdire une nouvelle release scientifique sur ce dépôt Zenodo partagé. Publier via un enregistrement Zenodo indépendant, ou via **un dépôt GitHub distinct et une intégration Zenodo activée pour ce dépôt**, afin de garantir un DOI concept distinct par travail. L'archive Github automatique peut comporter uniquement un ZIP, même quand le ZIP renferme le PDF. La présence d'un PDF **directement accessible sur la fiche Zenodo** doit être contrôlée avant toute affirmation de conformité.

Ce problème de regroupement des DOI est **PARTIAL — À CORRIGER DANS ZENODO** pour les records déjà déposés ; ne pas créer de faux nouveaux DOI ni modifier des métadonnées sans preuve.

## Incident Zenodo : ticket officiel et correction vérifiée (16 novembre 2026)

- **Ticket Zenodo Support #3331841** : le support a accusé réception, sans fournir encore de réparation. Délai indicatif annoncé : **3–4 semaines**, non une échéance garantie.
- **Trois releases GitHub corrigées en place** : ajout de leur DOI individuel, avertissement explicite de ne **pas** citer le DOI concept commun `10.5281/zenodo.24262785`, référence au ticket.
- **Preuve d'exécution** : [workflow de correction DOI du 16/11/2026](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43855086786), `success`, puis lecture indépendante des trois descriptions GitHub : **3/3 PASS**.
- **Aucun nouveau DOI généré** : modification de la description des releases existantes, **pas de nouvelle publication**.
- **Pas résolu dans Zenodo** : ses relations de version et le concept DOI sont toujours à traiter par l'opérateur Zenodo. Éviter suppression ou republication hâtive qui casserait des citations.
- [Documentation officielle Zenodo sur les versions et les DOI](https://help.zenodo.org/docs/deposit/manage-versions/). Pour un travail scientifique indépendant, créer une notice/famille distincte, non une version supplémentaire d'un autre article.

## Provenance et audits

- [SciFact — release](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/releases/tag/scifact-open-preprint-v0.5) · [audit Zenodo](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43766637916)
- [Quantum Gate — release](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/releases/tag/astra-quantum-maxcut-preprint-v0.1) · [workflow PDF (quantum)](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43771403148)
- [ANT Robotics — release](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/releases/tag/astra-ant-stuttgart-preprint-v0.1) · [workflow PDF corrigé](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43771538891)
- [Source antérieure SciFact, audit et protocoles — PR #48](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/pull/48)

## Limites scientifiques

Aucun des travaux n'a été examiné par des pairs. Quantum Gate concerne un simulateur CPU, pas un avantage quantique ; ANT Robotics est une étude observationnelle, pas un gain d'ordonnancement réel ; SciFact n'a ni réplication aveugle ni validation clinique.
