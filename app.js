"use strict";

const registry = window.ORELYN_REGISTRY;
const translations = {
  "zh-CN": {
    "nav.registry":"数据注册表","nav.provenance":"溯源证据","nav.cli":"CLI 同步","nav.guide":"使用边界",
    "hero.titleStart":"公开数据只是起点。","hero.titleEm":"可溯源，才可使用。","hero.intro":"面向矿业数据的来源注册、许可复核、增量更新与可复算证据，不把公开可访问笼统表述为可任意使用。","hero.explore":"浏览数据注册表 ↓","hero.cli":"执行增量同步","evidence.subtitle":"历史项目证据，不代表实时服务连接。","metric.layers":"治理图层","metric.rasters":"栅格图层","metric.checks":"对账检查","metric.evidence":"证据图层",
    "principle.public":"公开可访问","principle.publicText":"通过授权接口可以访问数据源。","principle.license":"使用授权","principle.licenseText":"独立审查许可、署名与使用限制。","principle.update":"更新证据","principle.updateText":"ETag、时间戳、字节数和 SHA-256 共同说明变化。",
    "registry.title":"先了解来源，再开始同步。","registry.intro":"每条记录分别标注访问方式、法律元数据、获取模式和证据日期，许可待复核的数据绝不自动下载。","search.placeholder":"搜索发布机构、数据集或类别…","filter.allLicenses":"全部许可状态","filter.open":"开放许可元数据","filter.review":"需要复核","filter.allCategories":"全部类别","filter.sync":"仅看可直接同步","registry.snapshot":"注册表快照 · 2026-11-02","table.source":"数据源","table.access":"访问方式","table.license":"许可","table.review":"复核周期","table.action":"操作","empty.title":"没有符合筛选条件的数据源。","empty.clear":"清除筛选",
    "license.title":"公开可读，不等于随意使用。","license.intro":"ORELYN 记录元数据以辅助复核，不替代法律意见或数据提供方的最新条款。","license.attribution":"署名是工作流的一部分","license.attributionText":"GA CSV 记录保留发布机构、许可地址与可复制的署名文本，供技术文章和派生成果使用。","license.services":"服务可访问不等于允许批量抓取","license.servicesText":"WFS 数据只标注有界查询，不把服务可用理解为无限制爬取的许可。","license.review":"元数据冲突会停止自动化","license.reviewText":"Copernicus 清单中存在 proprietary 标记，在数据集具体条款核对一致前，自动同步保持禁用。",
    "provenance.title":"成果应能解释自己如何形成。","provenance.intro":"Pine Creek 证据链以明确阶段和日期呈现历史验证，不用一句“数据已处理”掩盖过程。","lineage.acquire":"来源登记","lineage.acquireText":"登记 30 个源文件及其来源、访问方式和获取元数据。","lineage.clean":"治理与归一","lineage.cleanText":"通过记录的清洗与坐标规则派生 40 个图层和 19 个栅格。","lineage.store":"PostGIS 对账镜像","lineage.storeText":"治理文件与本地数据库之间完成 44/44 项检查。","lineage.publish":"本地 OGC 服务","lineage.publishText":"WMS 59/59、代表性 WFS 40/40 检查，不宣称已上线公有云。","lineage.evidence":"分析就绪证据","lineage.evidenceText":"20 个证据图层携带来源谱系进入后续矿业分析。",
    "cli.title":"低频监控，安全续传。","cli.intro":"CLI 使用条件请求和 Range 续传，不把部分文件标为完成，也不假定服务端一定支持续传。","cli.copy":"复制命令","state.title":"检查自己的同步证据","state.text":"选择 CLI 生成的 registry-state.json，文件只在浏览器本地读取，不会上传。","state.load":"载入 registry-state.json",
    "guide.title":"有用的自动化，始于清晰边界。","guide.intro":"ORELYN 是本地获取与证据工具，不是公共数据再分发服务，也不是法律判定引擎。","guide.authorized":"仅按授权获取","guide.authorizedText":"仅请求公开或授权端点，设置超时与有界并发，不绕过凭据控制。","guide.resume":"部分不等于完成","guide.resumeText":".part 文件表示未完成传输，只有完整响应才会计算哈希并移入只读源区。","guide.legal":"元数据不是法律意见","guide.legalText":"许可标签用于辅助复核，复用或发布前仍需确认提供方最新条款与署名义务。","guide.local":"本地证据，不是实时状态","guide.localText":"HTML 快照默认离线，只有显式运行 CLI 检查后才会报告实时可用性。"
  }
};

