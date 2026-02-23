import * as pdfjsLib from "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs";

const sampleReports = [
  {
    source: "ISAO Weekly Bulletin",
    incident: "Credential phishing campaign against remote access portals",
    threatActor: "Silent Lynx",
    industry: "Financial Services",
    severity: 4,
    confidence: 0.85
  },
  {
    source: "MSSP Incident Advisory",
    incident: "Ransomware intrusion using exposed RDP",
    threatActor: "Night Coil",
    industry: "Healthcare",
    severity: 5,
    confidence: 0.9
  }
];

const reportInput = document.getElementById("reportInput");
const pdfInput = document.getElementById("pdfInput");
const urlInput = document.getElementById("urlInput");
const loadSampleBtn = document.getElementById("loadSampleBtn");
const generateBtn = document.getElementById("generateBtn");
const errorText = document.getElementById("errorText");
const warningList = document.getElementById("warningList");
const aggregationSummary = document.getElementById("aggregationSummary");
const riskStatements = document.getElementById("riskStatements");
const incidentTableBody = document.getElementById("incidentTableBody");

const severityPatterns = [
  { regex: /(critical|ransomware|data exfiltration|wiper)/i, value: 5 },
  { regex: /(privilege escalation|active exploitation|supply chain)/i, value: 4 },
  { regex: /(phishing|credential theft|malware|remote access trojan)/i, value: 3 },
  { regex: /(scanning|reconnaissance|probe)/i, value: 2 }
];

function toPercent(decimal) {
  return `${Math.round(decimal * 100)}%`;
}

function cleanText(text) {
  return text.replace(/\s+/g, " ").trim();
}

function inferSeverity(text) {
  for (const rule of severityPatterns) {
    if (rule.regex.test(text)) return rule.value;
  }
  return 3;
}

function inferConfidence(text) {
  if (/confirmed|verified|observed/i.test(text)) return 0.85;
  if (/likely|probable|suggests/i.test(text)) return 0.7;
  if (/possible|suspected|unconfirmed/i.test(text)) return 0.55;
  return 0.65;
}

function inferThreatActor(text) {
  const match = text.match(/\b(?:APT\s?\d+|Lazarus|FIN\d+|Volt Typhoon|Silent Lynx|Night Coil)\b/i);
  return match ? match[0] : "Unknown actor";
}

function inferIndustry(text) {
  const knownIndustries = [
    "Healthcare",
    "Financial Services",
    "Manufacturing",
    "Retail",
    "Government",
    "Energy",
    "Education"
  ];

  const found = knownIndustries.find((industry) => new RegExp(industry, "i").test(text));
  return found || "Cross-sector";
}

function inferIncident(text) {
  const sentences = cleanText(text).split(/(?<=[.!?])\s+/);
  return sentences.find((s) => s.length > 20)?.slice(0, 180) || "Threat activity observed across source material";
}

function normalizeReport(report, fallbackSource = "User JSON") {
  return {
    source: report.source || fallbackSource,
    incident: report.incident || "Threat activity observed",
    threatActor: report.threatActor || "Unknown actor",
    industry: report.industry || "Cross-sector",
    severity: report.severity,
    confidence: report.confidence
  };
}

