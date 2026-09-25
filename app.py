"""
FraudGuard AI — Universal Web Application & Vercel Entrypoint.
Provides an interactive, real-time investigation dashboard, graph topology viewer,
EVOI Decision Compass, FinCEN SAR reviewer, and policy simulator.
Compatible with Vercel Serverless Functions (WSGI / ASGI / BaseHTTPRequestHandler)
and local standalone server (`python app.py`).
"""

import os
import sys
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
from wsgiref.simple_server import make_server

# Directory configuration
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
CASES_DIR = os.path.join(ROOT_DIR, "cases")
INNOVATIVE_DIR = os.path.join(ROOT_DIR, "cases_innovative")
SUMMARY_FILE = os.path.join(ROOT_DIR, "output", "benchmark_cases", "benchmark_summary.json")

def load_all_cases():
    """Load benchmark and innovative cases into memory."""
    cases_data = {"benchmark": {}, "innovative": {}, "summary": {}}
    
    # Load benchmark cases
    if os.path.exists(CASES_DIR):
        for f in sorted(os.listdir(CASES_DIR)):
            if f.endswith(".json") and f.startswith("HHG-"):
                cid = f.replace(".json", "")
                try:
                    with open(os.path.join(CASES_DIR, f), "r", encoding="utf-8") as fp:
                        cases_data["benchmark"][cid] = json.load(fp)
                except Exception:
                    pass

    # Load innovative cases
    if os.path.exists(INNOVATIVE_DIR):
        for f in sorted(os.listdir(INNOVATIVE_DIR)):
            if f.endswith(".json") and f.startswith("INV-"):
                cid = f.replace(".json", "")
                try:
                    with open(os.path.join(INNOVATIVE_DIR, f), "r", encoding="utf-8") as fp:
                        cases_data["innovative"][cid] = json.load(fp)
                except Exception:
                    pass

    # Load summary
    if os.path.exists(SUMMARY_FILE):
        try:
            with open(SUMMARY_FILE, "r", encoding="utf-8") as fp:
                cases_data["summary"] = json.load(fp)
        except Exception:
            pass

    return cases_data