let elements;

function translated(key) {
  const language = elements.language.value;
  return translations[language]?.[key] || document.querySelector(`[data-i18n="${key}"]`)?.textContent || key;
}

function applyLanguage() {
  document.documentElement.lang = elements.language.value;
  document.querySelectorAll("[data-i18n]").forEach(element => {
    const key = element.dataset.i18n;
    if (!element.dataset.i18nDefault) element.dataset.i18nDefault = element.textContent.trim();
    element.textContent = translations[elements.language.value]?.[key] || element.dataset.i18nDefault;
  });
  document.querySelector("#source-search").placeholder = elements.language.value === "zh-CN" ? "搜索发布机构、数据集或类别…" : "Search publisher, dataset or category…";
  try { localStorage.setItem("orelyn.language", elements.language.value); } catch { /* optional storage */ }
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function sourceCode(source) {
  if (source.publisher.includes("Geoscience Australia")) return "GA";
  if (source.publisher.includes("Northern Territory")) return "NT";
  if (source.publisher.includes("AuScope")) return "AE";
  return "CO";
}

function renderSources() {
  const query = elements.search.value.trim().toLowerCase();
  const license = elements.license.value;
  const category = elements.category.value;
  const syncOnly = elements.sync.checked;
  const sources = registry.sources.filter(source => {
    const matchesQuery = !query || `${source.name} ${source.publisher} ${source.category}`.toLowerCase().includes(query);
    return matchesQuery && (license === "all" || source.licenseClass === license) && (category === "all" || source.category === category) && (!syncOnly || source.syncEnabled);
  });
  elements.rows.replaceChildren();
  for (const source of sources) {
    const row = element("tr");
    const nameCell = element("td");
    const nameWrap = element("div", "source-name");
    nameWrap.append(element("span", "source-icon", sourceCode(source)));
    const nameText = element("div");
    nameText.append(element("strong", "", source.name), element("small", "", source.publisher));
    nameWrap.append(nameText); nameCell.append(nameWrap);
    const accessCell = element("td");
    accessCell.append(element("div", "", source.access));
    accessCell.append(element("span", `sync-pill ${source.syncEnabled ? "enabled" : ""}`, source.syncEnabled ? "DIRECT SYNC" : "QUERY ONLY"));
    const licenseCell = element("td");
    licenseCell.append(element("span", `license-pill ${source.licenseClass === "review" ? "review" : ""}`, source.license));
    const cycleCell = element("td", "", `${source.reviewCycleDays} days`);
    const actionCell = element("td");
    const button = element("button", "detail-button", elements.language.value === "zh-CN" ? "查看" : "Details");
    button.type = "button"; button.addEventListener("click", () => showSource(source));
    actionCell.append(button);
    row.append(nameCell, accessCell, licenseCell, cycleCell, actionCell);
    elements.rows.append(row);
  }
  elements.count.textContent = `${sources.length} / ${registry.sources.length} sources`;
  elements.empty.hidden = sources.length > 0;
}

function fact(label, value, link = null) {
  const box = element("div");
  box.append(element("span", "", label));
  if (link) {
    const anchor = element("a", "", value);
    anchor.href = link; anchor.target = "_blank"; anchor.rel = "noopener noreferrer";
    box.append(anchor);
  } else box.append(element("strong", "", value));
  return box;
}

async function copyText(text, confirmation = "Copied") {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const area = document.createElement("textarea"); area.value = text; document.body.append(area); area.select();
    document.execCommand("copy"); area.remove();
  }
  const toast = document.querySelector("#toast"); toast.textContent = confirmation; toast.hidden = false;
  window.setTimeout(() => { toast.hidden = true; }, 1800);
}

