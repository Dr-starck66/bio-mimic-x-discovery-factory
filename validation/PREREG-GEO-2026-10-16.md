# ASTRA BIO-MIMIC X — pré-enregistrement validation sur données expérimentales externes
Date : 2026-10-16. **Enregistré avant téléchargement / examen des valeurs d'expression et avant résultats**.

## Objet et frontière de preuve
Vérifier dans de véritables échantillons biologiques publics si une métrique pré-définie de réponse transcriptomique différencie la souris régénérative Acomys du modèle cicatriciel Mus. **Réanalyse rétrospective de véritables expériences effectuées par des tiers** et non expérience nouvelle au laboratoire, ni démonstration de nouveauté du logiciel.

## Cohortes figées
- Cohorte principale : GSE74387 (microarray ; Acomys et Mus, contrôle sans blessure jour 0, plaie jour 7 et 14 ; ~5-6 réplicats / groupe).
- Réplication sur technologie différente : GSE113081 (RNA-seq ; Acomys et Mus, jours 0,7,14 ; ~3-4 réplicats / groupe, exclure Mus_Day-0_rep3 tel que signalé par les auteurs).
- Autre validation indépendante de laboratoire à évaluer séparément : GSE159938, seulement si le design contient des points temporels harmonisables. Jamais substituer cette cohorte si le test principal échoue.

## Hypothèse et critère principal fixés à l'avance
Hypothèse : le fractionnement des gènes/probes dont le signal de réponse à la blessure se rapproche du niveau basal entre le jour 7 et le jour 14 est plus élevé chez Acomys que chez Mus.

Pour chaque espèce et chaque feature mesuré en trois points temporels, normaliser à l'intérieur de l'espèce et calculer les moyennes biologiques. Une feature est dite « réponse en résolution » si |mean(log2 expression jour14) - mean(log2 expression jour0)| < |mean(jour7) - mean(jour0)|. Ignorer une feature si |mean(jour7) - mean(jour0)| < 0.25 unités log2 (bruit). Critère principal = proportion résolue Acomys moins proportion résolue Mus sur features qualifiées.

- RNA-seq : log2(CPM+1) avec filtrage CPM>1 dans ≥3 échantillons de chaque espèce; si données raw count des deux espèces non compatibles, normaliser **séparément** chaque espèce (ne jamais comparer intensités absolues entre espèces).
- Microarray : valeurs déjà normalisées de la matrice GEO; détecter et journaliser l'échelle et refuser si impossible d'inférer le log2; aucune transformation opportuniste.
- Exiger ≥3 réplicats dans chacune des six cellules espèce x temps et ≥1000 features analysables par espèce.
- Estimer l'incertitude avec 1000 rééchantillonnages d'échantillons par cellule; afficher IC95% de delta. Ne pas considérer les gènes comme des réplications biologiques indépendantes.
- Pour annoncer « reproduit indépendamment » : delta>=0.05 dans chaque cohorte, les deux IC95% entièrement >0, et aucun drapeau qualité critique. Sinon FAIL/PARTIAL explicites. Ces seuils restent figés même si résultat non favorable.
- Aucune promotion biologique si les jeux ont un problème majeur de comparabilité, d'annotation, de lots ou d'accès.
- Les résultats n'impliquent aucun lien causal, efficacité clinique, brevetabilité ou découverte originale; les expériences source sont publiées et antérieures.

## Contrôles négatifs prévus
1. Mélanger à l'aveugle les étiquettes jour 7 et jour14 au sein de chaque espèce, puis recalculer (contrôle d'étiquette).
2. Si la composition d'échantillons est insuffisante, ne pas générer de score mais FAIL_PRECONDITION.
3. Hash SHA-256 de chaque entrée, code du programme, version, métadonnées et protocole.
4. Production automatique JSON / Markdown, y compris données manquantes et exclusions, sans sélection post hoc.

## Étape vers véritable preuve nouvelle
Seulement si le signal réplicatif est concluant : préenregistrer une perturbation ciblée de l'ECM + axe immunitaire, groupe contrôle et contrôle simple voie, critères d'arrêt, taille d'échantillon issue de puissance statistique, laboratoire tiers signataire et acquisition de nouveaux résultats à l'aveugle. Aucun laboratoire ni expérience prospective ne peut être déclaré exécuté sans signature et données authentifiables.
