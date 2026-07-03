// The "Android Device" hero banner: a full-width gapit-htmlgraphics panel that
// renders the child's day-on-screen at a glance. $family/$child come from the
// dashboard vars; screen-time / idle-vs-active / active-device come from the
// panel's own queries (refIds A/B/C). Degrades to a static hero when there's no
// data, and flips its accent cool (idle) -> warm (on screen) from the last-
// activity gap.
local panel = import 'custom/panel.libsonnet';

function(cfg)
  local sig = cfg.signals.family_link;

  local css = |||
    #hero {
      --warm: #ffb454; --cool: #7aa2ff; --accent: var(--cool);
      --text: #f5f3ff; --muted: #9d9ac0; --faint: #6d6a8c;
      --ground: #0f0e17; --ground2: #17161f; --line: rgba(255,255,255,.07);
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      color: var(--text); box-sizing: border-box;
      height: 100%; width: 100%; overflow: hidden; position: relative;
      display: flex; align-items: center;
      padding: clamp(18px,3vw,34px) clamp(22px,4vw,48px);
      border-radius: 14px;
      background:
        radial-gradient(120% 150% at 8% -20%, color-mix(in oklab, var(--accent) 22%, transparent), transparent 60%),
        linear-gradient(180deg, var(--ground2), var(--ground));
    }
    #hero.active { --accent: var(--warm); }
    #hero * { box-sizing: border-box; }
    #hero .glow {
      position: absolute; top: -50%; left: -6%; width: 46%; height: 200%;
      background: radial-gradient(closest-side, color-mix(in oklab, var(--accent) 40%, transparent), transparent 72%);
      filter: blur(46px); opacity: .5; pointer-events: none;
    }
    #hero .grid {
      position: relative; width: 100%; display: grid;
      grid-template-columns: minmax(0,1fr) auto; align-items: center;
      gap: clamp(20px,4vw,52px);
    }
    #hero .eyebrow { display: inline-flex; align-items: center; gap: 8px;
      font-size: 12.5px; letter-spacing: .08em; text-transform: uppercase;
      color: var(--muted); font-weight: 600; }
    #hero .eyebrow b { color: var(--text); text-transform: none; letter-spacing: 0; }
    #hero .eyebrow .d { color: var(--faint); }
    #hero h1 { margin: 12px 0 0; font-weight: 700; line-height: 1.02;
      letter-spacing: -.02em; font-size: clamp(26px,4.4vw,50px); }
    #hero h1 .rest { color: var(--muted); font-weight: 600; }
    #hero .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
    #hero .chip { display: inline-flex; align-items: center; gap: 7px;
      padding: 6px 12px; border: 1px solid var(--line); border-radius: 999px;
      background: rgba(255,255,255,.03); font-size: 13.5px; }
    #hero .chip .k { color: var(--faint); font-size: 12px; }
    #hero .chip.device { border-color: color-mix(in oklab, var(--accent) 40%, var(--line)); }
    #hero .chip.device b { color: color-mix(in oklab, var(--accent) 72%, var(--text)); }
    #hero .readout { display: flex; flex-direction: column; align-items: flex-end;
      gap: 14px; text-align: right; }
    #hero .rl { font-size: 12px; text-transform: uppercase; letter-spacing: .09em;
      color: var(--muted); font-weight: 600; }
    #hero .metric { font-variant-numeric: tabular-nums; font-weight: 700;
      font-size: clamp(34px,5.2vw,60px); line-height: .9; letter-spacing: -.02em;
      margin-top: 4px; white-space: nowrap; }
    #hero .metric .unit { color: var(--muted); font-size: .42em; font-weight: 600; margin-left: 1px; }
    #hero .status { display: inline-flex; align-items: center; gap: 9px;
      padding: 8px 14px 8px 11px; border-radius: 999px; font-size: 13.5px; font-weight: 600;
      border: 1px solid color-mix(in oklab, var(--accent) 45%, var(--line));
      background: color-mix(in oklab, var(--accent) 12%, transparent); }
    #hero .status .beacon { width: 9px; height: 9px; border-radius: 50%;
      background: var(--accent); box-shadow: 0 0 0 0 color-mix(in oklab, var(--accent) 55%, transparent);
      animation: hpulse 2.4s ease-out infinite; }
    #hero .status .when { color: var(--muted); font-weight: 500; }
    @keyframes hpulse { 0%{box-shadow:0 0 0 0 color-mix(in oklab,var(--accent) 55%,transparent);}
      70%{box-shadow:0 0 0 9px transparent;} 100%{box-shadow:0 0 0 0 transparent;} }
    @media (max-width:720px){ #hero .grid{grid-template-columns:1fr;} #hero .readout{align-items:flex-start;text-align:left;} }
    @media (prefers-reduced-motion:reduce){ #hero .status .beacon{animation:none;} }
  |||;

  local html = |||
    <section id="hero">
      <div class="glow"></div>
      <div class="grid">
        <div class="lead">
          <span class="eyebrow">🗓 <b id="family">komarek</b> family <span class="d">·</span> today</span>
          <h1><span id="kid">Jakub's day</span> <span class="rest">on screen</span></h1>
          <div class="chips">
            <span class="chip">🧒 Child</span>
            <span class="chip device">on <b id="dev">a device</b></span>
            <span class="chip">🎮 <span class="k" id="model">android</span></span>
          </div>
        </div>
        <div class="readout">
          <div>
            <div class="rl">On screen today</div>
            <div class="metric" id="st">&mdash;</div>
          </div>
          <span class="status"><span class="beacon"></span> <span id="status">Idle</span> <span class="when" id="when">&middot; no data yet</span></span>
        </div>
      </div>
    </section>
  |||;

  local onRender = |||
    try {
      var root = htmlNode;
      var $ = function (id) { return root.getElementById ? root.getElementById(id) : root.querySelector('#' + id); };
      var series = (data && data.series) || [];
      function byRef(ref, idx) { for (var i = 0; i < series.length; i++) { if (series[i].refId === ref) return series[i]; } return series[idx]; }
      function numField(s) { if (!s || !s.fields) return null; for (var i = 0; i < s.fields.length; i++) { if (s.fields[i].type === 'number') return s.fields[i]; } return null; }
      function lastVal(s) { var f = numField(s); if (!f) return null; var v = f.values, a = (v && v.toArray) ? v.toArray() : v; if (!a || !a.length) return null; for (var i = a.length - 1; i >= 0; i--) { if (a[i] != null && !isNaN(a[i])) return a[i]; } return null; }
      var ts = (typeof getTemplateSrv === 'function') ? getTemplateSrv() : null;
      function rep(v, d) { try { var r = ts ? ts.replace(v) : d; if (!r || r === '' || r.charAt(0) === '$' || r === 'All') return d; return r; } catch (e) { return d; } }

      var fam = rep('$family', 'komarek'), kid = rep('$child', 'your kid');
      if ($('family')) $('family').textContent = fam;
      if ($('kid')) $('kid').textContent = kid + "'s day";

      var secs = lastVal(byRef('A', 0));
      if (secs != null && $('st')) { var h = Math.floor(secs / 3600), m = Math.floor((secs % 3600) / 60); $('st').innerHTML = h + '<span class="unit">h</span> ' + (m < 10 ? '0' + m : m) + '<span class="unit">m</span>'; }

      var gap = lastVal(byRef('B', 1)), hero = $('hero');
      if (gap != null && hero) {
        var active = gap < 120;
        hero.classList.toggle('active', active);
        if ($('status')) $('status').textContent = active ? 'On screen' : 'Idle';
        if ($('when')) { var w = gap < 60 ? 'moments ago' : (gap < 3600 ? (Math.round(gap / 60) + ' min ago') : (Math.round(gap / 3600) + ' h ago')); $('when').textContent = active ? '· right now' : '· last active ' + w; }
      }

      var sd = byRef('C', 2), df = numField(sd);
      if (df && df.labels) { if ($('dev') && df.labels.friendly_name) $('dev').textContent = df.labels.friendly_name; if ($('model') && df.labels.model) $('model').textContent = df.labels.model; }
    } catch (e) { /* keep the static hero on any error */ }
  |||;

  panel.base('gapit-htmlgraphics-panel', '')
  + panel.withOptions({
    html: html,
    css: css,
    rootCSS: '',
    onRender: onRender,
    onInit: '',
    add100Percentage: true,
    centerAlignContent: false,
    overflow: 'hidden',
    renderOnMount: true,
    panelupdateOnMount: true,
    dynamicData: true,
    dynamicFieldDisplayValues: false,
    dynamicProps: false,
    dynamicHtmlGraphics: false,
    onInitOnResize: false,
    codeData: '{}',
    reduceOptions: { calcs: ['lastNotNull'], fields: '', values: false },
  })
  + panel.withTargets([
    sig.screenTime.asTarget(),
    sig.idleGap.asTarget(),
    sig.activeDevice.asTarget(),
  ])
