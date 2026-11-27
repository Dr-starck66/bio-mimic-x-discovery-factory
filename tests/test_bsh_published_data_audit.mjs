import assert from 'node:assert/strict';
import {auc,median,permutationP,bootstrapAuc,analyse,readCsv} from '../validation/bsh_published_data_audit.mjs';
import path from 'node:path';
assert.equal(auc([2,2],[1,2]),.75);
assert.equal(auc([2,2],[2,2]),.5);
assert.throws(()=>auc([],[1]),/Both nonempty/);
assert.throws(()=>auc([1],[NaN]),/Both nonempty/);
assert.equal(median([1,4,7,9]),5.5);
assert.ok(permutationP([4,5,6,7],[1,2,3,3],99)>0);
assert.deepEqual(bootstrapAuc([1,2,3,4,5],[0,0,0,0,0],99),[1,1]);
assert.throws(()=>analyse([],[],[]),/Unexpected Young count/);
const root=path.resolve(import.meta.dirname,'..');
const out=analyse(
 readCsv(path.join(root,'data/centenarian_2026_Fig2D_ln_cbh_recA.csv')),
 readCsv(path.join(root,'data/centenarian_2026_FigS2D_other_bile_genes.csv')),
 readCsv(path.join(root,'data/sardinia_2019_7ALPHADEHYDROX_59.csv'))
);
assert.equal(out.original.n,308);
assert.equal(out.independent_sardinia.n,59);
assert.ok(Math.abs(out.original.auc_centenarian_vs_elderly-0.6207201889020071)<1e-12);
assert.ok(Math.abs(out.original.candidate_gene_aucs.baiH-0.8354191263282172)<1e-12);
assert.ok(Math.abs(out.independent_sardinia.auc_centenarian_vs_elderly-0.5640732265446224)<1e-12);
assert.equal(out.independent_K01442_recA_validation,'UNVERIFIED');
console.log('PASS: 8 unit assertions + 6 published-data integration assertions');
