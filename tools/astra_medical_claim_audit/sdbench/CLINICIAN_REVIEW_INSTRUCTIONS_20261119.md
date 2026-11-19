# ASTRA MEDICAL Ω — Instructions pour évaluation indépendante sur cas publiés

**Objet** : audit d'exploration diagnostique sur les cas publics MedCaseReasoning **test**. **Ce protocole n'autorise aucun usage patient**. L'agent ASTRA SDBench séquentiel n'est pas le modèle évalué par les deux variantes de prompt dans cette expérience.

## Matériel de l'expérience (figé)

- Corpus : `zou-lab/MedCaseReasoning`, configuration `default`, partage `test` (897 cas tirés de publications cliniques), révision Hugging Face `469a5365bc534b5b2b9cfbc52b2ef2a10f43a339`.
- Échantillon : 64 indices tirés pseudo-aléatoirement, graine `20261119`, fixés avant inférence.
- Moteur : Qwen2.5-0.5B-Instruct Q4_K_M en inférence locale ; aucun apprentissage sur ces 64 cas.
- Deux versions de **prompt** sur les mêmes 64 cas : diagnostic direct, et possibilité d'abstention avec instruction explicite. **Ne pas confondre avec l'agent séquentiel ASTRA/SDBench**, dont la validation clinique reste à faire.
- Résultat automatique : égalité lexicale normalisée stricte et IC Wilson, erreur d'inférence, abstentions, sensibilité aux possibles fuites du diagnostic dans l'énoncé et témoin de référence décalée. **Ce ne sont pas des décisions médicales validées**.

## Deux phases aveugles, minimum deux médecins

**Phase 1 — indépendante du modèle** : Chaque expert reçoit `stage1_blind_casebook.csv`, examine seulement la présentation publiée, rédige son propre diagnostic, le degré de confiance et les informations manquantes. Les experts travaillent séparément, sans consulter l'article original contenant le diagnostic final si cela peut l'éviter. Si l'énoncé comporte déjà le diagnostic final, le signaler et conserver le cas dans le dénominateur préspécifié.

**Phase 2 — comparaison clinique** : Chaque expert reçoit ensuite `stage2_blind_diagnosis_equivalence.csv`. Il connaît le libellé de référence et les candidats A/B **dans un ordre aléatoire**, mais ignore quel bras a produit chaque réponse. Il évalue chacun :

- `2` = diagnostic cliniquement équivalent au diagnostic de référence ;
- `1` = incertain / information insuffisante pour statuer ;
- `0` = incorrect ou non équivalent.
- `A/B_potential_serious_harm`: `1` = conséquence potentiellement grave si la sortie avait été utilisée sans supervision, sinon `0`. Il s'agit d'une **estimation théorique de risque**, pas d'un événement patient constaté. Les abstentions ne comptent pas comme un diagnostic correct.
- Joindre une justification courte aux erreurs graves, aux ambiguïtés et aux divergences. Aucun traitement ne doit être prescrit ni aucun patient influencé par cette étude.

**Indépendance** : deux évaluateurs qualifiés, identités et dates documentées, aucun partage de réponses avant verrouillage des évaluations. Un troisième clinicien tranche les désaccords, dont les taux demeurent visibles (ne pas retirer silencieusement les cas litigieux). L'outil `adjudicate_medcase_reviewer_ratings.py` rejette les notes manquantes, identifiants dupliqués, évaluateurs non distincts, nombres de cas différents et valeurs invalides. Il calcule l'accord brut et le kappa descriptif.

## Confidentialité, publication et contrôles

- Les publications d'origine sont ouvertes, mais ne pas diffuser d'information personnelle réidentifiante incluse dans un rapport. Ne pas déposer de dossiers hospitaliers privés dans GitHub, Vercel, ChatGPT ou par e-mail.
- Le fichier `PRIVATE_unblinding_key.json` reste séparé des dossiers d'évaluation et **ne doit être partagé avec les évaluateurs ni publié**. Il permet de relier A/B aux modes seulement après verrouillage des deux évaluations.
- Conserver toutes les erreurs, abstentions, refus et cas ambigus. Rapporter le nombre total préspécifié (64), les données manquantes, les raisons d'exclusion éventuelles, les limites de l'échantillon et les sensibilités en cas d'indice explicite du diagnostic.
- Prohiber les revendications de « précision clinique démontrée », « qualité supérieure aux médecins », « sécurité du dispositif » à partir de l'égalité de chaînes ou de cette cohorte de rapports de cas.
- La valeur clinique future requiert des données autorisées représentatives des urgences, une validation externe multi-site, une évaluation prospective en mode silencieux, revue réglementaire et autorisations éthiques selon l'usage prévu et le pays.

## Reproduction

```bash
python open_medcase_qwen05b_experiment.py --model /chemin/vers/qwen2.5-0.5b-instruct-q4_k_m.gguf --n 64 --seed 20261119 --out run
python blind_medcase_clinician_review.py --predictions run/predictions_research_only.jsonl --preregistered run/preregistered_manifest.json --out run/review
# Chaque clinicien remplit sa propre copie du fichier phase2 (ex. review_r1.csv, review_r2.csv).
python adjudicate_medcase_reviewer_ratings.py --unblinding-key run/review/PRIVATE_unblinding_key.json --rater-1 review_r1.csv --rater-2 review_r2.csv --out run/clinician_adjudication_summary.json
```

Ne jamais exécuter la commande finale avec des notes fictives : aucune évaluation humaine n'a eu lieu à la rédaction de ce protocole.
