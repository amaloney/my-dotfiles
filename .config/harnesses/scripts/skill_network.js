#!/usr/bin/env node
// Skill network visualizer: serves a sigma.js page + live /api/graph.
// Zero dependencies (node stdlib only). Usage: node skill_network.js [port]

const http = require("http");
const fs = require("fs");
const path = require("path");

const HARNESSES = path.join(process.env.HOME, ".config", "harnesses");
const SKILLS_DIR = path.join(HARNESSES, "skills");
const SCORES_FILE = path.join(HARNESSES, "vectors", "edge_scores.json");
const PORT = Number(process.argv[2]) || 7474;

const LINK_RE = /\[\[([a-z][a-z0-9/_-]*)\]\]/g;
const NEXT_RE = /next: `?(?:\[\[)?([a-z0-9/_-]+)/g;

const RANK_COLORS = {
  0: "#e6194b", // route
  1: "#3cb44b", // diagnose/plan
  2: "#4363d8", // create
  3: "#f58231", // audit
  4: "#911eb4", // hygiene
  5: "#42d4f4", // test
  6: "#f032e6", // verify/ship
};

function parseRanks() {
  const md = fs.readFileSync(path.join(HARNESSES, "handoff-contract.md"), "utf8");
  const ranks = {};
  for (const line of md.split("\n")) {
    const m = line.match(/^\|\s*(\d)\s*\|[^|]*\|(.+)\|/);
    if (!m) continue;
    for (const name of m[2].matchAll(/`([^`]+)`/g)) ranks[name[1]] = Number(m[1]);
  }
  return ranks;
}

function rankOf(name, ranks) {
  if (name in ranks) return ranks[name];
  for (const key of Object.keys(ranks)) {
    if (!key.endsWith("/*")) continue;
    const stem = key.slice(0, -2);
    if (name.startsWith(stem + "/") || name.startsWith(stem + "-")) return ranks[key];
  }
  return null;
}

function collectSkills(dir = SKILLS_DIR, prefix = "") {
  const skills = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (fs.existsSync(path.join(dir, entry.name, "SKILL.md"))) skills.push(rel);
    skills.push(...collectSkills(path.join(dir, entry.name), rel));
  }
  return skills;
}

function buildGraph(simThreshold) {
  const ranks = parseRanks();
  const skills = collectSkills().sort();
  const edges = [];
  const degree = Object.fromEntries(skills.map((s) => [s, 0]));

  for (const skill of skills) {
    const text = fs.readFileSync(path.join(SKILLS_DIR, skill, "SKILL.md"), "utf8");
    for (const m of text.matchAll(LINK_RE)) {
      if (m[1] !== skill && skills.includes(m[1])) {
        edges.push({ source: skill, target: m[1], type: "link" });
        degree[skill]++; degree[m[1]]++;
      }
    }
    for (const m of text.matchAll(NEXT_RE)) {
      if (m[1] !== "done" && m[1] !== skill && skills.includes(m[1])) {
        edges.push({ source: skill, target: m[1], type: "next" });
        degree[skill]++; degree[m[1]]++;
      }
    }
  }

  if (simThreshold && fs.existsSync(SCORES_FILE)) {
    const history = JSON.parse(fs.readFileSync(SCORES_FILE, "utf8"));
    const scores = history.snapshots.at(-1)?.scores ?? {};
    const existing = new Set(edges.map((e) => [e.source, e.target].sort().join("|")));
    for (const [pair, score] of Object.entries(scores)) {
      if (score >= simThreshold && !existing.has(pair)) {
        const [a, b] = pair.split("|");
        if (skills.includes(a) && skills.includes(b)) {
          edges.push({ source: a, target: b, type: "similarity", score });
        }
      }
    }
  }

  // Layout: column per rank (unranked at -0.7), vertical spread within rank
  const byRank = {};
  const nodes = skills.map((skill) => {
    const rank = rankOf(skill, ranks);
    const key = rank ?? "x";
    byRank[key] = byRank[key] ?? [];
    const node = {
      id: skill,
      label: skill,
      rank,
      degree: degree[skill],
      idx: byRank[key].length,
    };
    byRank[key].push(node);
    return node;
  });
  for (const group of Object.values(byRank)) {
    group.forEach((n, i) => {
      n.y = i - (group.length - 1) / 2;
    });
  }
  for (const n of nodes) n.x = n.rank === null ? -0.7 : n.rank;

  return { nodes, edges };
}

