// Tests run against the engine exactly as shipped in index.html: the script is
// sliced out of the page and evaluated, so the page and the tests cannot drift.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const html = fs.readFileSync(path.join(__dirname, "index.html"), "utf8");
const start = html.indexOf("var WEIGHTS");
const end = html.indexOf("/* ---------- formatting ---------- */");
assert.ok(start > 0 && end > start, "engine section not found in index.html");
const E = {};
vm.runInNewContext(html.slice(start, end) +
  "\n;Object.assign(out,{evaluate,rank,sweep,npv,irr,example,WEIGHTS,ANCHORS});",
  { out: E });

const G = { gate: 30000, laborRate: 38, discountRate: 0.12 };
// Values built inside the vm carry that realm's prototypes; copy them into this
// realm before deep comparison.
const host = (v) => JSON.parse(JSON.stringify(v));

test("NPV and IRR match closed-form answers", () => {
  const pvf = (1 - Math.pow(1.1, -5)) / 0.1;
  assert.ok(Math.abs(E.npv(1000, 5, 0.1, 1000 * pvf)) < 1e-9);
  assert.ok(Math.abs(E.irr(1000, 5, 1000 * pvf) - 0.10) < 1e-9);
  // -1000 + 1000/(1+r) + 1000/(1+r)^2 = 0  =>  r = golden ratio - 1
  assert.ok(Math.abs(E.irr(1000, 2, 1000) - (Math.sqrt(5) - 1) / 2) < 1e-9);
  assert.equal(E.irr(100, 5, 600), null, "never recovers outlay");
  assert.equal(E.irr(-50, 5, 100), null, "negative cash flow");
});

test("worked example: gate excludes the deburr station, bar feeder wins", () => {
  const res = E.rank(E.example(), G);
  assert.deepEqual(host(res.ranked.map(r => r.name)), [
    "Used bar feeder, Gen 2 lathe",
    "Pallet-change fixturing, VMC #3",
    "In-process vision gauging",
    "Collaborative robot cell",
  ]);
  assert.deepEqual(host(res.excluded.map(r => r.name)), ["Automated deburr station"]);
  const cobot = res.ranked.find(r => r.name === "Collaborative robot cell");
  assert.ok(cobot.I / G.gate > 0.97, "cobot consumes >97% of the gate");
  assert.equal(res.ranked[0].unspent, 14400);
});

test("weak options cannot change anyone else's score (absolute anchors)", () => {
  const base = E.rank(E.example(), G).ranked.map(r => [r.name, r.score]);
  const decoy = { name: "Decoy", capital: 29000, install: 900, training: 0,
    recurringPerYear: 5000, hoursSavedPerWeek: 1, scrapReductionPerYear: 0,
    addedUnitsPerYear: 0, marginPerUnit: 0, life: 5 };
  const padded = E.rank([...E.example(), decoy], G).ranked
    .filter(r => r.name !== "Decoy").map(r => [r.name, r.score]);
  assert.deepEqual(host(padded), host(base));
});

test("gate, bounds and strict-dominance invariants hold on random instances", () => {
  let seed = 20260917;
  const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  const pick = (a, b) => a + rnd() * (b - a);
  const opt = () => ({ name: "x",
    capital: pick(3000, 32000), install: pick(0, 4000), training: pick(0, 2000),
    recurringPerYear: pick(0, 3000), hoursSavedPerWeek: pick(0, 14),
    scrapReductionPerYear: pick(0, 10000), addedUnitsPerYear: pick(0, 400),
    marginPerUnit: pick(0, 40), life: Math.round(pick(3, 12)) });
  let dominantPairs = 0;
  for (let t = 0; t < 40000; t++) {
    const a = E.evaluate(opt(), G), b = E.evaluate(opt(), G);
    for (const r of [a, b]) {
      if (r.I > G.gate) assert.equal(r.score, null, "over-gate option was scored");
      else assert.ok(r.score >= 0 && r.score <= 100, "score out of [0,100]");
    }
    if (a.gated || b.gated) continue;
    const ia = a.irr ?? -1, ib = b.irr ?? -1;
    if (a.I <= b.I && a.payback <= b.payback && a.npv >= b.npv && ia >= ib) {
      dominantPairs++;
      assert.ok(a.score >= b.score - 1e-9, "dominated option outranked its dominator");
    }
  }
  assert.ok(dominantPairs > 1000, `too few dominant pairs exercised (${dominantPairs})`);
});

test("sweep covers 125 cases and accounts for every one", () => {
  const sw = E.sweep(E.example(), G);
  assert.equal(sw.cases, 125);
  const won = sw.tally.reduce((s, t) => s + t[1], 0);
  assert.equal(won + sw.none, 125);
  assert.equal(sw.tally[0][0], "Used bar feeder, Gen 2 lathe");
});
