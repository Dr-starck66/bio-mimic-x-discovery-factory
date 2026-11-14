# ASTRA OBESITY Ω — external replication and clinical collaboration brief

Date: 2026-11-14. Status **PREPARED_NOT_SENT**. Cost €0. No participants recruited, patient data collected, messages sent, or new automation created.

## Evidence to share (reproducible)

Repository draft PR: https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/pull/56  
Real official CDC 2021–2023 NHANES run: https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43640222018  
Evidence snapshot: `evidence/nhanes_2021_2023_run_43640222018.json`.

- 5,453 adults with complete data, 665 elevated HbA1c (≥6.5%) observations.
- Weighted out-of-masked-PSU AUC for elevated HbA1c: BMI-only 0.679019; BMI + waist/height 0.745322; +0.066303.
- BMI+age+sex 0.761921 vs BMI+waist/height+age+sex 0.781072; +0.019151.
- Waist-ratio negative shuffle AUC 0.677623.
- Cross-sectional **US-only** biomarker association, **NOT** clinical obesity diagnosis, therapeutic effect, causal inference, external validation, or proof of cure. No independent geographic test.
- Source XPT SHA-256, code and log links in PR. No participant-level data attached or shared.

## Verified partner shortlist

### Spain — Hospital del Mar Research Institute / CIBEROBN
Contact **Prof. Montserrat Fitó**, `mfito@researchmar.net`, verified from CCNIEC group directory updated Feb 2026: https://www.ccniec.cat/fitxa-grup/grup-de-recerca-risc-cardiovascular-i-nutricio/ . The directory documents CIBEROBN, PREDIMED-Plus and OBEMAR long-term bariatric cohort. **Ask for methodological critique and possibility of separately executed external replication**, NOT access to raw patient-identifiable data and NOT a promise of collaboration.

Suggested subject: *Propuesta de colaboración científica — validación externa de análisis metabólico (ASTRA OBESITY Ω)*

Hola profesora Fitó:

Estoy desarrollando un proyecto independiente y de código abierto de investigación computacional sobre obesidad y salud metabólica (ASTRA OBESITY Ω, dentro de BIO-MIMIC X).

Hemos ejecutado un primer análisis reproducible con datos públicos reales de NHANES 2021–2023 (5.453 adultos con datos completos). Para identificar HbA1c ≥6,5 %, la AUC ponderada fuera de muestra pasó de 0,679 con IMC solo a 0,745 al añadir el cociente cintura/estatura; el incremento fue menor (+0,019) al ajustar por edad y sexo. Se trata de una **asociación observacional**, no de un diagnóstico de obesidad clínica ni de una afirmación de eficacia terapéutica.

Código, controles negativos, huellas de los datos y límites: https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/pull/56

¿Podría su grupo valorar una breve revisión metodológica y, si fuera viable bajo sus procedimientos institucionales, una reproducción independiente sobre una cohorte europea, idealmente con antropometría y biomarcadores medidos? También nos interesa distinguir obesidad clínica, riesgo metabólico y resultados longitudinales, siguiendo un protocolo preregistrado.

No solicitamos datos personales de pacientes por correo ni acceso fuera de los cauces autorizados. Actualmente el proyecto no dispone de financiación adicional.

Muchas gracias por su atención.  
Atentamente,  
Equipo ASTRA OBESITY Ω / BIO-MIMIC X

### Korea — KNHANES cross-national researcher
Contact **Dong Keon Yon** at `yonkkang@gmail.com` (corresponding-author email stated in Joo et al., *Medicine* 2025, cross-national KNHANES/NHANES metabolic syndrome comparison): https://pmc.ncbi.nlm.nih.gov/articles/PMC12708160/ .

KNHANES official raw-data portal: https://knhanes.kdca.go.kr/knhanes/main.do . Portal announced additional release of 2022–2024 files on 31 July 2026; authorized sign-in, statistical-data user undertaking and security acknowledgement required. **Access not obtained.** Cost-free access is documented by KDCA statistics source; do not bypass access flows.

Suggested subject: *Independent KNHANES replication request — anthropometry and elevated HbA1c (open-source pilot)*

Dear Dr Yon,

I am reaching out about a small, independent open-source obesity and metabolic-risk research project, ASTRA OBESITY Ω (BIO-MIMIC X). Your published work comparing KNHANES and NHANES motivated a possible independent replication.

