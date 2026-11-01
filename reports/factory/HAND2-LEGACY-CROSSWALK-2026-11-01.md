# BIO-MIMIC X — HAND2, audit scientifique contradictoire (2026-11-01)

## Preuve directe

- Exécution : [GitHub Actions #41317804506](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/41317804506) ; étape « Verify HAND2 historic gene ID and NCBI orthology » PASS informatique.
- [Reçu JSON source](HAND2-LEGACY-CROSSWALK-2026-11-01.json), SHA-256 canonique `d9804aadc994341f5dd54fa6b8d253977808a925fd69612ee685268f9a09edda`.
- GTF AmexT_v47/AmexG_v6.0-DD : SHA-256 `cc0c3c4e39f3afedcbe2bc5aad1d63fc461714aeb75051f4d109390455874c5d`; ancien locus `AMEX60DD030069`, `chr3q:632140538–632169448`, `+`.
- **Annotation contradictoire réelle** : `HAND1 [nr]|HAND2 [hs]` sur **le même locus**. Le nom HAND2 [hs] est un indice d'annotation, pas une correspondance de séquence déterministe.
- API NCBI : gène axolotl HAND2 `138516365` (taxon 8296) ; orthologue humain NCBI HAND2/Entrez `9464`, Ensembl `ENSG00000164107` — statut de la chaîne NCBI **PASS**.
- **AMEX60DD030069 ↔ NCBI Gene 138516365 : UNVERIFIED**, car l'alignement réciproque de séquences ou une référence de version d'assemblage explicitement reliée n'a pas été démontrée.

## Incidence sur la première analyse comparative

- L'ancienne analyse exploratoire axolotl–humain affichait HAND2 (ancien locus) `−0,0208`, sur un contraste **postérieur − antérieur** ; côté peau humaine J3 − intact `−0,1378`. Ces valeurs n'étaient pas directement comparables et la première ne doit plus être attribuée sans réserve à HAND2.
- La nouvelle validation exclut les locus dont le GTF contient des étiquettes de gènes contradictoires, et exige pour les quatre entrées GEO un SHA-256 identique à celui des téléchargements complets initialement vérifiés.
- Un nouveau run du 1er novembre a renvoyé **4 096 octets au lieu de la matrice GSE28914 attendue de 6 766 619 octets**. Le fichier possédait un en-tête gzip mais échouait à la décompression. Ce cas doit dorénavant être déclaré **PARTIAL_SOURCE_FAILURE**, jamais INPUT_VERIFIED.
- Les résultats historiques, y compris l'échec réplicatif préenregistré GSE74387, sont conservés, pas réétiquetés en PASS.

## Prochaine preuve nécessaire

Correspondance d'accession ou séquence, de manière réciproque et avec contrôles de paralogues, entre `AMEX60DD030069` et `138516365`. Demande technique préparée pour L. Otsuki (auteur de l'étude Hand2–Shh), non envoyée. Le rapprochement génétique, même réussi, ne démontrera **pas** la régénération de membres humains.

**Statut biologique : UNVERIFIED ; statut du contrôle logiciel : PASS avec anomalie d'entrée corrigée dans une PR distincte.**
