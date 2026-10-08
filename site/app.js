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

  const state = { tab: "stats", an: "all", shown: PAGE };
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

  function filtered(tab, skip = "") {
    const q = $("#q").value.trim().toLowerCase();
    const [since, until] = periodRange(tab);
    const topic = skip === "topic" ? "" : $("#topic").value;
    const country = skip === "country" ? "" : $("#country").value;
    const source = skip === "source" ? "" : $("#source").value;
    const onlyOpen = $("#onlyOpen").checked && tab === "tender";
    const onlyNew = $("#onlyNew").checked;
    return base(tab).filter((d) =>
      (!since || docDate(d) >= since) && (!until || docDate(d) <= until) &&
      (!topic || d.topics.includes(topic)) &&
      (!country || d.country === country) &&
      (!source || d.source === source) &&
      (!onlyOpen || isOpen(d)) &&
      (!onlyNew || isNew(d)) &&
      (!q || [d.title, d.title_ru, d.customer, d.number, d.source_id, (d.applicants || []).join(" "), d.summary_ru, (d.ipc || []).join(" ")]
        .join(" ").toLowerCase().includes(q))
    );
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
    return `<article class="card ${stars[keyOf(d)] ? "starred" : ""}" style="--c:${topicInfo[d.topics[0]]?.color}">
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
    return `<article class="card ${stars[keyOf(d)] ? "starred" : ""}" style="--c:${topicInfo[d.topics[0]]?.color}">
      <div class="card-main">
        <div class="meta">${isNew(d) ? '<span class="pill new">Новое</span>' : ""}${d.status ? `<span class="pill ${/^действ/i.test(d.status) ? "open" : ""}">${esc(d.status)}</span>` : ""}<span class="pill">${esc(d.number || d.source_id)}</span>${d.kind ? `<span>${esc(d.kind)}</span>·` : ""}<span>заявитель: ${esc(d.country)}</span>·<span>опубликован ${fmtDate(d.date)}</span></div>
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
    const val = (r) => (typeof r[1] === "number" ? r[1] : (r[1].tender || 0) + (r[1].patent || 0));
    const max = Math.max(1, ...rows.map(val));
    const body = rows.length ? rows.map((r) => {
      const segs = typeof r[1] === "number"
        ? `<i style="width:${(r[1] / max) * 100}%;background:${opts.color || TC.tender}"></i>`
        : ["tender", "patent"].map((t) => r[1][t] ? `<i style="width:${(r[1][t] / max) * 100}%;background:${TC[t]}" title="${t === "tender" ? "Тендеры" : "Патенты"}: ${r[1][t]}"></i>` : "").join("");
      const label = opts.fmt ? opts.fmt(val(r)) : val(r).toLocaleString("ru-RU");
      return `<div class="bar-row"><span class="bar-label" title="${esc(r[0])}">${esc(r[0])}</span><span class="bar-track">${segs}</span><b>${label}</b></div>`;
    }).join("") : `<div class="muted">Нет данных</div>`;
    return `<section class="panel ${opts.wide ? "wide" : ""}"><h3>${title}</h3>${opts.note ? `<p class="muted">${opts.note}</p>` : ""}${body}</section>`;
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

  function top(list, fn, n = 10) {
    const m = new Map();
    list.forEach((d) => [].concat(fn(d)).forEach((v) => v && m.set(v, (m.get(v) || 0) + 1)));
    return [...m].sort((a, b) => b[1] - a[1]).slice(0, n);
  }

  const kpi = (n, label) => `<div class="kpi"><b>${typeof n === "number" ? n.toLocaleString("ru-RU") : n}</b><span>${label}</span></div>`;
  const byTopicCount = (list) => D.topics.map((t) => [t.name, list.filter((d) => d.topics.includes(t.id)).length])
    .filter(([, n]) => n).sort((a, b) => b[1] - a[1]);
  const ipcClass = (code) => (code || "").replace(/\s.*$/, "").slice(0, 4);

  // при выбранной теме показываем, с какими ещё темами пересекаются её документы
  function topicPanel(title, rows, opts = {}) {
    const sel = topicInfo[$("#topic").value];
    if (!sel) return bars(title, rows, opts);
    return bars(`Пересечения темы «${sel.name}» с другими темами`, rows.filter(([name]) => name !== sel.name),
      { ...opts, note: "Сколько документов выбранной темы одновременно относятся и к другой теме (например, радиосвязь для БПЛА — это и радиосвязь, и робототехника)" });
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
    const money = D.topics.map((t) => [t.name, rub.filter((d) => d.topics.includes(t.id)).reduce((s, d) => s + d.price, 0)])
      .filter(([, v]) => v).sort((a, b) => b[1] - a[1]);
    const totalRub = rub.reduce((s, d) => s + d.price, 0);
    const dyn = monthly ? "Динамика по месяцам" : "Динамика по годам";
    const active = P.filter((d) => /^действ/i.test(d.status || "")).length;

    const switcher = `<div class="an-switch">${[["all", "Общая"], ["tender", `Тендеры (${T.length})`], ["patent", `Патенты (${P.length})`]]
      .map(([v, l]) => `<button data-an="${v}" class="${view === v ? "active" : ""}">${l}</button>`).join("")}</div>`;

    let html;
    if (view === "tender") {
      const open = T.filter(isOpen);
      const biggest = [...rub].sort((a, b) => b.price - a.price).slice(0, 8);
      html = `
        <div class="kpis">${kpi(T.length, "тендеров")}</div>
        <div class="panels">
          ${columns(dyn, buckets, ["tender"])}
          ${topicPanel("Тендеры по темам", byTopicCount(T))}
          ${bars("Открытый приём заявок по темам", byTopicCount(open), { color: "#0f9960" })}
          ${bars("Самые активные заказчики", top(T, (d) => shortOrg(d.customer)))}
          ${bars("Сумма закупок в РФ по темам", money, { fmt: (v) => fmtMoney(v, "RUB"), note: "Начальные цены тендеров ЕИС в рублях" })}
          <section class="panel wide"><h3>Крупнейшие закупки</h3>${biggest.length ? biggest.map((d) =>
            `<div class="bar-row"><span class="bar-label wide-label"><a href="${esc(d.url)}" target="_blank" rel="noopener" title="${esc(d.title_ru || d.title)}">${esc(d.title_ru || d.title)}</a></span><b>${fmtMoney(d.price, d.currency)}</b></div>`).join("") : '<div class="muted">Нет данных</div>'}</section>
          ${bars("Частые ключевые слова в тендерах", top(T, (d) => d.keywords, 12), { color: "#7c3aed" })}
        </div>`;
    } else if (view === "patent") {
      html = `
        <div class="kpis">${kpi(P.length, "патентов")}</div>
        <div class="panels">
          ${columns(dyn, buckets, ["patent"])}
          ${topicPanel("Патенты по темам", byTopicCount(P), { color: TC.patent })}
          ${bars("Статус", top(P, (d) => { const s = d.status || d.kind || "не указан"; return s[0].toUpperCase() + s.slice(1); }, 8), { color: TC.patent })}
          ${bars("Самые активные патентообладатели", top(P, (d) => shortOrg((d.applicants || [])[0])), { color: TC.patent })}
          ${bars("Частые классы МПК", top(P, (d) => [...new Set((d.ipc || []).map(ipcClass))], 10), { color: "#0e7490", note: "Подкласс Международной патентной классификации, например G06F — обработка данных" })}
          ${bars("Частые ключевые слова в патентах", top(P, (d) => d.keywords, 12), { color: "#7c3aed" })}
        </div>`;
    } else {
      html = `
        <div class="kpis">${kpi(T.length, "тендеров")}${kpi(P.length, "патентов")}</div>
        <div class="legend"><span><i style="background:${TC.tender}"></i>Тендеры</span><span><i style="background:${TC.patent}"></i>Патенты</span></div>
        <div class="panels">
          ${columns(dyn, buckets)}
          ${topicPanel("По темам", byTopic, { wide: true })}
          ${bars("Самые активные заказчики", top(T, (d) => shortOrg(d.customer)))}
          ${bars("Самые активные патентообладатели", top(P, (d) => shortOrg((d.applicants || [])[0])), { color: TC.patent })}
          ${bars("Частые ключевые слова", top(list, (d) => d.keywords, 12), { color: "#7c3aed", wide: true })}
        </div>`;
    }
    $("#analytics").innerHTML = switcher + html;
  }

  // ---------- отрисовка ----------
  function render() {
    const tab = state.tab;
    const isStats = tab === "stats";
    $("#openWrap").hidden = tab !== "tender";
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
    $("#summary").textContent = list.length ? `Найдено: ${list.length}` : "";
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
  ["#q", "#topic", "#country", "#source", "#dateFrom", "#dateTo", "#sort", "#onlyOpen", "#onlyNew"].forEach((s) =>
    $(s).addEventListener("input", () => { state.shown = PAGE; render(); }));
  document.querySelectorAll("#tabs button").forEach((b) => b.addEventListener("click", () => setTab(b.dataset.tab)));
  $("#more").onclick = () => { state.shown += PAGE; render(); };
  $("#reset").onclick = () => {
    ["#q", "#topic", "#country", "#source"].forEach((s) => ($(s).value = ""));
    $("#dateFrom").value = $("#dateTo").value = "";
    $("#onlyOpen").checked = $("#onlyNew").checked = false;
    render();
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
    if (!an) return;
    state.an = an;
    renderAnalytics();
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