function aggregateReports(reports) {
  const actorCounts = new Map();
  const industryCounts = new Map();

  let totalSeverity = 0;
  let totalConfidence = 0;

  reports.forEach((report) => {
    totalSeverity += report.severity;
    totalConfidence += report.confidence;
    actorCounts.set(report.threatActor, (actorCounts.get(report.threatActor) || 0) + 1);
    industryCounts.set(report.industry, (industryCounts.get(report.industry) || 0) + 1);
  });

  const topActor = [...actorCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || "N/A";
  const topIndustry = [...industryCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || "N/A";

  return {
    incidents: reports.length,
    avgSeverity: reports.length ? (totalSeverity / reports.length).toFixed(2) : "0.00",
    avgConfidence: reports.length ? totalConfidence / reports.length : 0,
    topActor,
    topIndustry
  };
}

function createRiskStatements(reports, aggregate) {
  const highSeverity = reports.filter((r) => r.severity >= 4).length;
  const strongConfidence = reports.filter((r) => r.confidence >= 0.7).length;

  return [
    `The merged corpus produced ${aggregate.incidents} incidents with average severity ${aggregate.avgSeverity}/5 and confidence ${toPercent(aggregate.avgConfidence)}. Risk exposure is elevated and requires ongoing executive oversight.`,
    `The most repeated actor is ${aggregate.topActor}; prioritize detection logic and hunt playbooks aligned to this actor profile.`,
    `${highSeverity} incidents are high severity (4-5), indicating potential for disruptive business impact if controls are not hardened quickly.`,
    `${strongConfidence} incidents have at least 70% confidence, giving enough evidence to action mitigation plans in ${aggregate.topIndustry}.`
  ];
}

function renderSummary(aggregate) {
  const items = [
    { label: "Incidents", value: aggregate.incidents },
    { label: "Avg Severity", value: `${aggregate.avgSeverity}/5` },
    { label: "Avg Confidence", value: toPercent(aggregate.avgConfidence) },
    { label: "Top Actor", value: aggregate.topActor },
    { label: "Top Industry", value: aggregate.topIndustry }
  ];

  aggregationSummary.innerHTML = items
    .map(
      (item) => `
      <article class="summary-item">
        <h3>${item.label}</h3>
        <p>${item.value}</p>
      </article>
    `
    )
    .join("");
}

function renderStatements(statements) {
  riskStatements.innerHTML = statements.map((s) => `<li>${s}</li>`).join("");
}

function renderTable(reports) {
  incidentTableBody.innerHTML = reports
    .map(
      (r) => `
      <tr>
        <td>${r.source}</td>
        <td>${r.incident}</td>
        <td>${r.threatActor}</td>
        <td>${r.industry}</td>
        <td>${r.severity}</td>
        <td>${toPercent(r.confidence)}</td>
      </tr>
    `
    )
    .join("");
}

function validateReport(report, index) {
  const requiredFields = ["severity", "confidence"];
  for (const field of requiredFields) {
    if (!(field in report)) {
      throw new Error(`JSON report ${index + 1} is missing required field: ${field}`);
    }
  }

  if (typeof report.severity !== "number" || report.severity < 1 || report.severity > 5) {
    throw new Error(`JSON report ${index + 1} has invalid severity. Use a number between 1 and 5.`);
  }

  if (typeof report.confidence !== "number" || report.confidence < 0 || report.confidence > 1) {
    throw new Error(`JSON report ${index + 1} has invalid confidence. Use a number between 0 and 1.`);
  }
}

function parseJsonReports(input) {
  if (!input.trim()) return [];
  const reports = JSON.parse(input);
  if (!Array.isArray(reports)) throw new Error("JSON input must be an array.");

  reports.forEach((report, index) => validateReport(report, index));
  return reports.map((r) => normalizeReport(r));
}

async function extractPdfText(file) {
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  const chunks = [];

  for (let i = 1; i <= pdf.numPages; i += 1) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const text = content.items.map((item) => item.str).join(" ");
    chunks.push(text);
  }

  return cleanText(chunks.join(" "));
}

async function parsePdfReports(files) {
  const reports = [];
  for (const file of files) {
    const text = await extractPdfText(file);
    reports.push({
      source: `PDF: ${file.name}`,
      incident: inferIncident(text),
      threatActor: inferThreatActor(text),
      industry: inferIndustry(text),
      severity: inferSeverity(text),
      confidence: inferConfidence(text)
    });
  }
  return reports;
}

async function fetchUrlText(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  const html = await response.text();
  const doc = new DOMParser().parseFromString(html, "text/html");
  const title = doc.querySelector("title")?.textContent || "Untitled source";
  const bodyText = cleanText(doc.body?.textContent || "").slice(0, 5000);
  return { title, text: `${title}. ${bodyText}` };
}

async function parseUrlReports(urlText) {
  const urls = urlText
    .split("\n")
    .map((url) => url.trim())
    .filter(Boolean);

  const warnings = [];
  const reports = [];

  for (const url of urls) {
    try {
      const payload = await fetchUrlText(url);
      reports.push({
        source: `URL: ${url}`,
        incident: inferIncident(payload.text),
        threatActor: inferThreatActor(payload.text),
        industry: inferIndustry(payload.text),
        severity: inferSeverity(payload.text),
        confidence: inferConfidence(payload.text)
      });
    } catch (error) {
      warnings.push(`Could not parse ${url}: ${error.message}`);
    }
  }

  return { reports, warnings };
}

function renderWarnings(warnings) {
  warningList.innerHTML = warnings.map((warning) => `<li>${warning}</li>`).join("");
}

async function generateFromInput() {
  errorText.textContent = "";
  renderWarnings([]);

  try {
    const jsonReports = parseJsonReports(reportInput.value);
    const pdfReports = await parsePdfReports(pdfInput.files);
    const urlResult = await parseUrlReports(urlInput.value);

    const reports = [...jsonReports, ...pdfReports, ...urlResult.reports];

    if (!reports.length) {
      throw new Error("Provide at least one JSON report, PDF, or URL.");
    }

    const aggregate = aggregateReports(reports);
    const statements = createRiskStatements(reports, aggregate);

    renderSummary(aggregate);
    renderStatements(statements);
    renderTable(reports);
    renderWarnings(urlResult.warnings);
  } catch (error) {
    aggregationSummary.innerHTML = "";
    riskStatements.innerHTML = "";
    incidentTableBody.innerHTML = "";
    errorText.textContent = error.message;
  }
}

loadSampleBtn.addEventListener("click", () => {
  reportInput.value = JSON.stringify(sampleReports, null, 2);
  urlInput.value = "https://www.cisa.gov/news-events/cybersecurity-advisories";
  renderWarnings([]);
});

generateBtn.addEventListener("click", () => {
  generateFromInput();
});

reportInput.value = JSON.stringify(sampleReports, null, 2);
generateFromInput();
