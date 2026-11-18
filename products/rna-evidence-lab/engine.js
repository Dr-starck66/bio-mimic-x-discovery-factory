'use strict';
/* BIO-MIMIC X RNA Evidence Lab — browser-local analysis, no third-party calls.
   This exploratory analysis is not DESeq2 and does not estimate gene-level FDR.
   Copyright 2026 BIO-MIMIC X. Research-use software only. */
(function (root) {
  const pick = xs => {
    const s = [...xs].sort((a, b) => a - b);
    return s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2;
  };
  const combinations = () => {
    const out = [];
    for (let a = 0; a < 6; a++)
      for (let b = a + 1; b < 6; b++)
        for (let c = b + 1; c < 6; c++) out.push([a, b, c]);
    return out;
  };
  const split = line => line.includes('\t') ? line.split('\t') : line.includes(';') ? line.split(';') : line.split(',');
  function parseCounts(source) {
    if (typeof source !== 'string' || source.length > 40_000_000) throw Error('Fichier texte vide ou supérieur à 40 Mo.');
    const lines = source.replace(/^\uFEFF/, '').trim().split(/\r?\n/).filter(x => x.trim() && !x.startsWith('#'));
    if (lines.length < 2 || lines.length > 150001) throw Error('Attendu : en-tête + 1 à 150 000 gènes.');
    const header = split(lines[0]).map(s => s.trim());
    if (header.length !== 7) throw Error('Format attendu : gene,control_1,control_2,control_3,case_1,case_2,case_3.');
    const rows = [], seen = new Set();
    for (let j = 1; j < lines.length; j++) {
      const cells = split(lines[j]).map(s => s.trim());
      if (cells.length !== 7) throw Error('Ligne ' + (j + 1) + ' : sept colonnes sont requises.');
      const id = cells[0];
      if (!id || seen.has(id)) throw Error('Ligne ' + (j + 1) + ' : identifiant absent ou dupliqué.');
      const counts = cells.slice(1).map(Number);
      if (counts.some(v => !Number.isSafeInteger(v) || v < 0)) throw Error('Ligne ' + (j + 1) + ' : comptages entiers positifs ou nuls uniquement.');
      seen.add(id); rows.push({ id, counts });
    }
    return { rows, samples: header.slice(1), genes: rows.length };
  }
  function analyze(matrix) {
    const { rows, samples } = matrix;
    if (!rows.length) throw Error('Aucun gène.');
    const totals = [0, 0, 0, 0, 0, 0], ratios = [[], [], [], [], [], []];
    for (const { counts } of rows) {
      for (let i = 0; i < 6; i++) totals[i] += counts[i];
      if (counts.every(v => v > 0)) {
        const gm = Math.exp(counts.reduce((s, v) => s + Math.log(v), 0) / 6);
        for (let i = 0; i < 6; i++) ratios[i].push(counts[i] / gm);
      }
    }
    if (!ratios[0].length || totals.some(x => x === 0)) throw Error('Impossible de normaliser : un groupe ou les gènes de référence sont vides.');
    const sizeFactors = ratios.map(pick);
    const normalized = rows.map(({ id, counts }) => ({ id, values: counts.map((v, i) => v / sizeFactors[i]) }));
    const effects = normalized.map(({ id, values }) => {
      const w = (values[0] + values[1] + values[2]) / 3;
      const z = (values[3] + values[4] + values[5]) / 3;
      const log2fc = Math.log2((z + 1) / (w + 1));
      const positive = Math.min(...values.slice(3)) > Math.max(...values.slice(0, 3));
      const negative = Math.max(...values.slice(3)) < Math.min(...values.slice(0, 3));
      const passes = (w + z) / 2 >= 10;
      const call = passes && log2fc >= 1 && positive ? 'UP' : passes && log2fc <= -1 && negative ? 'DOWN' : 'NONE';
      return { id, whole: w, caseMean: z, log2fc, call };
    });
    const positives = effects.filter(v => v.call === 'UP').length;
    const negatives = effects.filter(v => v.call === 'DOWN').length;
    const partitions = combinations().map(caseIdx => {
      const controlIdx = [0, 1, 2, 3, 4, 5].filter(i => !caseIdx.includes(i));
      let up = 0, down = 0;
      for (const { values } of normalized) {
        const a = caseIdx.map(i => values[i]);
        const b = controlIdx.map(i => values[i]);
        const am = (a[0] + a[1] + a[2]) / 3, bm = (b[0] + b[1] + b[2]) / 3;
        if ((am + bm) / 2 < 10) continue;
        if (Math.min(...a) > Math.max(...b) && am + 1 >= 2 * (bm + 1)) up++;
        if (Math.max(...a) < Math.min(...b) && bm + 1 >= 2 * (am + 1)) down++;
      }
      return { caseSamples: caseIdx.map(i => i + 1), up, down, total: up + down };
    });
    const observed = positives + negatives;
    const globalP = partitions.filter(row => row.total >= observed).length / 20;
    return {
      status: 'EXPLORATORY',
      version: 'RNA Evidence Lab v1.0',
      genes: rows.length, samples, totals, sizeFactors,
      allSixPositive: ratios[0].length,
      positives, negatives, partitions, globalP,
      effects: effects.filter(x => x.call !== 'NONE').sort((a, b) => Math.abs(b.log2fc) - Math.abs(a.log2fc)),
      limitations: [
        'Comparaison exploratoire de six échantillons seulement, sans correction FDR génique.',
        'Le test global bilatéral à 20 permutations possède une résolution minimale de p=0,10.',
        'Les fractions biologiques peuvent différer par composition, contamination et rendement d’extraction.',
        'Aucune causalité, performance clinique ou bénéfice thérapeutique n’est établi.'
      ]
    };
  }
  function syntheticCSV() {
    const lines = ['gene,whole_1,whole_2,whole_3,case_1,case_2,case_3'];
    for (let i = 0; i < 120; i++) {
      const b = 35 + ((i * 37) % 140);
      const ws = [b - 3, b + 1, b + 4];
      const cs = i < 15 ? [b * 7 - 2, b * 8, b * 8 + 3]
        : i < 30 ? [Math.floor(b / 8), Math.floor(b / 7), Math.floor(b / 6)]
        : [b + ((i * 3) % 17) - 8, b + ((i * 7) % 21) - 10, b + ((i * 11) % 19) - 9].map(v => Math.max(0, v));
      lines.push(['DEMO_' + String(i + 1).padStart(4, '0'), ...ws, ...cs].join(','));
    }
    return lines.join('\n');
  }
  function reportCSV(result) {
    const lines = ['gene,direction,log2_fc,mean_whole,mean_case'];
    for (const r of result.effects)
      lines.push([r.id, r.call, r.log2fc.toFixed(6), r.whole.toFixed(3), r.caseMean.toFixed(3)].join(','));
    return lines.join('\n');
  }
  root.RNAEvidence = { parseCounts, analyze, syntheticCSV, reportCSV };
})(globalThis);