ALL_DATA = load_all_cases()

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FraudGuard AI — Autonomous Fraud Operations</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkbg: '#0F172A',
                        panelbg: '#1E293B',
                        accentblue: '#3B82F6',
                        accentgreen: '#10B981',
                        accentred: '#EF4444',
                        accentamber: '#F59E0B',
                        accentpurple: '#8B5CF6'
                    }
                }
            }
        }
    </script>
    <style>
        body { background-color: #0F172A; color: #F8FAFC; font-family: system-ui, -apple-system, sans-serif; }
        .custom-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
        .custom-scroll::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        .badge-fraud { background-color: #EF4444; color: white; }
        .badge-legit { background-color: #10B981; color: white; }
        .badge-uncertain { background-color: #F59E0B; color: white; }
        .badge-sar { background-color: #8B5CF6; color: white; }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <!-- Top Navigation Bar -->
    <header class="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div class="flex items-center space-x-3">
            <div class="bg-blue-600 text-white p-2 rounded-lg text-xl shadow-lg">
                <i class="fa-solid fa-shield-halved"></i>
            </div>
            <div>
                <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                    FraudGuard AI
                    <span class="text-xs px-2 py-0.5 rounded-full bg-blue-900/60 text-blue-300 border border-blue-700 font-mono">TigerGraph × HHGoa</span>
                </h1>
                <p class="text-xs text-slate-400">Autonomous Fraud Investigation & Next-Best Action Agent</p>
            </div>
        </div>

        <div class="flex items-center space-x-4 text-xs text-slate-300">
            <div class="hidden md:flex items-center space-x-3 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
                <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span> TigerGraph Savanna / CE</span>
                <span class="text-slate-600">|</span>
                <span class="text-orange-400 font-semibold"><i class="fa-solid fa-bolt"></i> Groq LPU (qwen/qwen3.8-27b)</span>
            </div>
            <a href="https://github.com/vishnupriyanpr/fraudguard-ai" target="_blank" class="bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-2 transition">
                <i class="fa-brands fa-github text-sm"></i> GitHub Repo
            </a>
        </div>
    </header>

    <!-- Sub-Header Metric Strip -->
    <div class="bg-slate-900/60 border-b border-slate-800 px-6 py-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-center text-xs">
        <div class="bg-slate-800/50 p-2 rounded border border-slate-700/50">
            <div class="text-slate-400">Benchmark Cases</div>
            <div class="text-base font-bold text-white" id="stat-total">20 / 20</div>
        </div>
        <div class="bg-slate-800/50 p-2 rounded border border-slate-700/50">
            <div class="text-slate-400">Confirmed Fraud</div>
            <div class="text-base font-bold text-red-400" id="stat-fraud">12 Cases</div>
        </div>
        <div class="bg-slate-800/50 p-2 rounded border border-slate-700/50">
            <div class="text-slate-400">Cleared Legitimate</div>
            <div class="text-base font-bold text-green-400" id="stat-legit">6 Cases</div>
        </div>
        <div class="bg-slate-800/50 p-2 rounded border border-slate-700/50">
            <div class="text-slate-400">Uncertain / Escalated</div>
            <div class="text-base font-bold text-amber-400" id="stat-uncertain">2 Cases</div>
        </div>
        <div class="bg-slate-800/50 p-2 rounded border border-slate-700/50">
            <div class="text-slate-400">FinCEN SARs Filed</div>
            <div class="text-base font-bold text-purple-400" id="stat-sars">5 Filings</div>
        </div>
        <div class="bg-slate-800/50 p-2 rounded border border-slate-700/50">
            <div class="text-slate-400">Illicit Exposure</div>
            <div class="text-base font-bold text-yellow-300" id="stat-exposure">$4,614.16</div>
        </div>
    </div>

    <!-- Main Workspace -->
    <div class="flex-1 flex flex-col md:flex-row overflow-hidden">
        
        <!-- Sidebar Queue -->
        <aside class="w-full md:w-80 bg-slate-900/90 border-r border-slate-800 p-4 flex flex-col custom-scroll overflow-y-auto">
            <div class="mb-4">
                <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Queue Selection</label>
                <div class="grid grid-cols-2 gap-1 bg-slate-800 p-1 rounded-lg">
                    <button id="btn-mode-benchmark" onclick="switchQueue('benchmark')" class="text-xs py-1.5 rounded font-medium transition bg-blue-600 text-white">Benchmark (20)</button>
                    <button id="btn-mode-innovative" onclick="switchQueue('innovative')" class="text-xs py-1.5 rounded font-medium transition text-slate-400 hover:text-white">Innovative (10)</button>
                </div>
            </div>

            <div class="mb-3">
                <input type="text" id="case-search" placeholder="Search case or pattern..." oninput="filterCases()" class="w-full bg-slate-800 border border-slate-700 text-xs rounded px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500">
            </div>

            <div class="flex-1 space-y-1.5" id="case-list">
                <!-- Injected via JavaScript -->
            </div>
        </aside>

        <!-- Main Investigation View -->
        <main class="flex-1 p-6 overflow-y-auto custom-scroll flex flex-col space-y-6">
            
            <!-- Case Banner -->
            <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <div class="flex items-center gap-3">
                        <h2 class="text-2xl font-extrabold text-white" id="banner-case-id">HHG-001</h2>
                        <span id="banner-verdict-badge" class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider badge-legit">LEGITIMATE</span>
                        <span id="banner-sar-badge" class="hidden px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider badge-sar"><i class="fa-solid fa-landmark"></i> SAR FILED</span>
                    </div>
                    <p class="text-xs text-slate-400 mt-1">
                        Pattern: <span class="font-mono text-slate-200" id="banner-pattern">NONE</span> | 
                        Exposure: <span class="font-mono text-green-400 font-bold" id="banner-exposure">$0.00 USD</span> |
                        Status: <span class="text-blue-400 font-semibold uppercase" id="banner-status">CLOSED_LEGITIMATE</span>
                    </p>
                </div>

                <div class="flex items-center gap-3 self-end md:self-center">
                    <div class="text-right">
                        <div class="text-xs text-slate-400">Fraud Probability</div>
                        <div class="text-xl font-black text-white" id="banner-prob">5.0%</div>
                    </div>
                    <div class="w-12 h-12 rounded-full border-4 border-slate-700 flex items-center justify-center font-bold text-xs" id="prob-circle">
                        0.05
                    </div>
                </div>
            </div>

            <!-- Tabs -->
            <div class="border-b border-slate-800 flex space-x-6 text-sm font-medium">
                <button onclick="switchTab('tab-summary')" id="btn-tab-summary" class="pb-3 border-b-2 border-blue-500 text-blue-400 flex items-center gap-2"><i class="fa-solid fa-file-lines"></i> Summary</button>
                <button onclick="switchTab('tab-graph')" id="btn-tab-graph" class="pb-3 border-b-2 border-transparent text-slate-400 hover:text-white flex items-center gap-2"><i class="fa-solid fa-circle-nodes"></i> Graph Topology</button>
                <button onclick="switchTab('tab-evidence')" id="btn-tab-evidence" class="pb-3 border-b-2 border-transparent text-slate-400 hover:text-white flex items-center gap-2"><i class="fa-solid fa-magnifying-glass-chart"></i> Evidence Chain</button>
                <button onclick="switchTab('tab-nba')" id="btn-tab-nba" class="pb-3 border-b-2 border-transparent text-slate-400 hover:text-white flex items-center gap-2"><i class="fa-solid fa-scale-balanced"></i> Next Best Actions</button>
                <button onclick="switchTab('tab-evoi')" id="btn-tab-evoi" class="pb-3 border-b-2 border-transparent text-slate-400 hover:text-white flex items-center gap-2"><i class="fa-solid fa-compass"></i> EVOI Compass</button>
                <button onclick="switchTab('tab-sar')" id="btn-tab-sar" class="pb-3 border-b-2 border-transparent text-slate-400 hover:text-white flex items-center gap-2"><i class="fa-solid fa-building-columns"></i> FinCEN SAR</button>
            </div>

            <!-- Tab 1: Summary -->
            <div id="tab-summary" class="space-y-5">
                <div class="bg-slate-800/50 border border-slate-700/60 rounded-lg p-4">
                    <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Autonomous Investigation Rationale</h3>
                    <p class="text-sm text-slate-200 leading-relaxed" id="case-summary-text">...</p>
                    <div class="mt-3 text-xs text-slate-400">
                        <span class="text-red-400 font-bold"><i class="fa-solid fa-circle-stop"></i> Resolution Reason:</span> <span id="case-stop-reason">...</span>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-slate-800/40 border border-slate-700/50 p-4 rounded-lg">
                        <div class="text-xs text-slate-400 uppercase font-semibold mb-2"><i class="fa-solid fa-credit-card text-blue-400"></i> Connected Cards</div>
                        <div id="list-cards" class="text-xs font-mono text-slate-200 space-y-1"></div>
                    </div>
                    <div class="bg-slate-800/40 border border-slate-700/50 p-4 rounded-lg">
                        <div class="text-xs text-slate-400 uppercase font-semibold mb-2"><i class="fa-solid fa-mobile-screen text-purple-400"></i> Device Profiles</div>
                        <div id="list-devices" class="text-xs font-mono text-slate-200 space-y-1"></div>
                    </div>
                    <div class="bg-slate-800/40 border border-slate-700/50 p-4 rounded-lg">
                        <div class="text-xs text-slate-400 uppercase font-semibold mb-2"><i class="fa-solid fa-receipt text-green-400"></i> Affected Transactions</div>
                        <div id="list-txns" class="text-xs font-mono text-slate-200 space-y-1"></div>
                    </div>
                </div>
            </div>

            <!-- Tab 2: Graph Topology -->
            <div id="tab-graph" class="hidden space-y-4">
                <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-4 text-xs text-slate-400 flex items-center justify-between">
                    <span><i class="fa-solid fa-network-wired text-blue-400"></i> TigerGraph Topological Neighborhood (Point-In-Time Bounded)</span>
                    <span class="text-green-400">Zero Look-Ahead Bias Enforced</span>
                </div>
                <div id="graph-canvas-container" class="bg-slate-900 border border-slate-800 rounded-xl h-96 flex items-center justify-center p-6 relative">
                    <!-- Dynamic SVG topology rendered via JS -->
                    <div id="graph-svg-render" class="w-full h-full"></div>
                </div>
            </div>

            <!-- Tab 3: Evidence Chain -->
            <div id="tab-evidence" class="hidden space-y-4">
                <h3 class="text-sm font-bold text-slate-300">Graph Evidence Items with Exact References</h3>
                <div id="evidence-container" class="space-y-3"></div>
            </div>

            <!-- Tab 4: Next Best Actions -->
            <div id="tab-nba" class="hidden space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="bg-slate-800/40 border border-slate-700 p-4 rounded-xl">
                        <h4 class="text-xs font-bold uppercase text-slate-400 tracking-wider mb-3">1. Initial Actions (Pre-Verification)</h4>
                        <div id="nba-initial" class="space-y-3"></div>
                    </div>
                    <div class="bg-slate-800/40 border border-slate-700 p-4 rounded-xl">
                        <h4 class="text-xs font-bold uppercase text-slate-400 tracking-wider mb-3">2. Final Actions (Post-Verification)</h4>
                        <div id="nba-final" class="space-y-3"></div>
                    </div>
                </div>
                <div class="bg-blue-900/20 border border-blue-800/50 p-4 rounded-lg text-xs text-blue-200">
                    <span class="font-bold">Recommendation Progression (What Changed):</span> <span id="nba-what-changed">...</span>
                </div>
            </div>

            <!-- Tab 5: EVOI Compass -->
            <div id="tab-evoi" class="hidden space-y-6">
                <div class="bg-slate-800/50 border border-slate-700 p-5 rounded-xl">
                    <h3 class="text-base font-bold text-white mb-1"><i class="fa-solid fa-compass text-blue-400"></i> Expected Value of Information (EVOI) Decision Compass</h3>
                    <p class="text-xs text-slate-400 mb-4">Information-Theoretic Active Learning: Quantifies when customer outreach is economically justified.</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                        <div class="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                            <div class="text-xs text-slate-400">Shannon Entropy H(p)</div>
                            <div class="text-lg font-bold text-blue-400" id="evoi-entropy">0.24 bits</div>
                            <div class="text-[10px] text-slate-500">Max = 1.00b</div>
                        </div>
                        <div class="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                            <div class="text-xs text-slate-400">Information Gain</div>
                            <div class="text-lg font-bold text-green-400" id="evoi-gain">0.68 bits</div>
                            <div class="text-[10px] text-slate-500">Uncertainty reduction</div>
                        </div>
                        <div class="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                            <div class="text-xs text-slate-400">Customer Friction Cost</div>
                            <div class="text-lg font-bold text-amber-400">$15.00 USD</div>
                            <div class="text-[10px] text-slate-500">Operational / Churn</div>
                        </div>
                        <div class="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                            <div class="text-xs text-slate-400">Net EVOI</div>
                            <div class="text-lg font-bold text-purple-400" id="evoi-net">+$11.97 USD</div>
                            <div class="text-[10px] text-slate-500" id="evoi-action">Outreach Justified</div>
                        </div>
                    </div>

                    <div class="mt-4 p-3 bg-slate-900/80 rounded border border-slate-800 text-xs font-mono text-slate-300">
                        Formula: EVOI = E[Loss_uninformed] - E[Loss_informed] - FrictionCost
                    </div>
                </div>
            </div>

            <!-- Tab 6: SAR -->
            <div id="tab-sar" class="hidden space-y-5">
                <div id="sar-content-box" class="bg-slate-800/50 border border-slate-700 p-5 rounded-xl">
                    <!-- Populated dynamically -->
                </div>
            </div>

        </main>
    </div>

    <script>
        const DATA = %DATA_PLACEHOLDER%;
        let currentQueue = 'benchmark';
        let currentCaseId = 'HHG-001';

        function init() {
            renderCaseList();
            loadCase(currentCaseId);
        }

        function switchQueue(mode) {
            currentQueue = mode;
            document.getElementById('btn-mode-benchmark').className = mode === 'benchmark' ? 'text-xs py-1.5 rounded font-medium transition bg-blue-600 text-white' : 'text-xs py-1.5 rounded font-medium transition text-slate-400 hover:text-white';
            document.getElementById('btn-mode-innovative').className = mode === 'innovative' ? 'text-xs py-1.5 rounded font-medium transition bg-blue-600 text-white' : 'text-xs py-1.5 rounded font-medium transition text-slate-400 hover:text-white';
            
            const keys = Object.keys(DATA[currentQueue]);
            if (keys.length > 0) {
                renderCaseList();
                loadCase(keys[0]);
            }
        }

        function renderCaseList() {
            const list = document.getElementById('case-list');
            list.innerHTML = '';
            const cases = DATA[currentQueue];

            for (const [cid, cdata] of Object.entries(cases)) {
                const c = cdata.case;
                const v = c.verdict;
                const badgeColor = v === 'fraud' ? 'bg-red-900/60 text-red-300 border-red-700' : (v === 'legitimate' ? 'bg-green-900/60 text-green-300 border-green-700' : 'bg-amber-900/60 text-amber-300 border-amber-700');
                const isSar = cdata.sar && cdata.sar.file;

                const item = document.createElement('div');
                item.className = `p-2.5 rounded-lg border cursor-pointer transition flex items-center justify-between text-xs ${cid === currentCaseId ? 'bg-blue-900/40 border-blue-500' : 'bg-slate-800/40 border-slate-700/60 hover:bg-slate-800'}`;
                item.onclick = () => loadCase(cid);
                item.innerHTML = `
                    <div>
                        <div class="font-bold font-mono text-white flex items-center gap-1.5">
                            ${cid}
                            ${isSar ? '<span class="text-[10px] text-purple-400" title="SAR Filed"><i class="fa-solid fa-landmark"></i></span>' : ''}
                        </div>
                        <div class="text-[10px] text-slate-400 truncate max-w-[140px]">${c.pattern || 'none'}</div>
                    </div>
                    <div class="text-right">
                        <span class="text-[10px] px-1.5 py-0.5 rounded border font-semibold ${badgeColor}">${v.toUpperCase()}</span>
                        <div class="text-[10px] text-slate-400 mt-0.5">$${c.exposure_usd.toFixed(2)}</div>
                    </div>
                `;
                list.appendChild(item);
            }
        }

        function filterCases() {
            const query = document.getElementById('case-search').value.toLowerCase();
            const items = document.getElementById('case-list').children;
            const cases = Object.entries(DATA[currentQueue]);
            
            cases.forEach(([cid, cdata], idx) => {
                const text = (cid + ' ' + cdata.case.pattern + ' ' + cdata.case.verdict).toLowerCase();
                if (items[idx]) {
                    items[idx].style.display = text.includes(query) ? 'flex' : 'none';
                }
            });
        }

        function loadCase(cid) {
            currentCaseId = cid;
            renderCaseList();

            const cdata = DATA[currentQueue][cid];
            if (!cdata) return;

            const c = cdata.case;
            const sar = cdata.sar;
            const nba = cdata.next_best_actions;

            // Banner
            document.getElementById('banner-case-id').innerText = cid;
            const vBadge = document.getElementById('banner-verdict-badge');
            vBadge.innerText = c.verdict.toUpperCase();
            vBadge.className = `px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${c.verdict === 'fraud' ? 'badge-fraud' : (c.verdict === 'legitimate' ? 'badge-legit' : 'badge-uncertain')}`;
            
            const sarBadge = document.getElementById('banner-sar-badge');
            if (sar && sar.file) {
                sarBadge.classList.remove('hidden');
            } else {
                sarBadge.classList.add('hidden');
            }

            document.getElementById('banner-pattern').innerText = c.pattern.toUpperCase();
            document.getElementById('banner-exposure').innerText = `$${c.exposure_usd.toFixed(2)} USD`;
            document.getElementById('banner-status').innerText = c.status;
            document.getElementById('banner-prob').innerText = `${(c.fraud_probability * 100).toFixed(1)}%`;
            document.getElementById('prob-circle').innerText = c.fraud_probability.toFixed(2);
            document.getElementById('prob-circle').style.borderColor = c.fraud_probability >= 0.7 ? '#EF4444' : (c.fraud_probability <= 0.3 ? '#10B981' : '#F59E0B');

            // Summary
            document.getElementById('case-summary-text').innerText = c.summary || 'No summary recorded.';
            document.getElementById('case-stop-reason').innerText = cdata.stop_reason || 'Defensible resolution reached under policy.';

            // Entity lists
            const cardsBox = document.getElementById('list-cards');
            cardsBox.innerHTML = (c.connected_card_ids && c.connected_card_ids.length) ? c.connected_card_ids.map(card => `<div>💳 ${card}</div>`).join('') : '<div class="text-slate-500">None</div>';

            const devsBox = document.getElementById('list-devices');
            devsBox.innerHTML = (c.connected_device_profiles && c.connected_device_profiles.length) ? c.connected_device_profiles.map(d => `<div class="truncate" title="${d}">📱 ${d}</div>`).join('') : '<div class="text-slate-500">None</div>';

            const txnsBox = document.getElementById('list-txns');
            txnsBox.innerHTML = (c.affected_txn_ids && c.affected_txn_ids.length) ? c.affected_txn_ids.map(t => `<div>🧾 Txn #${t}</div>`).join('') : '<div class="text-slate-500">None (Cleared)</div>';

            // Evidence
            const evBox = document.getElementById('evidence-container');
            evBox.innerHTML = '';
            (c.evidence || []).forEach((ev, i) => {
                const el = document.createElement('div');
                el.className = 'bg-slate-800/40 border border-slate-700/60 p-3 rounded-lg text-xs';
                el.innerHTML = `
                    <div class="flex items-center justify-between text-slate-400 mb-1">
                        <span class="font-bold text-blue-400">#${i+1} [${(ev.source || '').toUpperCase()}]</span>
                        <span class="font-mono text-[10px] text-slate-500">${ev.ref || ''}</span>
                    </div>
                    <div class="text-slate-200 mb-1.5">${ev.claim || ''}</div>
                    <div class="text-[10px] text-slate-500 font-mono">Referenced Entities: ${(ev.entity_ids || []).join(', ') || 'N/A'}</div>
                `;
                evBox.appendChild(el);
            });

            // Next Best Actions
            const nbaInitBox = document.getElementById('nba-initial');
            nbaInitBox.innerHTML = '';
            (nba.initial || []).forEach(a => {
                const routeBadge = a.route === 'auto' ? 'bg-green-900/60 text-green-300 border-green-700' : (a.route === 'L1' ? 'bg-amber-900/60 text-amber-300 border-amber-700' : 'bg-red-900/60 text-red-300 border-red-700');
                nbaInitBox.innerHTML += `
                    <div class="p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-xs">
                        <div class="flex items-center justify-between mb-1">
                            <span class="font-bold text-white font-mono">${a.action}</span>
                            <span class="px-2 py-0.5 rounded border text-[10px] font-bold ${routeBadge}">${a.route}</span>
                        </div>
                        <div class="text-slate-400 text-[11px]">${a.reason}</div>
                    </div>
                `;
            });

            const nbaFinalBox = document.getElementById('nba-final');
            nbaFinalBox.innerHTML = '';
            (nba.final || []).forEach(a => {
                const routeBadge = a.route === 'auto' ? 'bg-green-900/60 text-green-300 border-green-700' : (a.route === 'L1' ? 'bg-amber-900/60 text-amber-300 border-amber-700' : 'bg-red-900/60 text-red-300 border-red-700');
                nbaFinalBox.innerHTML += `
                    <div class="p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-xs">
                        <div class="flex items-center justify-between mb-1">
                            <span class="font-bold text-white font-mono">${a.action}</span>
                            <span class="px-2 py-0.5 rounded border text-[10px] font-bold ${routeBadge}">${a.route}</span>
                        </div>
                        <div class="text-slate-400 text-[11px]">${a.reason}</div>
                    </div>
                `;
            });
            document.getElementById('nba-what-changed').innerText = nba.what_changed || 'No changes required.';

            // EVOI metrics
            const p = c.fraud_probability;
            const h = (p <= 0 || p >= 1) ? 0 : - (p * Math.log2(p) + (1-p) * Math.log2(1-p));
            document.getElementById('evoi-entropy').innerText = `${h.toFixed(2)} bits`;
            document.getElementById('evoi-gain').innerText = `${Math.max(0, 1.0 - h).toFixed(2)} bits`;

            // SAR Tab
            const sarBox = document.getElementById('sar-content-box');
            if (sar && sar.file) {
                sarBox.innerHTML = `
                    <div class="flex items-center justify-between mb-4">
                        <h4 class="text-sm font-bold text-red-400 flex items-center gap-2">
                            <i class="fa-solid fa-triangle-exclamation"></i> Mandatory FinCEN SAR Filing (31 CFR 1020.320)
                        </h4>
                        <span class="bg-orange-950 text-orange-400 border border-orange-700 px-2 py-0.5 rounded text-[11px] font-semibold">
                            <i class="fa-solid fa-bolt"></i> Synthesized via Groq LPU (~0.7s)
                        </span>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs mb-4">
                        <div class="bg-slate-900 p-2.5 rounded border border-slate-800">
                            <span class="text-slate-500 block">Total Suspicious Amount</span>
                            <span class="text-white font-bold font-mono">$${sar.total_amount_usd.toFixed(2)} USD</span>
                        </div>
                        <div class="bg-slate-900 p-2.5 rounded border border-slate-800">
                            <span class="text-slate-500 block">Named Subjects</span>
                            <span class="text-white font-mono">${(sar.subjects || []).join(', ')}</span>
                        </div>
                        <div class="bg-slate-900 p-2.5 rounded border border-slate-800">
                            <span class="text-slate-500 block">Activity Dates</span>
                            <span class="text-white font-mono">${(sar.activity_dates || []).join(', ')}</span>
                        </div>
                        <div class="bg-slate-900 p-2.5 rounded border border-slate-800">
                            <span class="text-slate-500 block">Filing Trigger</span>
                            <span class="text-purple-400 font-semibold truncate" title="${sar.reason}">${sar.reason}</span>
                        </div>
                    </div>
                    <div>
                        <div class="text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">Official Narrative Text:</div>
                        <div class="bg-slate-900 border border-slate-800 p-4 rounded-lg text-xs font-mono text-slate-300 leading-relaxed whitespace-pre-wrap">${sar.narrative}</div>
                    </div>
                `;
            } else {
                sarBox.innerHTML = `
                    <div class="text-center py-10">
                        <div class="text-green-400 text-3xl mb-2"><i class="fa-solid fa-shield-check"></i></div>
                        <div class="text-sm font-bold text-white">No Suspicious Activity Report Required</div>
                        <div class="text-xs text-slate-400 mt-1">Activity was cleared as legitimate or falls below statutory FinCEN filing thresholds.</div>
                    </div>
                `;
            }

            renderGraph(cid, c);
        }

        function renderGraph(cid, c) {
            const container = document.getElementById('graph-svg-render');
            const custId = (c.evidence && c.evidence[0] && c.evidence[0].entity_ids) ? c.evidence[0].entity_ids[0] : 'Customer';
            const cards = c.connected_card_ids || [];
            const txns = c.affected_txn_ids || ['Flagged'];
            const devs = c.connected_device_profiles || [];

            container.innerHTML = `
                <svg class="w-full h-full" viewBox="0 0 700 350">
                    <line x1="150" y1="175" x2="300" y2="100" stroke="#334155" stroke-width="2" />
                    <line x1="300" y1="100" x2="480" y2="100" stroke="#334155" stroke-width="2" />
                    <line x1="480" y1="100" x2="600" y2="175" stroke="#334155" stroke-width="2" />

                    <!-- Customer -->
                    <circle cx="150" cy="175" r="30" fill="#3B82F6" />
                    <text x="150" y="175" text-anchor="middle" fill="white" font-size="10" font-weight="bold" dy=".3em">CUST</text>
                    <text x="150" y="215" text-anchor="middle" fill="#94A3B8" font-size="9">${custId}</text>

                    <!-- Card -->
                    <circle cx="300" cy="100" r="26" fill="#10B981" />
                    <text x="300" y="100" text-anchor="middle" fill="white" font-size="9" font-weight="bold" dy=".3em">CARD</text>
                    <text x="300" y="136" text-anchor="middle" fill="#94A3B8" font-size="8">${cards[0] || 'Card-1'}</text>

                    <!-- Txn -->
                    <circle cx="480" cy="100" r="28" fill="${c.verdict === 'fraud' ? '#EF4444' : (c.verdict === 'legitimate' ? '#10B981' : '#F59E0B')}" />
                    <text x="480" y="100" text-anchor="middle" fill="white" font-size="9" font-weight="bold" dy=".3em">TXN</text>
                    <text x="480" y="138" text-anchor="middle" fill="#94A3B8" font-size="8">$${c.exposure_usd.toFixed(2)}</text>

                    <!-- Device -->
                    <circle cx="600" cy="175" r="24" fill="#8B5CF6" />
                    <text x="600" y="175" text-anchor="middle" fill="white" font-size="8" font-weight="bold" dy=".3em">DEVICE</text>
                    <text x="600" y="210" text-anchor="middle" fill="#94A3B8" font-size="8">${(devs[0] || 'Browser').substring(0, 12)}...</text>
                </svg>
            `;
        }

        function switchTab(tabId) {
            ['tab-summary', 'tab-graph', 'tab-evidence', 'tab-nba', 'tab-evoi', 'tab-sar'].forEach(id => {
                document.getElementById(id).classList.add('hidden');
                document.getElementById('btn-' + id).className = 'pb-3 border-b-2 border-transparent text-slate-400 hover:text-white flex items-center gap-2';
            });
            document.getElementById(tabId).classList.remove('hidden');
            document.getElementById('btn-' + tabId).className = 'pb-3 border-b-2 border-blue-500 text-blue-400 flex items-center gap-2';
        }

        window.onload = init;
    </script>
</body>
</html>
"""

# Render data into HTML
PAGE_CONTENT = HTML_PAGE.replace("%DATA_PLACEHOLDER%", json.dumps(ALL_DATA))


# =====================================================================
# WSGI Application (Vercel & Local Standard)
# =====================================================================
def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")

    # API: List all cases
    if path == "/api/cases":
        body = json.dumps(ALL_DATA).encode("utf-8")
        headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
            ("Access-Control-Allow-Origin", "*"),
        ]
        start_response("200 OK", headers)
        return [body]

    # API: Specific case
    if path.startswith("/api/case/"):
        cid = path.replace("/api/case/", "").strip()
        case_data = ALL_DATA["benchmark"].get(cid) or ALL_DATA["innovative"].get(cid)
        if case_data:
            body = json.dumps(case_data).encode("utf-8")
            status = "200 OK"
        else:
            body = json.dumps({"error": f"Case {cid} not found"}).encode("utf-8")
            status = "404 Not Found"
        headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
            ("Access-Control-Allow-Origin", "*"),
        ]
        start_response(status, headers)
        return [body]

    # Default: Render HTML UI
    body = PAGE_CONTENT.encode("utf-8")
    headers = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "public, max-age=300"),
    ]
    start_response("200 OK", headers)
    return [body]


# =====================================================================
# BaseHTTPRequestHandler (Vercel Alternative Loader)
# =====================================================================
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/api/cases":
            body = json.dumps(ALL_DATA).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif url.path.startswith("/api/case/"):
            cid = url.path.replace("/api/case/", "").strip()
            case_data = ALL_DATA["benchmark"].get(cid) or ALL_DATA["innovative"].get(cid)
            if case_data:
                body = json.dumps(case_data).encode("utf-8")
                self.send_response(200)
            else:
                body = json.dumps({"error": f"Case {cid} not found"}).encode("utf-8")
                self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        else:
            body = PAGE_CONTENT.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=300")
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Serving FraudGuard AI Dashboard on http://localhost:{port}...")
    with make_server("", port, app) as httpd:
        httpd.serve_forever()
