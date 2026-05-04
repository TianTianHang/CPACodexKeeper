import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


PANEL_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CPACodexKeeper Monitor</title>
  <style>
    :root { color-scheme: dark; --bg: #020617; --panel: #0f172a; --panel-2: #111c31; --muted: #94a3b8; --soft: #cbd5e1; --text: #f8fafc; --ok: #22c55e; --warn: #f59e0b; --bad: #ef4444; --line: rgba(148, 163, 184, 0.18); --blue: #38bdf8; --purple: #a78bfa; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; font-family: "Fira Sans", Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: radial-gradient(circle at 18% 0%, rgba(56, 189, 248, 0.16), transparent 30%), radial-gradient(circle at 86% 8%, rgba(167, 139, 250, 0.16), transparent 32%), linear-gradient(180deg, #020617 0%, #07111f 48%, #020617 100%); color: var(--text); }
    main { width: min(1280px, calc(100% - 36px)); margin: 0 auto; padding: 32px 0 48px; }
    header { display: grid; grid-template-columns: 1fr auto; gap: 20px; align-items: start; margin-bottom: 24px; }
    h1 { margin: 0 0 10px; font-family: "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace; font-size: clamp(28px, 4vw, 46px); letter-spacing: -0.06em; }
    .eyebrow { display: inline-flex; align-items: center; gap: 8px; margin-bottom: 12px; color: var(--blue); font: 700 12px/1 "Fira Code", ui-monospace, monospace; letter-spacing: 0.12em; text-transform: uppercase; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 18px rgba(34, 197, 94, 0.85); }
    .sub { color: var(--muted); font-size: 14px; line-height: 1.7; max-width: 780px; }
    .toolbar { display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; padding: 8px; border: 1px solid var(--line); border-radius: 18px; background: rgba(15, 23, 42, 0.72); backdrop-filter: blur(18px); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.22); }
    button, select { border: 1px solid var(--line); background: rgba(2, 6, 23, 0.72); color: var(--text); border-radius: 12px; padding: 10px 12px; font: inherit; outline: none; transition: border-color 180ms ease, background 180ms ease, box-shadow 180ms ease; }
    button { cursor: pointer; font-weight: 700; }
    button:hover, select:hover, button:focus-visible, select:focus-visible { border-color: rgba(56, 189, 248, 0.75); box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.12); }
    .summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }
    .summary-card { position: relative; overflow: hidden; min-height: 118px; border: 1px solid var(--line); border-radius: 24px; padding: 18px; background: linear-gradient(145deg, rgba(15, 23, 42, 0.94), rgba(17, 28, 49, 0.72)); box-shadow: 0 24px 70px rgba(0, 0, 0, 0.24); }
    .summary-card::after { content: ""; position: absolute; inset: auto -24px -42px auto; width: 110px; height: 110px; border-radius: 999px; background: var(--accent, rgba(56, 189, 248, 0.18)); filter: blur(4px); opacity: 0.45; }
    .summary-card span { display: block; color: var(--muted); font-size: 13px; margin-bottom: 16px; }
    .summary-card strong { position: relative; z-index: 1; font-family: "Fira Code", ui-monospace, monospace; font-size: 34px; line-height: 1; letter-spacing: -0.04em; }
    .summary-card small { display: block; margin-top: 10px; color: var(--soft); font-size: 12px; }
    .summary-card.ok { --accent: rgba(34, 197, 94, 0.42); }
    .summary-card.warn { --accent: rgba(245, 158, 11, 0.44); }
    .summary-card.bad { --accent: rgba(239, 68, 68, 0.44); }
    .summary-card.purple { --accent: rgba(167, 139, 250, 0.42); }
    .panel { border: 1px solid var(--line); border-radius: 28px; padding: 18px; background: rgba(15, 23, 42, 0.58); box-shadow: 0 30px 90px rgba(0, 0, 0, 0.22); backdrop-filter: blur(22px); }
    .panel-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 4px 4px 18px; color: var(--muted); font-size: 13px; }
    .panel-title { color: var(--text); font-weight: 800; font-size: 16px; }
    .token-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
    .token-card { position: relative; overflow: hidden; border: 1px solid var(--line); border-radius: 24px; padding: 18px; background: linear-gradient(145deg, rgba(15, 23, 42, 0.96), rgba(2, 6, 23, 0.82)); box-shadow: 0 18px 58px rgba(0, 0, 0, 0.22); transition: border-color 180ms ease, transform 180ms ease, background 180ms ease; }
    .token-card:hover { transform: translateY(-2px); border-color: rgba(56, 189, 248, 0.36); background: linear-gradient(145deg, rgba(17, 28, 49, 0.98), rgba(2, 6, 23, 0.86)); }
    .token-card::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: var(--state-color, var(--line)); }
    .token-card.alive, .token-card.enabled { --state-color: var(--ok); }
    .token-card.network_error, .token-card.invalid, .token-card.error, .token-card.deleted { --state-color: var(--bad); }
    .token-card.skipped, .token-card.disabled, .token-card.refreshed { --state-color: var(--warn); }
    .token-head { display: flex; justify-content: space-between; gap: 14px; align-items: flex-start; margin-bottom: 16px; }
    .name { font-weight: 900; font-size: 18px; letter-spacing: -0.02em; }
    .muted { color: var(--muted); }
    .email { margin-top: 5px; color: var(--muted); font-size: 13px; word-break: break-all; }
    .pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
    .pill { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 6px 10px; font-size: 12px; border: 1px solid var(--line); background: rgba(255,255,255,0.04); white-space: nowrap; }
    .alive, .enabled { color: var(--ok); border-color: rgba(34,197,94,.42); }
    .network_error, .invalid, .error, .deleted { color: var(--bad); border-color: rgba(239,68,68,.44); }
    .skipped, .disabled, .refreshed { color: var(--warn); border-color: rgba(245,158,11,.46); }
    .free { color: var(--ok); border-color: rgba(34,197,94,.42); }
    .plus { color: var(--blue); border-color: rgba(56,189,248,.44); }
    .team { color: var(--purple); border-color: rgba(167,139,250,.46); }
    .unknown, .none { color: var(--muted); }
    .metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 16px 0; }
    .metric { border: 1px solid rgba(148, 163, 184, 0.14); border-radius: 18px; padding: 13px; background: rgba(2, 6, 23, 0.42); }
    .metric-label { display: flex; justify-content: space-between; gap: 10px; color: var(--muted); font-size: 12px; margin-bottom: 9px; }
    .metric-value { color: var(--text); font-family: "Fira Code", ui-monospace, monospace; font-size: 20px; font-weight: 800; }
    .bar { width: 100%; height: 8px; border-radius: 999px; background: rgba(148, 163, 184, 0.16); overflow: hidden; margin-top: 10px; }
    .fill { height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--ok), #86efac); }
    .fill.warn { background: linear-gradient(90deg, var(--warn), #facc15); }
    .fill.bad { background: linear-gradient(90deg, var(--bad), #fb7185); }
    .details { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 16px; }
    .detail { border-top: 1px solid rgba(148, 163, 184, 0.12); padding-top: 12px; min-width: 0; }
    .detail span { display: block; color: var(--muted); font-size: 11px; margin-bottom: 5px; }
    .detail strong { display: block; color: var(--soft); font-size: 13px; font-weight: 700; overflow-wrap: anywhere; }
    .message { margin-top: 14px; padding: 12px; border-radius: 16px; background: rgba(15, 23, 42, 0.64); color: var(--soft); font-size: 13px; line-height: 1.5; }
    .empty { padding: 48px 20px; text-align: center; color: var(--muted); border: 1px dashed rgba(148, 163, 184, 0.22); border-radius: 22px; background: rgba(2, 6, 23, 0.26); }
    @media (max-width: 1080px) { header { grid-template-columns: 1fr; } .toolbar { justify-content: flex-start; } .summary-grid { grid-template-columns: repeat(2, 1fr); } .token-grid { grid-template-columns: 1fr; } }
    @media (max-width: 640px) { main { width: min(100% - 22px, 1280px); padding-top: 22px; } .summary-grid, .metrics, .details { grid-template-columns: 1fr; } .toolbar { display: grid; grid-template-columns: 1fr; } button, select { width: 100%; } .token-head { flex-direction: column; } }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <div class="eyebrow"><span class="dot"></span>Live monitor</div>
        <h1>CPACodexKeeper Monitor</h1>
        <div class="sub" id="meta">等待首次数据...</div>
      </div>
      <div class="toolbar">
        <select id="filter" aria-label="筛选账号状态">
          <option value="all">全部状态</option>
          <option value="alive">Alive</option>
          <option value="invalid">Invalid</option>
          <option value="network_error">Network Error</option>
          <option value="skipped">Skipped</option>
          <option value="error">Error</option>
        </select>
        <button id="refresh" type="button">立即刷新</button>
      </div>
    </header>
    <section class="summary-grid" id="cards"></section>
    <section class="panel">
      <div class="panel-head">
        <span><span class="panel-title">账号状态卡片</span> <span id="progress">巡检进度：0 / 0</span></span>
        <span id="next">自动刷新中</span>
      </div>
      <div class="token-grid" id="rows"><div class="empty">等待首次巡检数据</div></div>
    </section>
  </main>
  <script>
    const refreshMs = __REFRESH_MS__;
    const threshold = __THRESHOLD__;
    let lastSnapshot = null;
    let countdown = Math.floor(refreshMs / 1000);

    function pill(text, cls) { return `<span class="pill ${cls || ''}">${text}</span>`; }
    function esc(value) { return String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
    function normalizePlan(planType) {
      const plan = String(planType || 'unknown').toLowerCase();
      if (plan === 'free') return 'Free';
      if (plan === 'plus') return 'Plus';
      if (plan === 'team') return 'Team';
      return plan === 'unknown' ? 'Unknown' : planType;
    }
    function planClass(planType) {
      const plan = String(planType || 'unknown').toLowerCase();
      return ['free', 'plus', 'team'].includes(plan) ? plan : 'unknown';
    }
    function actionLabel(action) {
      const labels = {none: '无操作', disabled: '已禁用', enabled: '已启用', deleted: '已删除', refreshed: '已刷新'};
      return labels[action] || action || '无操作';
    }
    function quotaRemainingCell(usedPercent, label, emptyText = '未知') {
      if (usedPercent === null || usedPercent === undefined) return `<div class="metric"><div class="metric-label"><span>${esc(label || '额度')}</span><span>${esc(emptyText)}</span></div><div class="metric-value">--</div><div class="bar"><div class="fill" style="width:0%"></div></div></div>`;
      const used = Math.min(100, Math.max(0, Number(usedPercent)));
      const remaining = Math.max(0, 100 - used);
      const cls = used >= threshold ? 'bad' : used >= Math.max(80, threshold - 10) ? 'warn' : '';
      return `<div class="metric"><div class="metric-label"><span>${esc(label || '额度')} 剩余</span><span>已用 ${used}%</span></div><div class="metric-value">${remaining}%</div><div class="bar"><div class="fill ${cls}" style="width:${remaining}%"></div></div></div>`;
    }
    function quotaByWindow(token, wantedLabel, emptyText = '未知') {
      const quota = token.quota || {};
      if (quota.primary_label === wantedLabel) return quotaRemainingCell(quota.primary_used_percent, wantedLabel, emptyText);
      if (quota.secondary_label === wantedLabel) return quotaRemainingCell(quota.secondary_used_percent, wantedLabel, emptyText);
      return quotaRemainingCell(null, wantedLabel, emptyText);
    }
    function quotaMetrics(token) {
      const plan = String(token.plan_type || '').toLowerCase();
      const cells = [];
      if (plan !== 'free') cells.push(quotaByWindow(token, '5h'));
      cells.push(quotaByWindow(token, 'Week'));
      return cells.join('');
    }
    function renderCards(summary, tokens) {
      const planCount = name => tokens.filter(t => String(t.plan_type || '').toLowerCase() === name).length;
      const items = [
        ['总数', summary.total, '本轮纳入巡检', 'purple'],
        ['已处理', summary.processed, `${summary.total || 0} 个任务`, ''],
        ['在线', summary.alive, '当前可用账号', 'ok'],
        ['剩余额度不足', summary.quota_reached, '达到阈值风险', (summary.quota_reached || 0) > 0 ? 'bad' : 'ok'],
        ['已禁用', summary.disabled, '等待额度恢复', 'warn'],
        ['Free', planCount('free'), '免费计划', 'ok'],
        ['Plus', planCount('plus'), 'Plus 计划', ''],
        ['Team', planCount('team'), 'Team 计划', 'purple'],
      ];
      document.getElementById('cards').innerHTML = items.map(([k,v,sub,cls]) => `<div class="summary-card ${cls}"><span>${k}</span><strong>${v ?? 0}</strong><small>${sub}</small></div>`).join('');
    }
    function renderRows(tokens) {
      const filter = document.getElementById('filter').value;
      const visible = filter === 'all' ? tokens : tokens.filter(t => t.health === filter);
      if (!visible.length) {
        document.getElementById('rows').innerHTML = '<div class="empty">没有匹配的账号</div>';
        return;
      }
      document.getElementById('rows').innerHTML = visible.map(t => `
        <article class="token-card ${esc(t.health || '')} ${t.disabled ? 'is-disabled' : 'is-enabled'}">
          <div class="token-head">
            <div>
              <div class="name">${esc(t.name)}</div>
              <div class="email">${esc(t.email || '未知邮箱')}</div>
            </div>
            ${pill(esc(t.health || 'unknown'), t.health || 'unknown')}
          </div>
          <div class="pill-row">
            ${pill(`本轮处理: ${esc(actionLabel(t.action))}`, t.action || 'none')}
            ${t.disabled ? pill('已禁用', 'disabled') : pill('启用', 'enabled')}
            ${pill(`类型: ${esc(normalizePlan(t.plan_type))}`, planClass(t.plan_type))}
            ${pill(`Refresh: ${t.has_refresh_token ? '有' : '无'}`, t.has_refresh_token ? 'enabled' : 'disabled')}
          </div>
          <div class="metrics">
            ${quotaMetrics(t)}
          </div>
          <div class="details">
            <div class="detail"><span>过期</span><strong>${esc(t.remaining_label || '未知')}</strong></div>
            <div class="detail"><span>过期时间</span><strong>${esc(t.expired || '未知')}</strong></div>
            <div class="detail"><span>HTTP</span><strong>${esc(t.status_code ?? '-')}</strong></div>
          </div>
          <div class="message">${esc(t.message || '暂无消息')}<div class="muted">${esc(t.checked_at || '')}</div></div>
        </article>`).join('');
    }
    function render(snapshot) {
      lastSnapshot = snapshot;
      const summary = snapshot.summary || {};
      const tokens = snapshot.tokens || [];
      renderCards(summary, tokens);
      renderRows(tokens);
      document.getElementById('progress').textContent = `巡检进度：${summary.processed || 0} / ${summary.total || 0}`;
      document.getElementById('meta').textContent = `状态：${snapshot.state} | 轮次：${snapshot.round_no} | 更新：${snapshot.updated_at || '-'} | 下轮：${snapshot.next_run_at || '-'}`;
    }
    async function load() {
      const res = await fetch('/api/status', {cache: 'no-store'});
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      render(await res.json());
      countdown = Math.floor(refreshMs / 1000);
    }
    document.getElementById('refresh').addEventListener('click', () => load().catch(err => alert(err.message)));
    document.getElementById('filter').addEventListener('change', () => lastSnapshot && renderRows(lastSnapshot.tokens || []));
    setInterval(() => { countdown -= 1; if (countdown <= 0) load().catch(console.error); document.getElementById('next').textContent = `${Math.max(0, countdown)} 秒后刷新`; }, 1000);
    load().catch(console.error);
  </script>
</body>
</html>
"""


class MonitorServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_cls, keeper, *, refresh_interval: int):
        super().__init__(server_address, handler_cls)
        self.keeper = keeper
        self.refresh_interval = refresh_interval


class MonitorHandler(BaseHTTPRequestHandler):
    server_version = "CPACodexKeeperMonitor/0.1"

    def log_message(self, format, *args):
        return

    def _send_bytes(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self.handle_index()
        if path == "/api/status":
            return self.handle_status()
        if path == "/healthz":
            return self._send_bytes(HTTPStatus.OK, b"ok\n", "text/plain; charset=utf-8")
        body = json.dumps({"error": "not found"}).encode("utf-8")
        return self._send_bytes(HTTPStatus.NOT_FOUND, body, "application/json; charset=utf-8")

    def handle_index(self):
        html = PANEL_HTML.replace("__REFRESH_MS__", str(self.server.refresh_interval * 1000))
        html = html.replace("__THRESHOLD__", str(self.server.keeper.settings.quota_threshold))
        self._send_bytes(HTTPStatus.OK, html.encode("utf-8"), "text/html; charset=utf-8")

    def handle_status(self):
        body = json.dumps(self.server.keeper.get_monitor_snapshot(), ensure_ascii=False).encode("utf-8")
        self._send_bytes(HTTPStatus.OK, body, "application/json; charset=utf-8")


def run_web_server(keeper, host: str, port: int, *, refresh_interval: int):
    server = MonitorServer((host, port), MonitorHandler, keeper, refresh_interval=refresh_interval)
    keeper.log("INFO", f"Web 面板启动: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
