# BIO-MIMIC X — Audit épigénétique « de-aging » (1er novembre 2026)

## Étude originale

Berg et al., *Aging Cell* 25(10), e70751, 3 octobre 2026, DOI: [10.1111/acel.70751](https://doi.org/10.1111/acel.70751), texte intégral [PMC13634082](https://pmc.ncbi.nlm.nih.gov/articles/PMC13634082/).

**Observation publiée par les auteurs, non répliquée par BIO-MIMIC X :** conversion de progéniteurs érythroïdes humains en cellules souches neurales induites (iNSC) par SOX2/cMYC, associée à une forte diminution de l'âge estimé par méthylation de l'ADN. Ce n'est **ni** un rajeunissement humain de 61 ans **ni** une régénération de membre. La conversion modifie l'identité cellulaire ; l'horloge DNAm n'est qu'un marqueur de l'âge biologique.

## Provenance et accessibilité

- `GSE295849` — méthylation ADN ; cité dans la publication. Référence GEO, mais **intégrité des fichiers bruts non vérifiée ici** (l'accès web NCBI a retourné une page de vérification de navigateur).
- `E-MTAB-5808` — données de méthylation plus anciennes, citées par la publication ; **fichiers non téléchargés/contrôlés ici**.
- `phs004047.v1.p1` — ARN-seq via dbGaP : **accès autorisé requis** selon https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs004047.v1.p1 ; aucune tentative de contournement.
- `GSE74387` — contrôle antérieur défavorable de BIO-MIMIC X, conservé **FAIL** ; aucune substitution opportuniste des données.

## Protocole reproductible (sans faux positifs)

1. Obtenir légalement une matrice de méthylation *au niveau échantillon* avec provenance, métadonnées d'âge/donneur/temps et empreinte SHA-256 issue d'une acquisition vérifiée.
2. Exécuter `python validation/epigenetic_deaging_gate.py --local-gzip CHEMIN --sha256 EMPREINTE --min-bytes MINIMUM --out reports/factory/EPIGENETIC-DEAGING-LATEST.json`. Le « PASS_INTEGRITY_ONLY » éventuel prouve **uniquement** l'intégrité des octets, pas l'étude scientifique.
3. Recalculer les horloges DNAm avec les scripts/versions/sondes adéquats ; quantifier l'incertitude par donneur et passage, avec contrôles négatifs non reprogrammés, lots et qualité technique.
4. Pour les ponts vers l'axolotl, exiger preuves d'orthologie par séquences réciproques, exclusion des paralogues HAND1/HAND2, adéquation tissus/temps/modalités. Les anciens contrastes axolotl blastème vs peau humaine ne sont **pas** directement comparables.
5. Conserver tous les échecs (réplication, accès, tests négatifs). Une concordance de signatures ne prouve ni mécanisme causal ni traitement anti-âge.

## Statut

- Référence primaire/accès réglementé : vérifiés par lecture des sources.
- Éléments scientifiques calculés par BIO-MIMIC X : **UNVERIFIED**.
- Objectif de laboratoire humain/axolotl : **PARTIAL**, hypothèse à falsifier.
- Coûts nouveaux : **0 €** ; pas de GPU, nouveau cron, workflow ni accès non autorisé.