const PAGE = `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Skill Network</title>
<style>
  body { margin: 0; background: #111; color: #ddd; font: 13px/1.4 -apple-system, sans-serif; }
  #graph { position: fixed; inset: 0; }
  #panel { position: fixed; top: 10px; left: 10px; background: #1c1c1ecc; padding: 10px 14px; border-radius: 8px; }
  #panel label { display: block; margin-top: 6px; cursor: pointer; }
  .sw { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; }
  #sel { color: #fff; font-weight: 600; margin-top: 8px; }
</style>
</head>
<body>
<div id="graph"></div>
<div id="panel">
  <b>Skill Network</b>
  <div id="legend"></div>
  <label><input type="checkbox" id="links" checked> [[reference]] edges</label>
  <label><input type="checkbox" id="nexts" checked> next: handoff edges</label>
  <label><input type="checkbox" id="sims"> similarity candidates (&ge; <input id="simt" value="0.5" size="3">)</label>
  <div id="sel">&nbsp;</div>
</div>
<script src="https://unpkg.com/graphology@0.25.4/dist/graphology.umd.min.js"></script>
<script src="https://unpkg.com/sigma@2.4.0/build/sigma.min.js"></script>
<script>
const RANK_COLORS = ${JSON.stringify(RANK_COLORS)};
const RANK_NAMES = ["route","plan","create","audit","hygiene","test","verify"];
document.getElementById("legend").innerHTML = RANK_NAMES.map((n, i) =>
  '<span class="sw" style="background:' + RANK_COLORS[i] + '"></span>' + n).join("<br>");

let graph, renderer, data;

async function load() {
  const sims = document.getElementById("sims").checked;
  const t = document.getElementById("simt").value || "0.5";
  const res = await fetch("/api/graph" + (sims ? "?similarity=" + t : ""));
  data = await res.json();

  graph = new graphology.Graph({ multi: true });
  for (const n of data.nodes) {
    graph.addNode(n.id, {
      label: n.label,
      x: n.x * 6, y: -n.y * 1.6,
      size: 4 + Math.min(n.degree, 20),
      color: n.rank === null ? "#666" : RANK_COLORS[n.rank],
    });
  }
  const showLinks = document.getElementById("links").checked;
  const showNexts = document.getElementById("nexts").checked;
  let i = 0;
  for (const e of data.edges) {
    const style = e.type === "next"
      ? { color: "#f5a623", size: 2.5 }
      : e.type === "similarity"
        ? { color: "#ffffff33", size: 1 }
        : { color: "#555", size: 1 };
    if (e.type === "link" && !showLinks) continue;
    if (e.type === "next" && !showNexts) continue;
    try { graph.addEdge(e.source, e.target, style); } catch {}
  }

  if (renderer) renderer.kill();
  renderer = new Sigma(graph, document.getElementById("graph"));

  renderer.on("clickNode", ({ node }) => {
    document.getElementById("sel").textContent = node + " (rank " + (data.nodes.find(n => n.id === node).rank ?? "—") + ")";
    renderer.setSetting("nodeReducer", (n, attrs) =>
      n === node || graph.hasEdge(n, node) || graph.hasEdge(node, n)
        ? attrs : { ...attrs, color: "#333", label: "" });
    renderer.setSetting("edgeReducer", (e, attrs) =>
      graph.extremities(e).includes(node) ? attrs : { ...attrs, color: "#222" });
  });
  renderer.on("clickStage", () => {
    document.getElementById("sel").innerHTML = "&nbsp;";
    renderer.setSetting("nodeReducer", null);
    renderer.setSetting("edgeReducer", null);
  });
}

for (const id of ["links", "nexts", "sims"]) document.getElementById(id).onchange = load;
document.getElementById("simt").onchange = load;
load();
</script>
</body>
</html>`;

http
  .createServer((req, res) => {
    const url = new URL(req.url, "http://x");
    if (url.pathname === "/api/graph") {
      const sim = url.searchParams.get("similarity");
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify(buildGraph(sim ? Number(sim) : null)));
    } else if (url.pathname === "/") {
      res.writeHead(200, { "content-type": "text/html" });
      res.end(PAGE);
    } else {
      res.writeHead(404).end("not found");
    }
  })
  .listen(PORT, () => console.log(`skill network: http://localhost:${PORT}`));