function showSource(source) {
  elements.dialogContent.replaceChildren();
  const kicker = element("span", "dialog-source-kicker", `${source.category} / ${source.access}`);
  const title = element("h2", "dialog-source-title", source.name);
  const publisher = element("p", "dialog-publisher", source.publisher);
  const facts = element("div", "dialog-facts");
  facts.append(
    fact("LICENSE", source.license, source.licenseUrl),
    fact("ATTRIBUTION", source.attribution),
    fact("REVIEW CYCLE", `${source.reviewCycleDays} days`),
    fact("EVIDENCE DATE", source.evidenceDate),
    fact("ACCESS", source.access, source.endpoint),
    fact("SYNC POLICY", source.syncEnabled ? "Incremental download enabled" : "Bounded query only"),
  );
  const note = element("p", "dialog-note", source.usageNote);
  const actions = element("div", "dialog-actions");
  const citation = element("button", "button primary", "Copy attribution"); citation.type = "button";
  citation.addEventListener("click", () => copyText(`${source.name} — ${source.attribution}. ${source.license}. ${source.endpoint}`, "Attribution copied"));
  const endpoint = element("button", "button secondary", "Copy endpoint"); endpoint.type = "button";
  endpoint.addEventListener("click", () => copyText(source.endpoint, "Endpoint copied"));
  actions.append(citation, endpoint);
  elements.dialogContent.append(kicker, title, publisher, facts, note, actions);
  elements.dialog.showModal();
}

function initializeFilters() {
  const categories = [...new Set(registry.sources.map(source => source.category))].sort();
  for (const category of categories) elements.category.append(element("option", "", category));
  elements.category.value = "all";
  [elements.search, elements.license, elements.category, elements.sync].forEach(control => control.addEventListener("input", renderSources));
  document.querySelector("#clear-filters").addEventListener("click", () => {
    elements.search.value = ""; elements.license.value = "all"; elements.category.value = "all"; elements.sync.checked = false; renderSources();
  });
  document.querySelector("#close-dialog").addEventListener("click", () => elements.dialog.close());
  elements.dialog.addEventListener("click", event => { if (event.target === elements.dialog) elements.dialog.close(); });
}

function initializeStateImport() {
  const input = document.querySelector("#state-file");
  document.querySelector("#load-state").addEventListener("click", () => input.click());
  input.addEventListener("change", async () => {
    const file = input.files[0];
    if (!file) return;
    try {
      const state = JSON.parse(await file.text());
      const summary = document.querySelector("#state-summary");
      summary.replaceChildren();
      summary.append(element("strong", "", `Snapshot: ${state.generatedAt || "unknown"}`));
      const checks = Object.keys(state.checks || {}).length;
      const downloads = Object.keys(state.downloads || {}).length;
      summary.append(element("span", "", `${checks} endpoint checks · ${downloads} downloaded source records · local file only`));
      summary.hidden = false;
    } catch {
      const summary = document.querySelector("#state-summary");
      summary.textContent = "Invalid registry-state.json";
      summary.hidden = false;
    }
  });
}

function initialize() {
  elements = {
    rows: document.querySelector("#source-rows"), count: document.querySelector("#registry-count"),
    search: document.querySelector("#source-search"), license: document.querySelector("#license-filter"),
    category: document.querySelector("#category-filter"), sync: document.querySelector("#sync-filter"),
    empty: document.querySelector("#empty-state"), dialog: document.querySelector("#source-dialog"),
    dialogContent: document.querySelector("#dialog-content"), language: document.querySelector("#language-select"),
  };
  let saved = "en";
  try { saved = localStorage.getItem("orelyn.language") || "en"; } catch { /* optional storage */ }
  elements.language.value = saved === "zh-CN" ? "zh-CN" : "en";
  elements.language.addEventListener("change", () => { applyLanguage(); renderSources(); });
  applyLanguage();
  initializeFilters();
  renderSources();
  initializeStateImport();
  document.querySelector("#copy-commands").addEventListener("click", () => copyText("python cli.py check\npython cli.py sync --source ga-particle-size\npython cli.py status\npython cli.py watch --interval-hours 24", "Commands copied"));
}

document.addEventListener("DOMContentLoaded", () => {
  try { initialize(); } catch (error) { console.error(error.stack); throw error; }
});
