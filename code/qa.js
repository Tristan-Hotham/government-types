// QA: open index.html at desktop (1280 px) and phone (390 px) widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8797; set PORT to change).
// Leaflet is served from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked.
const { chromium } = require("playwright");
const LEAF = process.env.LEAFLET_DIST || "/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/node_modules/leaflet/dist";
(async () => {
  const b = await chromium.launch();
  const errs = [], over = {};
  for (const [nm, vw, vh] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet.min.js/, r => r.fulfill({ path: LEAF + "/leaflet.js" }));
    await p.route(/leaflet.min.css/, r => r.fulfill({ path: LEAF + "/leaflet.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8797) + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(2000);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(600); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    await shot("#atlas", "map_family");
    for (const m of ["head_of_state", "executive", "electoral_system", "territory", "chambers", "vdem_regime_label", "libdem"]) { await p.click(`#modeRow [data-m="${m}"]`); await p.waitForTimeout(500); await shot("#atlas", "map_" + m); }
    await p.click('#modeRow [data-m="family"]');
    await p.fill("#q", "Switzerland"); await p.waitForTimeout(300); await p.keyboard.press("Enter"); await p.waitForTimeout(1500); await shot("#atlas", "search_switzerland");
    await p.fill("#q", "Germany"); await p.waitForTimeout(300); await p.keyboard.press("Enter"); await p.waitForTimeout(1200);
    await p.click("#likeBtn"); await p.waitForTimeout(800); await shot("#atlas", "like_germany");
    await p.click("#likeBtn"); await p.click('#focusRow .btn:nth-child(2)'); await p.waitForTimeout(800);
    await p.fill("#q", "Lebanon"); await p.waitForTimeout(300); await p.keyboard.press("Enter"); await p.waitForTimeout(1200); await shot("#side", "card_lebanon");
    await p.fill("#q", "United Kingdom"); await p.waitForTimeout(300); await p.keyboard.press("Enter"); await p.waitForTimeout(1200); await shot("#side", "card_uk");
    await p.click(".back"); await p.locator("#map").scrollIntoViewIfNeeded(); await p.click(".lyrBtn"); await p.waitForTimeout(300); await shot("#map", "layers_panel"); await p.click(".lyrBtn");
    await p.click('#focusRow .btn:nth-child(8)'); await p.waitForTimeout(900); await shot("#atlas", "pacific_dots");
    await p.click('#legend .item[data-v="SR"]'); await p.waitForTimeout(600); await shot("#atlas", "legend_filter_SR"); await p.click('#legend .item[data-v="SR"]');
    for (const c of ["famChart", "sigTable", "uniqList", "xChart", "ldiChart", "hardTable", "checkTable"]) await shot("#" + c, c);
    await p.click('#famRow [data-k="pop"]'); await p.waitForTimeout(300); await shot("#famChart", "famChart_pop");
    await p.click('#xRow [data-k="pop"]'); await p.waitForTimeout(300); await shot("#xChart", "xChart_pop");
    await p.click('#sigTable tr[data-q]:nth-child(2)'); await p.waitForTimeout(1200); await shot("#atlas", "sig_click");
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(800); await shot("#atlas", "dark_map"); await p.click("#theme");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1200); await p.screenshot({ path: `qa/${nm}_fullscreen.png` }); await p.click(".mfs-btn");
    }
    over[nm] = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", over[nm]);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
  if (errs.length || Object.values(over).some(v => v > 0)) process.exit(1);
})();