Our real-data pilot used CDC NHANES August 2021–August 2023, 5,453 complete-case adults. Weighted held-out AUC for HbA1c ≥6.5% was 0.679 with BMI alone and 0.745 after including waist-to-height ratio; incremental AUC after age and sex adjustment was 0.019. These are US cross-sectional associations, not a clinical diagnosis, causal effect or validated treatment.

Reproducible source, controls, provenance and limitations: https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/pull/56

Would you be willing to advise on the correct 2022–2024 KNHANES releases, anthropometry/HbA1c variable harmonization, sampling weights and institutional rules for a pre-specified external replication? An independent rerun of the public code under your team's own data access, with aggregate outputs only, would be particularly useful. I am not requesting participant-level records.

The project has no additional budget at this stage. Thank you for considering a short methodological exchange.

Kind regards,  
ASTRA OBESITY Ω / BIO-MIMIC X research project

### Europe — European Association for the Study of Obesity (EASO)
General secretariat: `enquiries@easo.org` officially listed https://easo.org/about-easo/contact-easo/ . Ask for an introduction to a methodological epidemiology team with a non-US measured anthropometry+biomarkers cohort and support interpreting clinical obesity definitions. Do not claim institutional sponsorship.

## Second independent resource

WHO NCD Microdata Repository: https://extranet.who.int/ncdsmicrodata/index.php/home ; listed 937 survey entries on 14 Nov 2026. The STEPS approach uses interviews, physical measures (step 2), and *when available* biochemical measures (step 3). Candidate cohorts require country-specific variable/codebook review and permission checks before inclusion. A glucose endpoint is not automatically equivalent to HbA1c ≥6.5%.

## External replication protocol — locked questions before data inspection

- **Primary hypothesis:** on a different-country population, adding waist-to-height ratio to BMI improves out-of-sample discrimination for pre-specified **measured** elevated HbA1c ≥6.5% (if available); same reported AUC and Brier methods, but apply correct dataset-specific sampling design, weights and stratification.
- **Primary comparator:** BMI alone. **Secondary comparator:** BMI+age+sex vs BMI+waist-to-height+age+sex. Negative control: shuffle waist/height **only within training folds and held-out folds**; assess distribution and subgroup calibration.
- **No outcome substitution without labeling:** if only fasting glucose, measured blood pressure, or another biomarker exists, analyze as a distinct pre-specified endpoint and DO NOT call it a direct NHANES HbA1c replication.
- **Design:** blind external dataset while locking feature engineering, thresholds and exclusions; avoid leakage by household/PSU; estimate uncertainty under the proper complex survey design, not simple PSU bootstrap used in pilot.
- **Governance:** partner downloads under their own authorization, runs code locally, returns deidentified aggregate sufficient statistics and a provenance manifest; no raw patient emails or GitHub commits. No prospective recruitment now.
- **Failure criterion:** null/worse adjusted discrimination; major calibration deterioration; missingness/selection bias compromising comparability; subgroup instability; input provenance or survey-design incompatibility. Negative outcomes retained.

## Proposed questionnaire — NOT deployed; two gates

**Stage A: collaborator/recruitment interest form, no health data.** Prior to any ethics-reviewed clinical protocol, ask only: (1) researcher/institution name and professional contact, (2) type of expertise (epidemiology/endocrinology/statistics/data stewardship), (3) dataset held or can access (no records supplied), (4) availability to review 15 minutes or rerun code, (5) consent to reply. This is not a health questionnaire and does not validate an obesity hypothesis.

**Stage B: partner-governed participant health survey — DRAFT ONLY** based on WHO STEPS, conditional on an approved protocol, appropriate ethics and data-protection route, and secure investigator-controlled storage. Proposed domains: 1. country/site and eligibility; 2. age, sex-related variables relevant to analysis; 3. measured height and weight (with date/instrument); 4. measured waist (standardized protocol); 5. lab-measured HbA1c and date/method; 6. current diabetes medication and recent treatment context; 7. clinician-adjudicated adiposity-related organ function/clinical diagnosis only where justified; 8. predeclared social/environmental confounders using validated instruments; 9. consent and withdrawal route; 10. sampling source, sampling weights, missingness and data quality.

**Never** send this draft public health form to random participants, collect medical records in Gmail, imply BMI-only clinical diagnosis, claim self-reported blood results are verified, or use adult methods on children. In France, health research may require CNIL formalities and ethics pathways depending on category; the research sponsor / DPO must determine it: https://www.cnil.fr/fr/recherches-sante-quelles-formalites . For a multi-country study the partner must establish applicable procedures separately.
