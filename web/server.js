// Serveur local sans dépendance : fichiers statiques + enregistrement des résultats.
import http from "node:http";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC = path.join(ROOT, "public");
const RESULTS = path.join(ROOT, "..", "results");
const PORT = Number(process.env.PORT) || 3000;
const MAX_BODY = 1_000_000;

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".py": "text/plain; charset=utf-8",
  ".svg": "image/svg+xml",
};

async function serveStatic(req, res) {
  const url = new URL(req.url, "http://localhost");
  let rel = decodeURIComponent(url.pathname);
  if (rel.endsWith("/")) rel += "index.html";
  const file = path.normalize(path.join(PUBLIC, rel));
  if (!file.startsWith(PUBLIC + path.sep)) return send(res, 403, "Interdit");
  try {
    const data = await fs.readFile(file);
    res.writeHead(200, {
      "Content-Type": MIME[path.extname(file)] || "application/octet-stream",
      "Cache-Control": "no-cache",
    });
    res.end(data);
  } catch {
    send(res, 404, "Introuvable");
  }
}

function send(res, status, body, type = "text/plain; charset=utf-8") {
  res.writeHead(status, { "Content-Type": type });
  res.end(body);
}

async function saveResult(req, res) {
  let size = 0;
  const chunks = [];
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_BODY) return send(res, 413, "Trop volumineux");
    chunks.push(chunk);
  }
  let report;
  try {
    report = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
  } catch {
    return send(res, 400, "JSON invalide");
  }
  const name = String(report.candidate || "candidat").replace(/[^\p{L}\p{N}]+/gu, "_").slice(0, 40) || "candidat";
  const stamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 14);
  const file = path.join(RESULTS, `${stamp}_${name}.json`);
  await fs.mkdir(RESULTS, { recursive: true });
  await fs.writeFile(file, JSON.stringify(report, null, 1), "utf-8");
  send(res, 200, JSON.stringify({ path: path.resolve(file) }), MIME[".json"]);
}

const server = http.createServer((req, res) => {
  const handler =
    req.method === "POST" && req.url === "/api/results" ? saveResult : req.method === "GET" || req.method === "HEAD" ? serveStatic : null;
  if (!handler) return send(res, 405, "Méthode non autorisée");
  handler(req, res).catch((err) => send(res, 500, String(err)));
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`Simulateur prêt : http://localhost:${PORT}`);
});
