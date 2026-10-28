(() => {
  const D = window.TM_DATA || { meta: {}, topics: [], docs: [] };
  const MIN_DATE = "2021-01-01";
  D.docs = D.docs.filter((d) => !d.date || d.date >= MIN_DATE);
  const PAGE = 40;
  const STAR_KEY = "tm_starred_v1";
  const COLORS = ["#2563eb", "#d13b3b", "#0f9960", "#7c3aed", "#b86e00", "#0e7490", "#be185d", "#4d7c0f", "#475569", "#c2410c"];
  const SORTS = {
    tender: [["date", "Дата публикации: сначала новые"], ["dateAsc", "Дата публикации: сначала старые"], ["price", "Цена: сначала дорогие"], ["priceAsc", "Цена: сначала дешёвые"]],
    patent: [["date", "Дата публикации: сначала новые"], ["dateAsc", "Дата публикации: сначала старые"]],
    stats: [["date", "—"]],
    star: [["starred", "Недавно добавленные"]],
  };

  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const topicInfo = Object.fromEntries(D.topics.map((t, i) => [t.id, { ...t, color: COLORS[i % COLORS.length] }]));
  const today = new Date().toISOString().slice(0, 10);

  // drill — переход из аналитики: заказчик/заявитель/тема/период
  const state = { tab: "stats", an: "all", shown: PAGE, drill: null };
  let stars = JSON.parse(localStorage.getItem(STAR_KEY) || "{}");
  const keyOf = (d) => `${d.type}:${d.source}:${d.source_id}`;

  // ---------- избранное: Firestore (общее для всех), иначе — localStorage этого браузера ----------
  const favs = (() => {
    if (!window.TM_FIREBASE || !window.firebase) return null;
    try {
      firebase.initializeApp(window.TM_FIREBASE);
      return firebase.firestore().collection("favorites");
    } catch (e) {
      console.warn("Firestore недоступен:", e);
      return null;
    }
  })();
  const favId = (key) => encodeURIComponent(key);
  function setStar(key, on) {
    if (on) stars[key] = { key, doc: D.docs.find((d) => keyOf(d) === key) || stars[key]?.doc, at: new Date().toISOString() };
    else delete stars[key];
    localStorage.setItem(STAR_KEY, JSON.stringify(stars));
    if (!favs) return;
    (on ? favs.doc(favId(key)).set(stars[key]) : favs.doc(favId(key)).delete())
      .catch((e) => toast(`Не удалось сохранить в облако: ${e.code || e.message}`));
  }

  const isNew = (d) => D.meta.updated && d.first_seen >= D.meta.updated;
  const isOpen = (d) => d.type === "tender" && d.deadline && d.deadline >= today && !/заверш|отмен|итоги/i.test(d.status || "");
  const daysLeft = (d) => Math.ceil((new Date(d.deadline) - new Date(today)) / 864e5);

  const ORG_FORMS = [
    [/федеральное государственное бюджетное образовательное учреждение высшего образования/gi, "ФГБОУ ВО"],
    [/федеральное государственное автономное образовательное учреждение высшего образования/gi, "ФГАОУ ВО"],
    [/федеральное государственное бюджетное учреждение науки/gi, "ФГБУН"],
    [/федеральное государственное бюджетное учреждение/gi, "ФГБУ"],
    [/федеральное государственное казенное учреждение/gi, "ФГКУ"],
    [/федеральное государственное унитарное предприятие/gi, "ФГУП"],
    [/федеральное государственное автономное учреждение/gi, "ФГАУ"],
    [/государственное бюджетное учреждение здравоохранения/gi, "ГБУЗ"],
    [/государственное бюджетное общеобразовательное учреждение/gi, "ГБОУ"],
    [/государственное бюджетное профессиональное образовательное учреждение/gi, "ГБПОУ"],
    [/государственное автономное учреждение/gi, "ГАУ"],
    [/государственное бюджетное учреждение/gi, "ГБУ"],
    [/государственное казенное учреждение/gi, "ГКУ"],
    [/государственное учреждение/gi, "ГУ"],
    [/муниципальное бюджетное общеобразовательное учреждение/gi, "МБОУ"],
    [/муниципальное автономное общеобразовательное учреждение/gi, "МАОУ"],
    [/муниципальное унитарное предприятие/gi, "МУП"],
    [/муниципальное казенное учреждение/gi, "МКУ"],
    [/публичное акционерное общество/gi, "ПАО"],
    [/акционерное общество/gi, "АО"],
    [/общество с ограниченной ответственностью/gi, "ООО"],
    [/индивидуальный предприниматель/gi, "ИП"],
  ];
  const shortOrg = (s) => ORG_FORMS.reduce((t, [re, abbr]) => t.replace(re, abbr), String(s || "")).replace(/\s*\((RU|[A-Z]{2})\)\s*$/, "").trim();

  function fmtDate(iso) {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" }).replace(" г.", "");
  }
  function fmtMoney(v, cur) {
    if (!v) return "";
    const sym = { RUB: "₽", EUR: "€", USD: "$" }[cur] || cur || "";
    const n = v >= 1e9 ? `${(v / 1e9).toLocaleString("ru-RU", { maximumFractionDigits: 2 })} млрд`
      : v >= 1e6 ? `${(v / 1e6).toLocaleString("ru-RU", { maximumFractionDigits: 2 })} млн`
      : Math.round(v).toLocaleString("ru-RU");
    return `${n} ${sym}`;
  }
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toast.t);
    toast.t = setTimeout(() => (t.hidden = true), 2000);
  }

  // ---------- шапка ----------
  const byType = (t) => D.docs.filter((d) => d.type === t);
  $("#updated").innerHTML = D.meta.updated
    ? `Обновлено<br><b>${new Date(D.meta.updated).toLocaleString("ru-RU", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" })}</b>`
    : "Данных нет — запустите collect.py";
  $("#stats").innerHTML = [["tender", byType("tender").length, "тендеров"], ["patent", byType("patent").length, "патентов"]]
    .map(([tab, n, label]) => `<div class="stat" data-go="${tab}"><b>${n.toLocaleString("ru-RU")}</b><span>${label}</span></div>`).join("");

  // ---------- выборка ----------
  function base(tab) {
    if (tab === "star") return Object.values(stars).map((s) => D.docs.find((d) => keyOf(d) === s.key) || s.doc);
    if (tab === "stats") return D.docs;
    return byType(tab);
  }

  const docDate = (d) => d.date || (d.first_seen || "").slice(0, 10);
  $("#dateFrom").max = $("#dateTo").max = today;

  function periodRange(tab) {
    if (tab === "star") return ["", ""];
    return [$("#dateFrom").value, $("#dateTo").value];
  }

  // усечение окончаний: «медицинский» → «медицин»
  function stem(w) {
    let s = w.toLowerCase();
    if (/^[a-z]+$/i.test(s)) {
      s = s.replace(/(?:ational|ing|ies|ied|es|ed|ly|s)$/i, "");
      return s.length >= 3 ? s : w.toLowerCase();
    }
    const endings = ["ыми", "ими", "ого", "ему", "ому", "ых", "их", "ое", "ее", "ая", "яя", "ые", "ие",
      "ой", "ый", "ий", "ою", "ею", "ом", "ем", "ам", "ям", "ах", "ях", "ов", "ев", "ью",
      "ия", "ии", "ию", "ей", "ую", "юю", "ск", "нн"];
    let changed = true;
    while (changed) {
      changed = false;
      for (const e of endings) {
        if (s.length - e.length >= 4 && s.endsWith(e)) { s = s.slice(0, -e.length); changed = true; break; }
      }
    }
    if (s.length >= 5 && /[аеёиоуыэюя]$/i.test(s)) s = s.slice(0, -1);
    return s.length >= 4 ? s : w.toLowerCase();
  }

  // синонимы: «дрон» = «БПЛА» = «UAV». Короткие аббревиатуры — только целое слово (иначе «бас»→«базовый»)
  const SYNONYMS = [
    ["дрон", "дроны", "дрона", "дронов", "дроном", "бпла", "бвс", "бас", "uav", "uas", "rpas",
      "беспилотник", "беспилотники", "беспилотный", "беспилотная", "беспилотное", "беспилотные",
      "квадрокоптер", "мультикоптер", "коптер", "fpv"],
    ["экзоскелет", "экзоскелеты", "exoskeleton", "exoskeletons"],
    ["робот", "роботы", "робототехника", "robot", "robots", "robotics", "роботизированный", "роботизированная"],
  ];
  const ABBR = new Set(["бпла", "бвс", "бас", "uav", "uas", "rpas", "fpv", "ртк"]);
  const SYNONYM_STEMS = SYNONYMS.map((g) => g.map((s) => ({ raw: s, st: stem(s) })));

  function expandToken(t) {
    const low = t.toLowerCase();
    const st = stem(low);
    if (/^дронопорт|^дронпорт|^droneport/.test(low)) return [st, low];
    for (const group of SYNONYM_STEMS) {
      if (group.some(({ raw, st: ss }) => low === raw || st === ss || (st.length >= 3 && ss.startsWith(st)))) {
        return [...new Set(group.flatMap(({ raw, st: ss }) => [ss, raw]))];
      }
    }
    return [st, low];
  }

  // индекс поиска один раз — иначе на каждую букву заново склеивается текст тысяч документов
  D.docs.forEach((d) => {
    const blob = [
      d.title, d.title_ru, d.summary, d.summary_ru, d.customer, d.number, d.source_id, d.status,
      (d.applicants || []).join(" "), (d.ipc || []).join(" "), (d.keywords || []).join(" "),
      (d.topics || []).map((t) => topicInfo[t]?.name || t).join(" "),
    ].join(" ").toLowerCase();
    const words = blob.split(/[^\p{L}\p{N}]+/u).filter(Boolean);
    d._blob = blob;
    d._words = words;
    d._stems = words.map(stem);
    d._wordSet = new Set(words);
  });

  function variantHit(d, v) {
    if (v.length < 2) return false;
    // аббревиатуры и очень короткие основы — только точное слово, не «бас» внутри «базовый»
    if (ABBR.has(v) || v.length <= 3) return d._wordSet.has(v);
    if (d._blob.includes(v)) return true;
    return d._words.some((w, i) => w.startsWith(v) || d._stems[i].startsWith(v));
  }

  function textHit(d, q) {
    if ((d._blob || "").includes(q)) return true;
    const tokens = q.split(/[^\p{L}\p{N}]+/u).filter((t) => t.length >= 2);
    if (!tokens.length) return true;
    return tokens.every((t) => expandToken(t).some((v) => variantHit(d, v)));
  }

  function filtered(tab, skip = "") {
    const q = $("#q").value.trim().toLowerCase();
    let [since, until] = periodRange(tab);
    const topic = skip === "topic" ? "" : $("#topic").value;
    const country = skip === "country" ? "" : $("#country").value;
    const source = skip === "source" ? "" : $("#source").value;
    const dr = state.drill;
    if (dr?.since && (!since || dr.since > since)) since = dr.since;
    if (dr?.until && (!until || dr.until < until)) until = dr.until;
    return base(tab).filter((d) =>
      (!since || docDate(d) >= since) && (!until || docDate(d) <= until) &&
      (!topic || d.topics.includes(topic)) &&
      (!country || d.country === country) &&
      (!source || d.source === source) &&
      (!dr?.customer || shortOrg(d.customer) === dr.customer) &&
      (!dr?.applicant || shortOrg((d.applicants || [])[0]) === dr.applicant) &&
      (!dr?.keyword || (d.keywords || []).some((k) => k.toLowerCase() === dr.keyword.toLowerCase()) || textHit(d, dr.keyword.toLowerCase())) &&
      (!q || textHit(d, q))
    );
  }

  function clearDrill() {
    state.drill = null;
    render();
  }

  function drillTo(opts) {
    state.drill = {
      customer: opts.customer || "",
      applicant: opts.applicant || "",
      keyword: opts.keyword || "",
      since: opts.since || "",
      until: opts.until || "",
      label: opts.label || "",
    };
    if (opts.topic) $("#topic").value = opts.topic;
    if (opts.clearDates) { $("#dateFrom").value = ""; $("#dateTo").value = ""; }
    if (opts.since && opts.until) {
      $("#dateFrom").value = opts.since;
      $("#dateTo").value = opts.until;
    }
    setTab(opts.tab || "tender");
    toast(opts.label || "Фильтр из аналитики");
  }

  function drillChip() {
    if (!state.drill || state.tab === "stats") return "";
    const parts = [
      state.drill.customer && `заказчик: ${state.drill.customer}`,
      state.drill.applicant && `заявитель: ${state.drill.applicant}`,
      state.drill.keyword && `слово: ${state.drill.keyword}`,
      state.drill.label,
    ].filter(Boolean);
    return `<div class="drill-chip">Фильтр аналитики: ${esc(parts[0] || "выборка")} <button type="button" id="clearDrill">✕ сбросить</button></div>`;
  }

  function sorted(list) {
    const s = $("#sort").value;
    const by = {
      date: (a, b) => (b.date || "").localeCompare(a.date || ""),
      dateAsc: (a, b) => (a.date || "9").localeCompare(b.date || "9"),
      price: (a, b) => (b.price || 0) - (a.price || 0),
      priceAsc: (a, b) => (a.price || Infinity) - (b.price || Infinity),
      starred: (a, b) => (stars[keyOf(b)]?.at || "").localeCompare(stars[keyOf(a)]?.at || ""),
    }[s];
    return by ? [...list].sort(by) : list;
  }

  // ---------- выпадающие списки с количеством ----------
  function fillSelect(sel, allLabel, entries) {
    const cur = sel.value;
    sel.innerHTML = `<option value="">${allLabel}</option>` + entries.map(([v, label, n]) => `<option value="${esc(v)}">${esc(label)} (${n})</option>`).join("");
    sel.value = entries.some(([v]) => v === cur) ? cur : "";
  }
  function counts(list, fn) {
    const m = new Map();
    list.forEach((d) => [].concat(fn(d)).forEach((v) => v && m.set(v, (m.get(v) || 0) + 1)));
    return m;
  }
  function updateSelects() {
    const tab = state.tab;
    const tc = counts(filtered(tab, "topic"), (d) => d.topics);
    fillSelect($("#topic"), "Все темы", D.topics.filter((t) => tc.get(t.id)).map((t) => [t.id, t.name, tc.get(t.id)]));
    const cc = counts(filtered(tab, "country"), (d) => d.country);
    const countries = [...cc].sort((a, b) => (b[0] === "Россия") - (a[0] === "Россия") || b[1] - a[1]);
    fillSelect($("#country"), "Все страны", countries.map(([c, n]) => [c, c, n]));
    const sc = counts(filtered(tab, "source"), (d) => d.source);
    fillSelect($("#source"), "Все источники", [...sc].map(([s, n]) => [s, s, n]));
  }

  // ---------- карточки ----------
  // цвет полоски: выбранная в фильтре тема, иначе первая тема в фиксированном порядке списка тем
  function cardColor(d) {
    const sel = $("#topic").value;
    const id = (sel && d.topics.includes(sel) ? sel : null)
      || D.topics.map((t) => t.id).find((id) => d.topics.includes(id))
      || d.topics[0];
    return topicInfo[id]?.color || "";
  }
  function topicPills(d) {
    return d.topics.slice(0, 3).map((t) => topicInfo[t] ? `<span class="pill topic" style="--tc:${topicInfo[t].color}">${esc(topicInfo[t].name)}</span>` : "").join("");
  }
  function origLine(d) {
    return d.title_ru && d.title_ru !== d.title ? `<div class="orig" title="${esc(d.title)}">Оригинал: ${esc(d.title)}</div>` : "";
  }
  function buttons(d) {
    const on = !!stars[keyOf(d)];
    return `<div class="btns">
      <button class="btn star ${on ? "on" : ""}" data-key="${esc(keyOf(d))}">${on ? "★ В избранном" : "☆ В избранное"}</button>
      <a class="btn primary" href="${esc(d.url)}" target="_blank" rel="noopener">Открыть ↗</a></div>`;
  }

  function tenderCard(d) {
    let status = `<span class="pill">${esc(d.status || "—")}</span>`;
    if (isOpen(d)) {
      const left = daysLeft(d);
      status = `<span class="pill ${left <= 5 ? "soon" : "open"}">Приём заявок · осталось ${left} дн.</span>`;
    }
    return `<article class="card ${stars[keyOf(d)] ? "starred" : ""}" style="--c:${cardColor(d)}">
      <div class="card-main">
        <div class="meta">${isNew(d) ? '<span class="pill new">Новое</span>' : ""}${status}<span>${esc(d.country)}</span>·<span>${esc(d.law || "")} ${esc(d.procedure || "")}</span></div>
        <h3><a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(d.title_ru || d.title)}</a></h3>
        ${origLine(d)}
        ${d.customer ? `<div class="who"><b>Заказчик:</b> ${esc(d.customer)}</div>` : ""}
        <div class="meta">${topicPills(d)}<span>№ ${esc(d.source_id)}</span>·<span>${esc(d.source)}</span>·<span>размещено ${fmtDate(d.date)}</span></div>
      </div>
      <div class="card-side">
        <div class="price">${fmtMoney(d.price, d.currency) || '<small>цена не указана</small>'}${d.price ? "<small>начальная / общая стоимость</small>" : ""}</div>
        ${d.deadline ? `<div class="deadline">Приём заявок до <b>${fmtDate(d.deadline)}</b></div>` : ""}
        ${buttons(d)}
      </div>
    </article>`;
  }

  function patentCard(d) {
    return `<article class="card ${stars[keyOf(d)] ? "starred" : ""}" style="--c:${cardColor(d)}">
      <div class="card-main">
        <div class="meta">${isNew(d) ? '<span class="pill new">Новое</span>' : ""}${d.status ? `<span class="pill ${/^действ/i.test(d.status) ? "open" : ""}">${esc(d.status)}</span>` : ""}<span class="pill">${esc(d.number || d.source_id)}</span>${d.kind && !/^европейск/i.test(d.kind) ? `<span>${esc(d.kind)}</span>·` : ""}<span>заявитель: ${esc(d.country)}</span>·<span>опубликован ${fmtDate(d.date)}</span></div>
        <h3><a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(d.title_ru || d.title)}</a></h3>
        ${origLine(d)}
        ${d.applicants?.length ? `<div class="who"><b>Заявитель:</b> ${esc(d.applicants.slice(0, 3).join("; "))}</div>` : ""}
        ${d.summary_ru ? `<div class="abstract">${esc(d.summary_ru)}</div>` : ""}
        <div class="meta">${topicPills(d)}${d.ipc?.length ? `<span>МПК: ${esc(d.ipc.slice(0, 3).join(", "))}</span>·` : ""}<span>${esc(d.source)}</span></div>
      </div>
      <div class="card-side">${buttons(d)}</div>
    </article>`;
  }

  const card = (d) => (d.type === "tender" ? tenderCard : patentCard)(d);

  function emptyState() {
    if (state.tab === "patent" && !byType("patent").length) {
      return `<div class="empty"><h3>Патентов пока нет</h3>Запустите <code>collect.py --only patents</code> — патенты берутся из открытой базы ФИПС (Роспатент), ключи не нужны.</div>`;
    }
    if (state.tab === "star") return `<div class="empty"><h3>Избранное пусто</h3>Нажмите «☆ В избранное» у тендера или патента — он появится здесь.</div>`;
    return `<div class="empty"><h3>Ничего не найдено</h3>Попробуйте увеличить период или сбросить фильтры.</div>`;
  }

  // ---------- аналитика ----------
  const TC = { tender: "#2563eb", patent: "#0f9960" };

  function bars(title, rows, opts = {}) {
    // rows: [[подпись, {tender: n, patent: n}] | [подпись, n]]
    // opts.click: (label) => ({ tab, customer, applicant, topic, keyword, label })
    const val = (r) => (typeof r[1] === "number" ? r[1] : (r[1].tender || 0) + (r[1].patent || 0));
    const max = Math.max(1, ...rows.map(val));
    const body = rows.length ? rows.map((r, idx) => {
      const segs = typeof r[1] === "number"
        ? `<i style="width:${(r[1] / max) * 100}%;background:${opts.color || TC.tender}"></i>`
        : ["tender", "patent"].map((t) => r[1][t] ? `<i style="width:${(r[1][t] / max) * 100}%;background:${TC[t]}" title="${t === "tender" ? "Тендеры" : "Патенты"}: ${r[1][t]}"></i>` : "").join("");
      const label = opts.fmt ? opts.fmt(val(r)) : val(r).toLocaleString("ru-RU");
      const clickable = !!opts.click;
      const attrs = clickable ? ` class="bar-row clickable" role="button" tabindex="0" data-bar="${idx}"` : ` class="bar-row"`;
      return `<div${attrs}><span class="bar-label" title="${esc(r[0])}">${esc(r[0])}</span><span class="bar-track">${segs}</span><b>${label}</b></div>`;
    }).join("") : `<div class="muted">Нет данных</div>`;
    const id = opts.id ? ` id="${esc(opts.id)}"` : "";
    return `<section class="panel ${opts.wide ? "wide" : ""}"${id} data-bar-kind="${esc(opts.kind || "")}"><h3>${title}</h3>${opts.note ? `<p class="muted">${opts.note}</p>` : ""}${body}</section>`;
  }

  function columns(title, buckets, types = ["tender", "patent"]) {
    const sum = (v) => types.reduce((s, t) => s + (v[t] || 0), 0);
    buckets = buckets.filter(([, v]) => sum(v));
    const max = Math.max(1, ...buckets.map(([, v]) => sum(v)));
    const cols = buckets.map(([k, v]) => {
      const h = (n) => ((n || 0) / max) * 100;
      const tip = types.map((t) => `${t === "tender" ? "тендеров" : "патентов"} ${v[t] || 0}`).join(", ");
      return `<div class="col" title="${k}: ${tip}">
        <b>${sum(v) || ""}</b>
        <div class="col-stack">${[...types].reverse().map((t) => `<i style="height:${h(v[t])}%;background:${TC[t]}"></i>`).join("")}</div>
        <span>${k}</span></div>`;
    }).join("");
    return `<section class="panel wide"><h3>${title}</h3><div class="cols">${cols || '<div class="muted">Нет данных</div>'}</div></section>`;
  }

  function top(list, fn, n = 10) {
    const m = new Map();
    list.forEach((d) => [].concat(fn(d)).forEach((v) => v && m.set(v, (m.get(v) || 0) + 1)));
    return [...m].sort((a, b) => b[1] - a[1]).slice(0, n);
  }

  const kpi = (n, label) => `<div class="kpi"><b>${typeof n === "number" ? n.toLocaleString("ru-RU") : n}</b><span>${label}</span></div>`;
  const byTopicCount = (list) => D.topics.map((t) => [t.name, list.filter((d) => d.topics.includes(t.id)).length])
    .filter(([, n]) => n).sort((a, b) => b[1] - a[1]);
  const daysAgo = (n) => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);

  // при выбранной теме показываем, с какими ещё темами пересекаются её документы
  function topicPanel(title, rows, opts = {}) {
    const sel = topicInfo[$("#topic").value];
    const shown = sel ? rows.filter(([name]) => name !== sel.name) : rows;
    if (opts.kind && opts.click && state._barClicks?.[opts.kind]) {
      // индексы строк после фильтрации должны совпадать с картой кликов
      state._barClicks[opts.kind] = shown.map(([name]) => {
        const tid = D.topics.find((t) => t.name === name)?.id || "";
        const tab = (opts.kind || "").includes("patent") ? "patent"
          : (opts.kind || "").includes("tender") ? "tender" : "tender";
        return { tab, topic: tid, label: name };
      });
    }
    if (!sel) return bars(title, shown, opts);
    return bars(`Пересечения темы «${sel.name}» с другими темами`, shown,
      { ...opts, note: "Нажмите тему — откроется список. Показано, с какими ещё темами пересекаются документы." });
  }

  // круговая диаграмма долей
  function donut(title, rows, opts = {}) {
    const total = Math.max(1, rows.reduce((s, [, n]) => s + n, 0));
    let acc = 0;
    const stops = rows.map(([, n], i) => {
      const a = acc;
      acc += (n / total) * 360;
      return `${COLORS[i % COLORS.length]} ${a}deg ${acc}deg`;
    }).join(", ");
    const legend = rows.map(([name, n], i) =>
      `<li><i style="background:${COLORS[i % COLORS.length]}"></i><span title="${esc(name)}">${esc(name)}</span><b>${n.toLocaleString("ru-RU")}</b><em>${Math.round(n / total * 100)}%</em></li>`).join("");
    return `<section class="panel ${opts.wide ? "wide" : ""}"><h3>${title}</h3>
      ${rows.length ? `<div class="donut-wrap"><div class="donut" style="background:conic-gradient(${stops})"></div><ul class="donut-legend">${legend}</ul></div>` : '<div class="muted">Нет данных</div>'}</section>`;
  }

  // кто сколько закупил (сумма НМЦК в рублях)
  function topSpend(list, n = 10) {
    const m = new Map();
    list.forEach((d) => {
      if (d.currency !== "RUB" || !d.price) return;
      const org = shortOrg(d.customer);
      if (!org) return;
      m.set(org, (m.get(org) || 0) + d.price);
    });
    return [...m].sort((a, b) => b[1] - a[1]).slice(0, n);
  }

  // «опа, активно закупают»: заказчик × тема за последние N дней
  function buyerSignals(tenders, days = 30, minN = 2) {
    const since = daysAgo(days);
    const recent = tenders.filter((d) => docDate(d) >= since);
    const m = new Map();
    recent.forEach((d) => {
      const org = shortOrg(d.customer);
      if (!org) return;
      (d.topics.length ? d.topics : [""]).forEach((tid) => {
        const key = org + "|" + tid;
        const v = m.get(key) || { org, tid, n: 0, sum: 0 };
        v.n++;
        if (d.currency === "RUB" && d.price) v.sum += d.price;
        m.set(key, v);
      });
    });
    return [...m.values()]
      .filter((v) => v.n >= minN)
      .sort((a, b) => b.n - a.n || b.sum - a.sum)
      .slice(0, 8);
  }

  function applicantSignals(patents, days = 90, minN = 2) {
    const since = daysAgo(days);
    const recent = patents.filter((d) => docDate(d) >= since);
    const m = new Map();
    recent.forEach((d) => {
      const org = shortOrg((d.applicants || [])[0]);
      if (!org) return;
      const tid = d.topics[0] || "";
      const key = org + "|" + tid;
      const v = m.get(key) || { org, tid, n: 0 };
      v.n++;
      m.set(key, v);
    });
    return [...m.values()].filter((v) => v.n >= minN).sort((a, b) => b.n - a.n).slice(0, 8);
  }

  function signalsPanel(title, note, items, kind) {
    if (!items.length) {
      return `<section class="panel wide"><h3>${title}</h3><p class="muted">${note} Пока нет явных всплесков — попробуйте сменить период или тему.</p></section>`;
    }
    const since = kind === "tender" ? daysAgo(30) : daysAgo(90);
    const rows = items.map((v) => {
      const topic = topicInfo[v.tid]?.name || "без темы";
      const color = topicInfo[v.tid]?.color || "#64748b";
      const money = v.sum ? ` · ${fmtMoney(v.sum, "RUB")}` : "";
      const what = kind === "tender"
        ? `<b>${esc(v.org)}</b> — ${v.n} закупок по теме «${esc(topic)}»${money}`
        : `<b>${esc(v.org)}</b> — ${v.n} патентов/заявок по теме «${esc(topic)}»`;
      return `<div class="signal clickable" style="--sc:${color}" role="button" tabindex="0"
        data-drill-tab="${kind}" data-drill-org="${esc(v.org)}" data-drill-topic="${esc(v.tid || "")}"
        data-drill-since="${since}" data-drill-label="${esc(v.org)} · ${esc(topic)}">
        <div>${what}<div class="signal-hint">нажмите, чтобы открыть список</div></div></div>`;
    }).join("");
    return `<section class="panel wide signals"><h3>${title}</h3><p class="muted">${note}</p>${rows}</section>`;
  }

  // рост темы: отдельно тендеры и патенты, 30 vs предыдущие 30
  function topicGrowthSplit(T, P) {
    const a0 = daysAgo(30), a1 = daysAgo(60);
    const count = (list, tid, from, to) => list.filter((d) => d.topics.includes(tid) && docDate(d) >= from && (!to || docDate(d) < to)).length;
    return D.topics.map((t) => {
      const tPrev = count(T, t.id, a1, a0), tNow = count(T, t.id, a0, "");
      const pPrev = count(P, t.id, a1, a0), pNow = count(P, t.id, a0, "");
      return {
        id: t.id, name: t.name, color: topicInfo[t.id].color,
        tPrev, tNow, pPrev, pNow,
        delta: (tNow + pNow) - (tPrev + pPrev),
      };
    }).filter((x) => x.tPrev + x.tNow + x.pPrev + x.pNow > 0)
      .sort((a, b) => b.delta - a.delta || (b.tNow + b.pNow) - (a.tNow + a.pNow));
  }

  function growthPanel(T, P) {
    const rows = topicGrowthSplit(T, P);
    if (!rows.length) return "";
    const body = rows.map((r) => {
      const cls = r.delta > 0 ? "up" : r.delta < 0 ? "down" : "";
      const sign = r.delta > 0 ? `+${r.delta}` : String(r.delta);
      return `<div class="grow-row clickable" role="button" tabindex="0" data-drill-topic="${esc(r.id)}"
        data-drill-label="${esc(r.name)}">
        <span class="grow-name" style="--tc:${r.color}">${esc(r.name)}</span>
        <span class="grow-detail">
          <span>тендеры: было ${r.tPrev} → стало ${r.tNow}</span>
          <span>патенты: было ${r.pPrev} → стало ${r.pNow}</span>
        </span>
        <b class="${cls}">${sign}</b></div>`;
    }).join("");
    return `<section class="panel wide"><h3>Динамика изменения количества патентов и тендеров по темам</h3>
      <p class="muted">Последние 30 дней против предыдущих 30. Нажмите тему — откроется список.</p>${body}</section>`;
  }

  function renderAnalytics() {
    const view = state.an;
    const list = filtered("stats");
    const T = list.filter((d) => d.type === "tender"), P = list.filter((d) => d.type === "patent");
    const byTopic = D.topics.map((t) => [t.name, {
      tender: T.filter((d) => d.topics.includes(t.id)).length,
      patent: P.filter((d) => d.topics.includes(t.id)).length,
    }]).filter(([, v]) => v.tender + v.patent).sort((a, b) => (b[1].tender + b[1].patent) - (a[1].tender + a[1].patent));

    const [from, to] = periodRange("stats");
    const monthly = !!from && (new Date(to || today) - new Date(from)) / 864e5 <= 731;
    const keyOfDate = (d) => (monthly ? docDate(d).slice(0, 7) : docDate(d).slice(0, 4));
    const m = new Map();
    list.forEach((d) => {
      const k = keyOfDate(d);
      if (!/^\d{4}/.test(k)) return;
      const v = m.get(k) || { tender: 0, patent: 0 };
      v[d.type]++;
      m.set(k, v);
    });
    const MONTHS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
    const buckets = [...m].sort((a, b) => a[0].localeCompare(b[0]))
      .map(([k, v]) => [monthly ? `${MONTHS[+k.slice(5) - 1]} ${k.slice(2, 4)}` : k, v]);

    const rub = T.filter((d) => d.currency === "RUB" && d.price);
    const selTopic = $("#topic").value;
    const moneyTopic = selTopic && topicInfo[selTopic]
      ? [[topicInfo[selTopic].name, rub.filter((d) => d.topics.includes(selTopic)).reduce((s, d) => s + d.price, 0)]].filter(([, v]) => v)
      : [];
    const totalRub = rub.reduce((s, d) => s + d.price, 0);
    const openN = T.filter(isOpen).length;
    const dyn = monthly ? "Динамика по месяцам" : "Динамика по годам";
    const switcher = `<div class="an-switch">${[["all", "Общая"], ["tender", `Тендеры (${T.length})`], ["patent", `Патенты (${P.length})`]]
      .map(([v, l]) => `<button data-an="${v}" class="${view === v ? "active" : ""}">${l}</button>`).join("")}</div>`;

    // сохраняем данные для кликов по строкам (индексы → параметры drill)
    state._barClicks = {};

    const clickCustomers = (rows) => {
      state._barClicks.customers = rows.map(([org]) => ({ tab: "tender", customer: org, label: org }));
      return true;
    };
    const clickApplicants = (rows) => {
      state._barClicks.applicants = rows.map(([org]) => ({ tab: "patent", applicant: org, label: org }));
      return true;
    };
    const clickSpend = (rows) => {
      state._barClicks.spend = rows.map(([org]) => ({ tab: "tender", customer: org, label: org }));
      return true;
    };
    const clickKeywords = (rows, tab) => {
      state._barClicks["kw-" + tab] = rows.map(([kw]) => ({ tab, keyword: kw, label: kw }));
      return true;
    };
    const clickTopics = (rows, tab) => {
      // rows may be [name, n] or [name, {tender,patent}]
      state._barClicks["topics-" + tab] = rows.map(([name]) => {
        const tid = D.topics.find((t) => t.name === name)?.id || "";
        return { tab: tab === "all" ? "tender" : tab, topic: tid, label: name };
      });
      return true;
    };

    let html;
    if (view === "tender") {
      const biggest = [...rub].sort((a, b) => b.price - a.price).slice(0, 8);
      const spend = topSpend(selTopic ? rub.filter((d) => d.topics.includes(selTopic)) : rub);
      const cust = top(T, (d) => shortOrg(d.customer));
      const kws = top(T, (d) => d.keywords, 12);
      const tTopics = byTopicCount(T);
      clickSpend(spend); clickCustomers(cust); clickKeywords(kws, "tender"); clickTopics(tTopics, "tender");
      html = `
        <div class="kpis">${kpi(T.length, "тендеров")}${kpi(openN, "с открытым приёмом")}${kpi(fmtMoney(totalRub, "RUB") || "—", "сумма закупок в РФ")}${kpi(spend[0] ? spend[0][0].slice(0, 28) : "—", "топ-заказчик по сумме")}</div>
        ${signalsPanel("На что обратить внимание · последние 30 дней",
          "Заказчики с несколькими закупками по одной теме за месяц. Нажмите строку — откроются их тендеры.",
          buyerSignals(T, 30, 2), "tender")}
        <div class="panels">
          ${columns(dyn, buckets, ["tender"])}
          ${topicPanel("Тендеры по темам", tTopics, { kind: "topics-tender", click: true })}
          ${growthPanel(T, P)}
          ${bars("Кто сколько закупил (₽)", spend, { fmt: (v) => fmtMoney(v, "RUB"), note: "Нажмите заказчика — откроются его закупки. Суммы НМЦК ЕИС в ₽", wide: true, kind: "spend", click: true })}
          ${bars("Самые активные заказчики (по числу закупок)", cust, { note: "Нажмите — список тендеров заказчика", kind: "customers", click: true })}
          ${moneyTopic.length ? bars(`Сумма по выбранной теме`, moneyTopic, { fmt: (v) => fmtMoney(v, "RUB") }) : ""}
          <section class="panel wide"><h3>Крупнейшие закупки</h3>${biggest.length ? biggest.map((d) =>
            `<div class="bar-row clickable" role="button" data-drill-tab="tender" data-drill-org="${esc(shortOrg(d.customer))}" data-drill-label="${esc(shortOrg(d.customer))}">
              <span class="bar-label wide-label"><a href="${esc(d.url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()" title="${esc(d.title_ru || d.title)}">${esc(shortOrg(d.customer) || "—")}: ${esc(d.title_ru || d.title)}</a></span><b>${fmtMoney(d.price, d.currency)}</b></div>`).join("") : '<div class="muted">Нет данных</div>'}</section>
          ${bars("Частые ключевые слова в тендерах", kws, { color: "#7c3aed", note: "Нажмите слово — откроются тендеры", kind: "kw-tender", click: true })}
        </div>`;
    } else if (view === "patent") {
      const apps = top(P, (d) => shortOrg((d.applicants || [])[0]));
      const kws = top(P, (d) => d.keywords, 12);
      const pTopics = byTopicCount(P);
      clickApplicants(apps); clickKeywords(kws, "patent"); clickTopics(pTopics, "patent");
      html = `
        <div class="kpis">${kpi(P.length, "патентов и заявок")}${kpi(P.filter((d) => /^действ/i.test(d.status || "")).length, "действуют (ФИПС)")}${kpi(P.filter((d) => d.source.startsWith("ФИПС")).length, "российских")}${kpi(P.filter((d) => d.source.startsWith("EPO")).length, "европейских")}</div>
        ${signalsPanel("На что обратить внимание · последние 90 дней",
          "Заявители с несколькими публикациями по одной теме за квартал. Нажмите — откроются их патенты.",
          applicantSignals(P, 90, 2), "patent")}
        <div class="panels">
          ${columns(dyn, buckets, ["patent"])}
          ${topicPanel("Патенты по темам", pTopics, { color: TC.patent, kind: "topics-patent", click: true })}
          ${growthPanel(T, P)}
          ${bars("Статус охраны", top(P.filter((d) => d.status), (d) => d.status[0].toUpperCase() + d.status.slice(1), 8), { color: TC.patent, note: "По данным реестра ФИПС" })}
          ${bars("Самые активные патентообладатели", apps, { color: TC.patent, wide: true, note: "Нажмите — список патентов заявителя", kind: "applicants", click: true })}
          ${bars("Частые ключевые слова в патентах", kws, { color: "#7c3aed", note: "Нажмите слово — откроются патенты", kind: "kw-patent", click: true })}
        </div>`;
    } else {
      const cust = top(T, (d) => shortOrg(d.customer));
      const apps = top(P, (d) => shortOrg((d.applicants || [])[0]));
      const spend = topSpend(rub);
      const kws = top(list, (d) => d.keywords, 12);
      clickCustomers(cust); clickApplicants(apps); clickSpend(spend); clickKeywords(kws, "tender"); clickTopics(byTopic, "all");
      html = `
        <div class="kpis">${kpi(T.length, "тендеров")}${kpi(P.length, "патентов")}${kpi(openN, "тендеров с открытым приёмом")}${kpi(fmtMoney(totalRub, "RUB") || "—", "сумма закупок в РФ")}</div>
        ${signalsPanel("Сигналы за последний месяц",
          "Кто активно закупает какую технологию. Нажмите строку — откроются тендеры этого заказчика по теме.",
          buyerSignals(T, 30, 2), "tender")}
        <div class="legend"><span><i style="background:${TC.tender}"></i>Тендеры</span><span><i style="background:${TC.patent}"></i>Патенты</span></div>
        <div class="panels">
          ${columns(dyn, buckets)}
          ${topicPanel("Распределение патентов и тендеров по темам", byTopic, { wide: true, kind: "topics-all", click: true })}
          ${growthPanel(T, P)}
          ${bars("Самые активные заказчики", cust, { note: "Нажмите — тендеры заказчика", kind: "customers", click: true })}
          ${bars("Самые активные патентообладатели", apps, { color: TC.patent, note: "Нажмите — патенты заявителя", kind: "applicants", click: true })}
          ${bars("Кто сколько закупил (₽)", spend, { fmt: (v) => fmtMoney(v, "RUB"), note: "Нажмите заказчика — его закупки. НМЦК ЕИС в ₽", wide: true, kind: "spend", click: true })}
          ${bars("Частые ключевые слова", kws, { color: "#7c3aed", wide: true, note: "Нажмите слово — поиск по нему", kind: "kw-tender", click: true })}
        </div>`;
    }
    $("#analytics").innerHTML = switcher + html;
  }

  // ---------- отрисовка ----------
  function render() {
    const tab = state.tab;
    const isStats = tab === "stats";
    $("#sortWrap").hidden = isStats;
    $("#list").hidden = isStats;
    $("#analytics").hidden = !isStats;
    updateSelects();
    document.querySelectorAll("#tabs button .cnt").forEach((c) => (c.textContent = filtered(c.parentElement.dataset.tab).length));
    if (isStats) {
      $("#summary").textContent = "";
      $("#more").hidden = true;
      renderAnalytics();
      return;
    }
    const list = sorted(filtered(tab));
    $("#summary").innerHTML = (list.length ? `Найдено: ${list.length}` : "") + drillChip();
    const chipBtn = $("#clearDrill");
    if (chipBtn) chipBtn.onclick = clearDrill;
    $("#list").innerHTML = list.length ? list.slice(0, state.shown).map(card).join("") : emptyState();
    $("#more").hidden = list.length <= state.shown;
  }

  function setTab(tab) {
    state.tab = tab;
    document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
    $("#sort").innerHTML = (SORTS[tab] || SORTS.tender).map(([v, l]) => `<option value="${v}">${l}</option>`).join("");
    state.shown = PAGE;
    render();
  }

  // ---------- выгрузка CSV (то, что сейчас отфильтровано) ----------
  function exportCsv() {
    const tab = state.tab;
    const list = tab === "stats" ? filtered("stats") : sorted(filtered(tab));
    const cols = [
      ["Тип", (d) => (d.type === "tender" ? "Тендер" : "Патент")],
      ["Темы", (d) => d.topics.map((t) => topicInfo[t]?.name || t).join(", ")],
      ["Название", (d) => d.title_ru || d.title],
      ["Название (оригинал)", (d) => d.title],
      ["Страна", (d) => d.country],
      ["Источник", (d) => d.source],
      ["Номер", (d) => d.number || d.source_id],
      ["Дата публикации", (d) => d.date || ""],
      ["Заказчик / заявитель", (d) => d.customer || (d.applicants || []).join("; ")],
      ["Цена", (d) => (d.price ? String(Math.round(d.price)) : "")],
      ["Валюта", (d) => (d.price ? d.currency || "" : "")],
      ["Окончание приёма заявок", (d) => d.deadline || ""],
      ["Статус", (d) => d.status || ""],
      ["МПК", (d) => (d.ipc || []).join(", ")],
      ["Ключевые слова", (d) => (d.keywords || []).join(", ")],
      ["Описание", (d) => d.summary_ru || d.summary || ""],
      ["Ссылка", (d) => d.url],
    ];
    const cell = (v) => `"${String(v ?? "").replace(/"/g, '""').replace(/\s+/g, " ").trim()}"`;
    const lines = [cols.map(([h]) => cell(h)).join(";"), ...list.map((d) => cols.map(([, f]) => cell(f(d))).join(";"))];
    const blob = new Blob(["\ufeff" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
    const name = { tender: "тендеры", patent: "патенты", star: "избранное", stats: "все" }[tab] || "выгрузка";
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: `${name}_${today}.csv` });
    document.body.appendChild(a);
    a.click();
    a.remove();
    toast(`Выгружено записей: ${list.length}`);
  }
  $("#csv").onclick = exportCsv;

  // ---------- события ----------
  // поиск — с паузой 280 мс, чтобы набор букв не блокировался пересчётом тысяч карточек
  let renderTimer = 0;
  function requestRender(delay = 0) {
    state.shown = PAGE;
    clearTimeout(renderTimer);
    if (delay <= 0) { render(); return; }
    renderTimer = setTimeout(render, delay);
  }
  $("#q").addEventListener("input", () => requestRender(280));
  ["#topic", "#country", "#source", "#dateFrom", "#dateTo", "#sort"].forEach((s) =>
    $(s).addEventListener("input", () => requestRender(0)));
  document.querySelectorAll("#tabs button").forEach((b) => b.addEventListener("click", () => setTab(b.dataset.tab)));
  $("#more").onclick = () => { state.shown += PAGE; render(); };
  $("#reset").onclick = () => {
    ["#q", "#topic", "#country", "#source"].forEach((s) => ($(s).value = ""));
    $("#dateFrom").value = $("#dateTo").value = "";
    state.drill = null;
    requestRender(0);
  };
  $("#stats").addEventListener("click", (e) => {
    const go = e.target.closest("[data-go]")?.dataset.go;
    if (!go) return;
    setTab(go);
  });
  $("#list").addEventListener("click", (e) => {
    const btn = e.target.closest(".star");
    if (!btn) return;
    const key = btn.dataset.key;
    const on = !stars[key];
    setStar(key, on);
    toast(on ? "Добавлено в избранное" : "Убрано из избранного");
    render();
  });

  $("#analytics").addEventListener("click", (e) => {
    const an = e.target.closest("[data-an]")?.dataset.an;
    if (an) { state.an = an; renderAnalytics(); return; }

    const signal = e.target.closest(".signal[data-drill-tab]");
    if (signal) {
      const tab = signal.dataset.drillTab;
      const org = signal.dataset.drillOrg || "";
      drillTo({
        tab,
        customer: tab === "tender" ? org : "",
        applicant: tab === "patent" ? org : "",
        topic: signal.dataset.drillTopic || "",
        since: signal.dataset.drillSince || "",
        until: today,
        label: signal.dataset.drillLabel || org,
        clearDates: !signal.dataset.drillSince,
      });
      return;
    }

    const grow = e.target.closest(".grow-row[data-drill-topic]");
    if (grow && grow.dataset.drillTopic) {
      $("#topic").value = grow.dataset.drillTopic;
      state.drill = { label: grow.dataset.drillLabel || "" };
      setTab("tender");
      toast(grow.dataset.drillLabel || "Тема");
      return;
    }

    const big = e.target.closest(".bar-row[data-drill-org]");
    if (big && big.dataset.drillOrg) {
      drillTo({ tab: "tender", customer: big.dataset.drillOrg, label: big.dataset.drillLabel || big.dataset.drillOrg });
      return;
    }

    const row = e.target.closest(".bar-row.clickable");
    const panel = row?.closest("[data-bar-kind]");
    if (row && panel) {
      const kind = panel.dataset.barKind;
      const idx = +row.dataset.bar;
      const cfg = state._barClicks?.[kind]?.[idx];
      if (cfg) {
        if (cfg.topic) $("#topic").value = cfg.topic;
        drillTo(cfg);
      }
    }
  });


  setTab(SORTS[location.hash.slice(1)] ? location.hash.slice(1) : "stats");

  if (favs) {
    favs.onSnapshot((snap) => {
      stars = {};
      snap.forEach((s) => { const v = s.data(); if (v?.key) stars[v.key] = v; });
      localStorage.setItem(STAR_KEY, JSON.stringify(stars));
      render();
    }, (e) => toast(`Облачное избранное недоступно: ${e.code || e.message}`));
  }
})();
