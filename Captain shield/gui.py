"""
AegisGuard — DoS Simulation & Adaptive Defense Lab
===================================================

GUI Module (`gui.py`)
SOC Command Center Interface matching enterprise cybersecurity dashboard designs.
Renders real-time DoS traffic simulation metrics, ML anomaly detection risk scores,
adaptive defense policy enforcement, telemetry window features, incident lifecycle,
and live SOC event console logs.

Strictly intended for controlled local laboratory target:
    http://127.0.0.1:5000/

Controlled local laboratory use only.
"""

from __future__ import annotations

import sys
import threading
import time
from collections import deque
from pathlib import Path
from subprocess import CREATE_NEW_PROCESS_GROUP, Popen
from typing import Optional

import requests
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import ttkbootstrap as tb

from incident_analyzer import IncidentAnalyzer, IncidentRecord
from live_ml_pipeline import LiveMLDefenseMonitor, LiveMLSnapshot
from simulator import SimulationEngine, SimulationSnapshot
from telemetry import TelemetryCollector

# =============================================================================
# APPLICATION CONSTANTS & COLOR PALETTE
# =============================================================================

APP_NAME = "AegisGuard"
APP_SUBTITLE = "DoS Simulation & Adaptive Defense Lab"

SERVER_URL = "http://127.0.0.1:5000"
HEALTH_URL = f"{SERVER_URL}/health"
RESET_URL = f"{SERVER_URL}/lab/reset"

PROJECT_DIR = Path(__file__).resolve().parent
APP_FILE = PROJECT_DIR / "app.py"

# Modern Cyberpunk SOC Color Palette
BG = "#0A0D14"           # Deepest obsidian background
PANEL = "#121824"        # Dark blue-gray card panel
PANEL_2 = "#182232"      # Lighter slate blue panel for inputs/badges
BORDER = "#202D42"       # Subtle slate border

TEXT = "#F8FAFC"         # Crisp white primary text
MUTED = "#94A3B8"        # Slate gray muted text

CYAN = "#38BDF8"        # Bright cyber cyan
BLUE = "#3B82F6"        # Electric primary blue
PURPLE = "#A855F7"      # Telemetry purple
MAGENTA = "#EC4899"     # ML magenta
GREEN = "#10B981"       # Emerald green
GREEN_TEXT = "#34D399"  # Bright green text
AMBER = "#F59E0B"       # Warning amber
ORANGE = "#F97316"      # Alert orange
RED = "#EF4444"         # Danger red
RED_TEXT = "#F87171"    # Bright red text


# =============================================================================
# MAIN SOC GUI APPLICATION
# =============================================================================

class AegisGuardGUI:
    """
    Main SOC Dashboard and Control Interface for AegisGuard.
    Provides a real-time cybersecurity interface for local DoS simulation,
    live telemetry collection, ML anomaly detection, dynamic rate limiting,
    incident lifecycle tracking, and recovery analysis.
    """

    def __init__(self, root: tb.Window) -> None:
        self.root = root
        self.root.title(f"{APP_NAME} — {APP_SUBTITLE}")
        self.root.geometry("1600x950")
        self.root.minsize(1280, 800)
        self.root.configure(background=BG)

        # Server Subprocess Management
        self.server_process: Popen | None = None
        self.server_started_by_gui = False

        # Live Backend Objects
        self.engine: SimulationEngine | None = None
        self.monitor: LiveMLDefenseMonitor | None = None
        self.incident_analyzer = IncidentAnalyzer(incident_risk_threshold=60.0)
        self.current_incident: IncidentRecord | None = None

        # State tracking
        self.previous_risk_score = 0.0
        self.running = False
        self.closing = False
        self.start_time: float | None = None

        # Live Graph Deques (Latest 60 samples ~ 2 minutes at 2s interval)
        self.graph_times: deque[str] = deque(maxlen=60)
        self.graph_rates: deque[float] = deque(maxlen=60)
        self.graph_risks: deque[float] = deque(maxlen=60)

        # Event Log Queue
        self.event_lines: deque[str] = deque(maxlen=100)

        # Tkinter Dynamic Variables
        # Controls
        self.thread_var = tk.IntVar(value=3)
        self.interval_var = tk.DoubleVar(value=10.0)
        self.jitter_var = tk.DoubleVar(value=2.5)
        self.duration_var = tk.DoubleVar(value=30.0)

        # Status Badges
        self.status_var = tk.StringVar(value="INITIALIZING...")
        self.server_var = tk.StringVar(value="CHECKING")
        self.ml_var = tk.StringVar(value="CHECKING")
        self.defense_var = tk.StringVar(value="NORMAL")

        # Live ML Data
        self.prediction_var = tk.StringVar(value="NORMAL")
        self.risk_var = tk.StringVar(value="0.00")
        self.risk_badge_var = tk.StringVar(value="LOW")
        self.rps_var = tk.StringVar(value="0.00 req/s")
        self.clients_var = tk.StringVar(value="0")
        self.request_var = tk.StringVar(value="0")
        self.analysis_var = tk.StringVar(value="0")

        # Simulator Totals
        self.success_var = tk.StringVar(value="0")
        self.limited_var = tk.StringVar(value="0")
        self.failed_var = tk.StringVar(value="0")
        self.avg_response_var = tk.StringVar(value="0.00 ms")

        # Telemetry Features (7-Feature Window)
        self.tel_rps_var = tk.StringVar(value="0.00 req/s")
        self.tel_inter_var = tk.StringVar(value="0.00 s")
        self.tel_burst_var = tk.StringVar(value="0.00")
        self.tel_ratelimit_var = tk.StringVar(value="0.0%")
        self.tel_error_var = tk.StringVar(value="0.0%")
        self.tel_response_var = tk.StringVar(value="0.00 ms")
        self.tel_clients_var = tk.StringVar(value="0")

        # Rate Limiter Detailed Variables
        self.rate_limiter_policy_var = tk.StringVar(value="NORMAL_RATE_LIMIT")
        self.rate_limiter_limit_var = tk.StringVar(value="5 requests / 30 seconds")
        self.rate_limiter_window_var = tk.StringVar(value="30 seconds")
        self.rate_limiter_restriction_var = tk.StringVar(value="INACTIVE")

        # Incident Variables
        self.incident_id_var = tk.StringVar(value="—")
        self.incident_status_var = tk.StringVar(value="NO ACTIVE INCIDENT")
        self.incident_severity_var = tk.StringVar(value="—")
        self.incident_summary_var = tk.StringVar(value="Monitoring is ready. All traffic evaluated via Isolation Forest.")
        self.opened_at_var = tk.StringVar(value="—")
        self.recovered_at_var = tk.StringVar(value="—")

        # Policy & Action
        self.action_var = tk.StringVar(value="NORMAL_RATE_LIMIT")
        self.defense_policy_var = tk.StringVar(value="5 requests / 30 seconds")

        # Setup GUI Components
        self._configure_styles()
        self._build_layout()

        # Window protocol
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start background health checker
        self._start_backend_check()

        # Start UI periodic update loop
        self.root.after(350, self._poll_runtime)

    # =========================================================================
    # STYLE CONFIGURATION
    # =========================================================================

    def _configure_styles(self) -> None:
        """
        Configure custom ttkbootstrap styles matching the modern dark SOC reference design.
        Ensures clear notebook tabs and visible spinbox text.
        """
        style = tb.Style(themename="darkly")

        style.configure("Aegis.TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Panel2.TFrame", background=PANEL_2)

        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))

        style.configure("CardTitle.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 8, "bold"))
        style.configure("CardValue.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 16, "bold"))

        style.configure("Section.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 10, "bold"))
        style.configure("Body.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 8.5))
        style.configure("Muted.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 8))
        style.configure("Status.TLabel", background=PANEL_2, foreground=AMBER, font=("Segoe UI", 9, "bold"))
        style.configure("Metric.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 9, "bold"))

        # Spinbox / Entry styling for crisp numeric visibility
        style.configure("TSpinbox", background=PANEL_2, foreground=TEXT, fieldbackground=PANEL_2, insertcolor=TEXT, font=("Segoe UI", 9, "bold"))

        # Pipeline Node Base Styles
        style.configure("NodeNormal.TLabel", background=PANEL_2, foreground=MUTED, font=("Segoe UI", 8, "bold"))
        style.configure("NodeActive.TLabel", background=BLUE, foreground="#FFFFFF", font=("Segoe UI", 8, "bold"))
        style.configure("NodeOk.TLabel", background="#064E3B", foreground=GREEN_TEXT, font=("Segoe UI", 8, "bold"))
        style.configure("NodeWarn.TLabel", background="#78350F", foreground=AMBER, font=("Segoe UI", 8, "bold"))
        style.configure("NodeDanger.TLabel", background="#7F1D1D", foreground=RED_TEXT, font=("Segoe UI", 8, "bold"))

        # Notebook tab bar styling with bright active accent and unclipped tab padding
        style.configure("TNotebook", background=PANEL, borderwidth=0, tabmargins=[2, 2, 2, 0])
        style.configure("TNotebook.Tab", background=PANEL_2, foreground=MUTED, padding=[14, 8], font=("Segoe UI", 9, "bold"))
        style.map(
            "TNotebook.Tab",
            background=[("selected", PANEL)],
            foreground=[("selected", CYAN)],
        )

    # =========================================================================
    # MAIN LAYOUT ASSEMBLY
    # =========================================================================

    def _build_layout(self) -> None:
        """
        Assemble outer layout structure: Header, Sidebar, and Main Content Area.
        """
        outer = ttk.Frame(self.root, style="Aegis.TFrame")
        outer.pack(fill="both", expand=True, padx=14, pady=12)

        self._build_header(outer)

        content = ttk.Frame(outer, style="Aegis.TFrame")
        content.pack(fill="both", expand=True, pady=(10, 0))

        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        self._build_sidebar(content)
        self._build_main_area(content)

    # =========================================================================
    # HEADER BAR
    # =========================================================================

    def _build_header(self, parent) -> None:
        """
        Build top header bar with title, subtitle, and dynamic status pills.
        """
        header = ttk.Frame(parent, style="Aegis.TFrame")
        header.pack(fill="x")

        left = ttk.Frame(header, style="Aegis.TFrame")
        left.pack(side="left", fill="x", expand=True)

        title_box = ttk.Frame(left, style="Aegis.TFrame")
        title_box.pack(anchor="w")

        ttk.Label(title_box, text="🛡️ ", font=("Segoe UI Emoji", 18), background=BG).pack(side="left")
        ttk.Label(title_box, text=APP_NAME, style="Title.TLabel").pack(side="left")

        ttk.Label(left, text=APP_SUBTITLE, style="Subtitle.TLabel").pack(anchor="w", pady=(1, 0))

        right = ttk.Frame(header, style="Aegis.TFrame")
        right.pack(side="right")

        pills_frame = ttk.Frame(right, style="Aegis.TFrame")
        pills_frame.pack(side="right")

        self.pill_lab = ttk.Label(
            pills_frame,
            text=" 🏠 LOCAL LAB ONLY  http://127.0.0.1:5000/ ",
            style="NodeNormal.TLabel",
            padding=(6, 4),
        )
        self.pill_lab.pack(side="left", padx=3)

        self.pill_server = ttk.Label(
            pills_frame,
            text=" 🟢 SERVER: CHECKING ",
            style="NodeNormal.TLabel",
            padding=(6, 4),
        )
        self.pill_server.pack(side="left", padx=3)

        self.pill_ml = ttk.Label(
            pills_frame,
            text=" 🟢 ML: CHECKING ",
            style="NodeNormal.TLabel",
            padding=(6, 4),
        )
        self.pill_ml.pack(side="left", padx=3)

        self.pill_defense = ttk.Label(
            pills_frame,
            text=" 🟢 DEFENSE: ENABLED ",
            style="NodeOk.TLabel",
            padding=(6, 4),
        )
        self.pill_defense.pack(side="left", padx=3)

        self.pill_theme = ttk.Label(
            pills_frame,
            text=" 🌙 ",
            style="NodeNormal.TLabel",
            padding=(6, 4),
        )
        self.pill_theme.pack(side="left", padx=3)

    # =========================================================================
    # SIDEBAR CONTROLS
    # =========================================================================

    def _build_sidebar(self, parent) -> None:
        """
        Build left control sidebar: Parameters, Control Buttons, Runtime Status, Presets, Info Banner.
        """
        sidebar = ttk.Frame(parent, width=275, style="Panel.TFrame")
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        sidebar.grid_propagate(False)

        # Section: Lab Control
        self._section_label(sidebar, "🚀 LAB CONTROL").pack(anchor="w", padx=12, pady=(12, 6))

        self._control_label(sidebar, "Worker Threads")
        ttk.Spinbox(sidebar, from_=1, to=32, textvariable=self.thread_var, width=12, font=("Segoe UI", 9, "bold")).pack(fill="x", padx=12, pady=(0, 6))

        self._control_label(sidebar, "Request Interval (sec)")
        ttk.Entry(sidebar, textvariable=self.interval_var, font=("Segoe UI", 9, "bold")).pack(fill="x", padx=12, pady=(0, 6))

        self._control_label(sidebar, "Jitter (sec)")
        ttk.Entry(sidebar, textvariable=self.jitter_var, font=("Segoe UI", 9, "bold")).pack(fill="x", padx=12, pady=(0, 6))

        self._control_label(sidebar, "Duration (sec)")
        ttk.Entry(sidebar, textvariable=self.duration_var, font=("Segoe UI", 9, "bold")).pack(fill="x", padx=12, pady=(0, 10))

        # Control Buttons
        tb.Button(
            sidebar,
            text="▶ START SIMULATION",
            command=self.start_simulation,
            bootstyle="success",
        ).pack(fill="x", padx=12, pady=3)

        self.stop_button = tb.Button(
            sidebar,
            text="■ STOP SIMULATION",
            command=self.stop_simulation,
            bootstyle="danger",
            state="disabled",
        )
        self.stop_button.pack(fill="x", padx=12, pady=3)

        tb.Button(
            sidebar,
            text="↺ RESET LAB",
            command=self.reset_lab,
            bootstyle="secondary",
        ).pack(fill="x", padx=12, pady=3)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=12, pady=10)

        # Section: Simulation Presets
        self._section_label(sidebar, "📊 SIMULATION PRESETS").pack(anchor="w", padx=12, pady=(0, 6))

        tb.Button(
            sidebar,
            text="📈 Normal Traffic",
            command=self._normal_preset,
            bootstyle="info-outline",
        ).pack(fill="x", padx=12, pady=3)

        tb.Button(
            sidebar,
            text="🔥 Controlled Attack",
            command=self._attack_preset,
            bootstyle="warning-outline",
        ).pack(fill="x", padx=12, pady=3)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=12, pady=10)

        # Section: Runtime Status
        self._section_label(sidebar, "💻 RUNTIME STATUS").pack(anchor="w", padx=12, pady=(0, 6))
        self._status_row(sidebar, "Server Process", self.server_var)
        self._status_row(sidebar, "ML Model Runtime", self.ml_var)
        self._status_row(sidebar, "Adaptive Defense", self.defense_var)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=12, pady=10)

        # Info Scope Banner
        self._section_label(sidebar, "ℹ INFO").pack(anchor="w", padx=12, pady=(0, 4))
        ttk.Label(
            sidebar,
            text=(
                "LOCAL LAB ONLY\n"
                "Target: http://127.0.0.1:5000/\n\n"
                "• 2-Second Telemetry Feature Window\n"
                "• Isolation Forest Anomaly Detection\n"
                "• Adaptive Rate Limiting & Restriction"
            ),
            style="Muted.TLabel",
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 0))

    # =========================================================================
    # MAIN CONTENT AREA
    # =========================================================================

    def _build_main_area(self, parent) -> None:
        """
        Build main dashboard grid: Defense Pipeline, KPI Cards, Dual Charts, ML Notebook, Event Console, Incident Panel.
        """
        main = ttk.Frame(parent, style="Aegis.TFrame")
        main.grid(row=0, column=1, sticky="nsew")

        main.rowconfigure(2, weight=4)  # Generous weight for chart area
        main.rowconfigure(3, weight=2)
        main.columnconfigure(0, weight=1)

        # Top Pipeline Visualizer
        self._build_pipeline_visualizer(main)

        # KPI Cards
        self._build_kpis(main)

        # Middle Area: Charts (Left) & Notebook (Right)
        self._build_middle_area(main)

        # Bottom Area: Events (Left) & Incident Panel (Right)
        self._build_bottom_area(main)

    # =========================================================================
    # DEFENSE PIPELINE ARCHITECTURE VISUALIZER
    # =========================================================================

    def _build_pipeline_visualizer(self, parent) -> None:
        """
        Build horizontal visual cards representing the AegisGuard architecture.
        Node 6 (RATE LIMITER) is prominently highlighted with dynamic rate limit policy.
        """
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        header_box = ttk.Frame(frame, style="Panel.TFrame")
        header_box.pack(anchor="w", padx=12, pady=(6, 4))
        ttk.Label(header_box, text="⚙️ ", font=("Segoe UI Emoji", 10), background=PANEL).pack(side="left")
        ttk.Label(header_box, text="DEFENSE PIPELINE ARCHITECTURE", style="CardTitle.TLabel").pack(side="left")

        nodes_frame = ttk.Frame(frame, style="Panel.TFrame")
        nodes_frame.pack(fill="x", padx=12, pady=(0, 8))

        stages = [
            ("🔗 TRAFFIC", "node_traffic"),
            ("➔", None),
            ("📊 TELEMETRY", "node_telemetry"),
            ("➔", None),
            ("🧠 ML DETECTOR", "node_ml"),
            ("➔", None),
            ("⚡ RISK SCORE", "node_risk"),
            ("➔", None),
            ("🛡️ ADAPTIVE DEFENSE", "node_defense"),
            ("➔", None),
            ("🗄️ RATE LIMITER\n   5 req / 30s", "node_limiter"),
            ("➔", None),
            ("📄 HTTP RESPONSE\n   200 / 429", "node_http"),
        ]

        self.pipeline_labels: dict[str, ttk.Label] = {}

        for text, node_key in stages:
            if node_key is None:
                lbl = ttk.Label(nodes_frame, text=text, style="Muted.TLabel", font=("Segoe UI", 10, "bold"))
                lbl.pack(side="left", padx=3)
            else:
                lbl = ttk.Label(
                    nodes_frame,
                    text=f" {text} ",
                    style="NodeNormal.TLabel",
                    padding=(6, 5),
                    justify="center",
                )
                lbl.pack(side="left", padx=2)
                self.pipeline_labels[node_key] = lbl

    # =========================================================================
    # KPI METRIC CARDS
    # =========================================================================

    def _build_kpis(self, parent) -> None:
        """
        Build row of 5 KPI cards displaying real live runtime metrics.
        """
        frame = ttk.Frame(parent, style="Aegis.TFrame")
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        for column in range(5):
            frame.columnconfigure(column, weight=1)

        self._kpi_card_with_badge(frame, 0, "🛡️ ML RISK (0–100)", self.risk_var, self.risk_badge_var)
        self._metric_card(frame, 1, "📊 REQUEST RATE", self.rps_var)
        self._metric_card(frame, 2, "👤 ACTIVE CLIENTS", self.clients_var)
        self._metric_card(frame, 3, "🔄 ML ANALYSES", self.analysis_var)
        self._metric_card(frame, 4, "📋 TOTAL REQUESTS", self.request_var)

    def _kpi_card_with_badge(self, parent, column: int, title: str, var: tk.StringVar, badge_var: tk.StringVar) -> None:
        card = ttk.Frame(parent, style="Panel.TFrame")
        card.grid(row=0, column=column, sticky="nsew", padx=3)

        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(8, 2))

        val_box = ttk.Frame(card, style="Panel.TFrame")
        val_box.pack(anchor="w", padx=10, pady=(0, 8))

        ttk.Label(val_box, textvariable=var, style="CardValue.TLabel").pack(side="left")
        self.lbl_risk_badge = ttk.Label(val_box, textvariable=badge_var, style="NodeOk.TLabel", padding=(4, 2))
        self.lbl_risk_badge.pack(side="left", padx=(8, 0))

    # =========================================================================
    # MIDDLE AREA (LARGE CHARTS & NOTEBOOK)
    # =========================================================================

    def _build_middle_area(self, parent) -> None:
        """
        Build middle region containing Matplotlib dual charts and Notebook tabs.
        """
        middle = ttk.Frame(parent, style="Aegis.TFrame")
        middle.grid(row=2, column=0, sticky="nsew")

        middle.rowconfigure(0, weight=1)
        middle.columnconfigure(0, weight=3)
        middle.columnconfigure(1, weight=2)

        self._build_chart_panel(middle)
        self._build_notebook_panel(middle)

    # =========================================================================
    # LIVE TRAFFIC & ML RISK DUAL CHARTS (LARGE & UNCOMPRESSED)
    # =========================================================================

    def _build_chart_panel(self, parent) -> None:
        """
        Build expansive Matplotlib chart area with two large subplots:
        Subplot 1: REAL-TIME TRAFFIC (requests_per_second over time)
        Subplot 2: ML RISK SCORE (0-100 over time with 30 Watch, 60 Suspicious, 80 High Risk lines)
        """
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        header_box = ttk.Frame(panel, style="Panel.TFrame")
        header_box.grid(row=0, column=0, sticky="w", padx=12, pady=(8, 2))
        ttk.Label(header_box, text="📈 ", font=("Segoe UI Emoji", 10), background=PANEL).pack(side="left")
        ttk.Label(header_box, text="REAL-TIME TRAFFIC & ML RISK MONITOR", style="CardTitle.TLabel").pack(side="left")

        # Large Figure for high readability
        self.figure = Figure(figsize=(8.5, 5.2), dpi=100, facecolor=PANEL)

        # Subplot 1: REAL-TIME TRAFFIC
        self.ax_rate = self.figure.add_subplot(211)
        self.ax_rate.set_facecolor(PANEL)
        self.ax_rate.tick_params(colors=MUTED, labelsize=8)
        for spine in self.ax_rate.spines.values():
            spine.set_color(BORDER)
        self.ax_rate.grid(True, alpha=0.15, color=BORDER, linestyle=":")
        self.ax_rate.set_title("REAL-TIME TRAFFIC  (Request Rate: requests/sec)", color=TEXT, fontsize=8, loc="left", fontweight="bold")

        # Subplot 2: ML RISK SCORE
        self.ax_risk = self.figure.add_subplot(212, sharex=self.ax_rate)
        self.ax_risk.set_facecolor(PANEL)
        self.ax_risk.tick_params(colors=MUTED, labelsize=8)
        for spine in self.ax_risk.spines.values():
            spine.set_color(BORDER)
        self.ax_risk.grid(True, alpha=0.15, color=BORDER, linestyle=":")
        self.ax_risk.set_title("ML RISK SCORE  (0 – 100)", color=TEXT, fontsize=8, loc="left", fontweight="bold")
        self.ax_risk.set_xlabel("Time (seconds, 2-second windows)", color=MUTED, fontsize=8)

        self.figure.tight_layout(pad=1.4)

        self.canvas = FigureCanvasTkAgg(self.figure, master=panel)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))

    # =========================================================================
    # ML & TELEMETRY DETAIL NOTEBOOK (EXPLICIT UNCLIPPED TAB LABELS)
    # =========================================================================

    def _build_notebook_panel(self, parent) -> None:
        """
        Build notebook panel with 3 wide, clearly styled tab titles:
        1. LIVE ML ANALYSIS
        2. 7-FEATURE TELEMETRY
        3. MODEL PERFORMANCE
        """
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        notebook = ttk.Notebook(panel)
        notebook.pack(fill="both", expand=True, padx=6, pady=6)

        # Tab 1: LIVE ML ANALYSIS
        tab_ml = ttk.Frame(notebook, style="Panel.TFrame")
        notebook.add(tab_ml, text="  LIVE ML ANALYSIS  ")
        self._build_tab_ml(tab_ml)

        # Tab 2: 7-FEATURE TELEMETRY
        tab_telemetry = ttk.Frame(notebook, style="Panel.TFrame")
        notebook.add(tab_telemetry, text="  7-FEATURE TELEMETRY  ")
        self._build_tab_telemetry(tab_telemetry)

        # Tab 3: MODEL PERFORMANCE
        tab_perf = ttk.Frame(notebook, style="Panel.TFrame")
        notebook.add(tab_perf, text="  MODEL PERFORMANCE  ")
        self._build_tab_performance(tab_perf)

    # -------------------------------------------------------------------------
    # TAB 1: LIVE ML ANALYSIS & PROMINENT RATE LIMITER CARD
    # -------------------------------------------------------------------------

    def _build_tab_ml(self, parent) -> None:
        """
        Build Tab 1 content featuring ML Classification and a prominent Rate Limiter status card.
        """
        header_box = ttk.Frame(parent, style="Panel.TFrame")
        header_box.pack(anchor="w", padx=10, pady=(8, 6))
        ttk.Label(header_box, text="⚡ ", font=("Segoe UI Emoji", 10), background=PANEL).pack(side="left")
        ttk.Label(header_box, text="ML CLASSIFICATION & ADAPTIVE POLICY", style="CardTitle.TLabel").pack(side="left")

        # Top Row: Prediction & Risk Score Gauges
        gauges_frame = ttk.Frame(parent, style="Panel.TFrame")
        gauges_frame.pack(fill="x", padx=10, pady=4)

        # Prediction Box
        pred_box = ttk.Frame(gauges_frame, style="Panel2.TFrame", padding=6)
        pred_box.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Label(pred_box, text="📈 Model Prediction", style="Muted.TLabel", background=PANEL_2).pack(side="left")
        self.lbl_prediction_badge = ttk.Label(pred_box, textvariable=self.prediction_var, style="NodeOk.TLabel", padding=(6, 2))
        self.lbl_prediction_badge.pack(side="right")

        # Risk Score Box
        risk_box = ttk.Frame(gauges_frame, style="Panel2.TFrame", padding=6)
        risk_box.pack(side="right", fill="x", expand=True, padx=(4, 0))
        ttk.Label(risk_box, text="⚡ Risk Score", style="Muted.TLabel", background=PANEL_2).pack(side="left")
        
        r_val_frame = ttk.Frame(risk_box, style="Panel2.TFrame")
        r_val_frame.pack(side="right")
        ttk.Label(r_val_frame, textvariable=self.risk_var, font=("Segoe UI", 10, "bold"), foreground=TEXT, background=PANEL_2).pack(side="left")
        ttk.Label(r_val_frame, text=" / 100", font=("Segoe UI", 8), foreground=MUTED, background=PANEL_2).pack(side="left")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=6)

        # Prominent Dedicated Rate Limiter Status Card
        rl_card = ttk.Frame(parent, style="Panel2.TFrame", padding=8)
        rl_card.pack(fill="x", padx=10, pady=4)

        rl_title_box = ttk.Frame(rl_card, style="Panel2.TFrame")
        rl_title_box.pack(anchor="w", pady=(0, 4))
        ttk.Label(rl_title_box, text="🗄️ ", font=("Segoe UI Emoji", 10), background=PANEL_2).pack(side="left")
        ttk.Label(rl_title_box, text="PROMINENT RATE LIMITER STATUS", font=("Segoe UI", 9, "bold"), foreground=CYAN, background=PANEL_2).pack(side="left")

        self._detail_row_bg(rl_card, "Active Policy", self.rate_limiter_policy_var, PANEL_2)
        self._detail_row_bg(rl_card, "Request Limit", self.rate_limiter_limit_var, PANEL_2)
        self._detail_row_bg(rl_card, "Evaluation Window", self.rate_limiter_window_var, PANEL_2)
        self._detail_row_bg(rl_card, "HTTP 429 Rate Limited", self.limited_var, PANEL_2)
        self._detail_row_bg(rl_card, "Temporary Restriction", self.rate_limiter_restriction_var, PANEL_2)

        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=6)

        # Details list with icons matching reference image
        self._detail_row_icon(parent, "🛡️", "Adaptive Defense State", self.defense_var)
        self._detail_row_icon(parent, "⚙️", "Active Defense Action", self.action_var)
        self._detail_row_icon(parent, "👤", "Active Logical Clients", self.clients_var)

    # -------------------------------------------------------------------------
    # TAB 2: 7-FEATURE TELEMETRY
    # -------------------------------------------------------------------------

    def _build_tab_telemetry(self, parent) -> None:
        """
        Build Tab 2 content: Displays the 7 exact ML telemetry features in order.
        """
        header_box = ttk.Frame(parent, style="Panel.TFrame")
        header_box.pack(anchor="w", padx=10, pady=(8, 6))
        ttk.Label(header_box, text="📊 ", font=("Segoe UI Emoji", 10), background=PANEL).pack(side="left")
        ttk.Label(header_box, text="2-SECOND TELEMETRY FEATURE WINDOW", style="CardTitle.TLabel").pack(side="left")

        self._detail_row_icon(parent, "1.", "Request Rate", self.tel_rps_var)
        self._detail_row_icon(parent, "2.", "Avg Inter-Request Time", self.tel_inter_var)
        self._detail_row_icon(parent, "3.", "Burst Ratio", self.tel_burst_var)
        self._detail_row_icon(parent, "4.", "Rate-Limit Ratio", self.tel_ratelimit_var)
        self._detail_row_icon(parent, "5.", "Error Ratio", self.tel_error_var)
        self._detail_row_icon(parent, "6.", "Avg Response Time", self.tel_response_var)
        self._detail_row_icon(parent, "7.", "Active Clients", self.tel_clients_var)

        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=8)
        ttk.Label(
            parent,
            text="Telemetry values are computed across a rolling 2-second window to match ML model calibration.",
            style="Muted.TLabel",
            justify="left",
            wraplength=340,
        ).pack(anchor="w", padx=10)

    # -------------------------------------------------------------------------
    # TAB 3: MODEL PERFORMANCE
    # -------------------------------------------------------------------------

    def _build_tab_performance(self, parent) -> None:
        """
        Build Tab 3 content: Display validated historical evaluation metrics.
        """
        header_box = ttk.Frame(parent, style="Panel.TFrame")
        header_box.pack(anchor="w", padx=10, pady=(8, 6))
        ttk.Label(header_box, text="🎯 ", font=("Segoe UI Emoji", 10), background=PANEL).pack(side="left")
        ttk.Label(header_box, text="HISTORICAL VALIDATION METRICS", style="CardTitle.TLabel").pack(side="left")

        grid_frame = ttk.Frame(parent, style="Panel.TFrame")
        grid_frame.pack(fill="x", padx=10, pady=2)

        metrics = [
            ("Model Architecture", "Isolation Forest"),
            ("Accuracy", "98.31%"),
            ("Precision", "95.65%"),
            ("Recall", "100.00%"),
            ("F1-Score", "97.78%"),
            ("Unseen Test Set", "59 Feature Windows"),
            ("Normal Windows", "36 / 37 Correct (1 FP)"),
            ("Anomaly Windows", "22 / 22 Detected (0 Missed)"),
        ]

        for label, val in metrics:
            row = ttk.Frame(grid_frame, style="Panel.TFrame")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, style="Muted.TLabel").pack(side="left")
            ttk.Label(row, text=val, style="Metric.TLabel").pack(side="right")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=8)
        ttk.Label(
            parent,
            text="HISTORICAL VALIDATION / VALIDATED TEST SET\nMeasured offline evaluation on unseen test dataset.",
            style="Muted.TLabel",
            justify="left",
            wraplength=340,
        ).pack(anchor="w", padx=10)

    # =========================================================================
    # BOTTOM AREA (EVENTS & INCIDENT ANALYZER)
    # =========================================================================

    def _build_bottom_area(self, parent) -> None:
        """
        Build bottom region containing Live Events console and Incident Analyzer panel.
        """
        bottom = ttk.Frame(parent, style="Aegis.TFrame")
        bottom.grid(row=3, column=0, sticky="nsew", pady=(8, 0))

        bottom.rowconfigure(0, weight=1)
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=2)

        self._build_events_panel(bottom)
        self._build_incident_panel(bottom)

    # =========================================================================
    # LIVE EVENT CONSOLE (SOC LOG WITH CLEAR LOG BUTTON)
    # =========================================================================

    def _build_events_panel(self, parent) -> None:
        """
        Build scrollable dark event log console matching reference image,
        complete with [ Clear Log ] header button.
        """
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        header_row = ttk.Frame(panel, style="Panel.TFrame")
        header_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(6, 4))

        ttk.Label(header_row, text="💻 ", font=("Segoe UI Emoji", 10), background=PANEL).pack(side="left")
        ttk.Label(header_row, text="LIVE EVENT CONSOLE (SOC LOG)", style="CardTitle.TLabel").pack(side="left")

        # Clear Log Button
        tb.Button(
            header_row,
            text="Clear Log",
            command=self._clear_events,
            bootstyle="secondary-outline",
            padding=(6, 2),
        ).pack(side="right")

        self.event_text = tk.Text(
            panel,
            background="#070A0F",
            foreground=TEXT,
            insertbackground=TEXT,
            relief="flat",
            borderwidth=0,
            wrap="word",
            font=("Consolas", 8),
        )
        self.event_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))
        self.event_text.configure(state="disabled")

    # =========================================================================
    # INCIDENT ANALYSIS & RECOVERY PANEL
    # =========================================================================

    def _build_incident_panel(self, parent) -> None:
        """
        Build Incident Analysis & HTTP Counters panel matching reference image.
        """
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Incident Section Header
        inc_header = ttk.Frame(panel, style="Panel.TFrame")
        inc_header.pack(fill="x", padx=10, pady=(6, 4))
        ttk.Label(inc_header, text="⚠️ ", font=("Segoe UI Emoji", 10), background=PANEL).pack(side="left")
        ttk.Label(inc_header, text="INCIDENT LIFECYCLE & RECOVERY", style="CardTitle.TLabel").pack(side="left")

        # Badge and ID row
        badge_row = ttk.Frame(panel, style="Panel.TFrame")
        badge_row.pack(fill="x", padx=10, pady=2)

        self.lbl_incident_badge = ttk.Label(badge_row, textvariable=self.incident_status_var, style="NodeOk.TLabel", padding=(6, 3))
        self.lbl_incident_badge.pack(side="left")

        ttk.Label(badge_row, textvariable=self.incident_id_var, font=("Segoe UI", 10, "bold"), foreground=TEXT, background=PANEL).pack(side="right")

        # Incident Details Rows (Matches Reference Image)
        self._detail_row_icon(panel, "📌", "Severity", self.incident_severity_var)
        
        desc_box = ttk.Frame(panel, style="Panel.TFrame")
        desc_box.pack(fill="x", padx=10, pady=2)
        ttk.Label(desc_box, text="📝 Description", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(desc_box, textvariable=self.incident_summary_var, style="Body.TLabel", wraplength=340, justify="left").pack(anchor="w", padx=(16, 0))

        self._detail_row_icon(panel, "📅", "Opened At", self.opened_at_var)
        self._detail_row_icon(panel, "📅", "Recovered At", self.recovered_at_var)

        ttk.Separator(panel, orient="horizontal").pack(fill="x", padx=10, pady=6)

        # Simulation HTTP Counters Section Header
        http_header = ttk.Frame(panel, style="Panel.TFrame")
        http_header.pack(fill="x", padx=10, pady=(2, 4))
        ttk.Label(http_header, text="📊 ", font=("Segoe UI Emoji", 10), background=PANEL).pack(side="left")
        ttk.Label(http_header, text="SIMULATION HTTP COUNTERS", style="CardTitle.TLabel").pack(side="left")

        # HTTP Counters with Color Accents matching Reference Image
        self._counter_row(panel, "🟩 HTTP 200 Accepted", self.success_var, GREEN_TEXT)
        self._counter_row(panel, "🟥 HTTP 429 Rate Limited", self.limited_var, RED_TEXT)
        self._counter_row(panel, "⚠️ Failed / Connection Errors", self.failed_var, AMBER)
        self._counter_row(panel, "🕒 Average Response Time", self.avg_response_var, CYAN)

    # =========================================================================
    # SMALL UI BUILDERS & HELPERS
    # =========================================================================

    def _section_label(self, parent, text: str) -> ttk.Label:
        return ttk.Label(parent, text=text, style="Section.TLabel")

    def _control_label(self, parent, text: str) -> None:
        ttk.Label(parent, text=text, style="Muted.TLabel").pack(anchor="w", padx=12, pady=(0, 2))

    def _status_row(self, parent, label: str, variable: tk.StringVar) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", padx=12, pady=2)
        ttk.Label(row, text=label, style="Muted.TLabel").pack(side="left")
        ttk.Label(row, textvariable=variable, style="Metric.TLabel").pack(side="right")

    def _detail_row_icon(self, parent, icon: str, label: str, variable: tk.StringVar) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", padx=10, pady=2)
        lbl_box = ttk.Frame(row, style="Panel.TFrame")
        lbl_box.pack(side="left")
        ttk.Label(lbl_box, text=f"{icon} ", font=("Segoe UI Emoji", 8), background=PANEL).pack(side="left")
        ttk.Label(lbl_box, text=label, style="Muted.TLabel").pack(side="left")
        ttk.Label(row, textvariable=variable, style="Metric.TLabel").pack(side="right")

    def _detail_row_bg(self, parent, label: str, variable: tk.StringVar, bg_color: str) -> None:
        row = ttk.Frame(parent, style="Panel2.TFrame")
        row.pack(fill="x", pady=1)
        ttk.Label(row, text=label, style="Muted.TLabel", background=bg_color).pack(side="left")
        ttk.Label(row, textvariable=variable, font=("Segoe UI", 8, "bold"), foreground=TEXT, background=bg_color).pack(side="right")

    def _counter_row(self, parent, label: str, variable: tk.StringVar, color: str) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", padx=10, pady=2)
        ttk.Label(row, text=label, style="Muted.TLabel").pack(side="left")
        ttk.Label(row, textvariable=variable, font=("Segoe UI", 9, "bold"), foreground=color, background=PANEL).pack(side="right")

    def _metric_card(self, parent, column: int, title: str, variable: tk.StringVar) -> None:
        card = ttk.Frame(parent, style="Panel.TFrame")
        card.grid(row=0, column=column, sticky="nsew", padx=3)

        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(8, 2))
        ttk.Label(card, textvariable=variable, style="CardValue.TLabel").pack(anchor="w", padx=10, pady=(0, 8))

    # =========================================================================
    # BACKEND CONNECTION & HEALTH CHECK
    # =========================================================================

    def _start_backend_check(self) -> None:
        """
        Launch background thread to verify or connect to local Flask server.
        """
        thread = threading.Thread(target=self._backend_worker, name="aegis-backend-check", daemon=True)
        thread.start()

    def _backend_worker(self) -> None:
        """
        Background worker thread checking Flask /health endpoint.
        Spawns app.py subprocess if server is unavailable.
        """
        # 1. Check if backend is already running
        try:
            res = requests.get(HEALTH_URL, timeout=1.2)
            if res.ok:
                self._ui_call(self._set_backend_ready, res.json())
                return
        except requests.RequestException:
            pass

        # 2. Try launching app.py if available
        if not APP_FILE.exists():
            self._ui_call(self._set_backend_missing)
            return

        try:
            self.server_process = Popen(
                [sys.executable, str(APP_FILE)],
                cwd=str(PROJECT_DIR),
                creationflags=CREATE_NEW_PROCESS_GROUP,
            )
            self.server_started_by_gui = True
            self._ui_call(self._add_event, "[SYSTEM] Launching local Flask backend process...")
        except OSError as exc:
            self._ui_call(self._set_backend_error, str(exc))
            return

        # 3. Poll for readiness up to 10 seconds
        for _ in range(40):
            if self.closing:
                return
            try:
                res = requests.get(HEALTH_URL, timeout=1.0)
                if res.ok:
                    self._ui_call(self._set_backend_ready, res.json())
                    return
            except requests.RequestException:
                pass
            time.sleep(0.25)

        self._ui_call(self._set_backend_error, "Flask backend did not become ready.")

    def _set_backend_ready(self, data: dict) -> None:
        """
        UI callback when Flask server health check passes.
        """
        self.server_var.set("ONLINE")
        self.ml_var.set("LOADED")
        self.status_var.set("READY")

        self.pill_server.configure(text=" 🟢 SERVER: ONLINE ", style="NodeOk.TLabel")
        self.pill_ml.configure(text=" 🟢 ML: LOADED ", style="NodeOk.TLabel")

        self._add_event(f"[SYSTEM] AegisGuard backend online ({SERVER_URL}). ML Detector loaded.")

    def _set_backend_missing(self) -> None:
        self.server_var.set("MISSING")
        self.ml_var.set("UNAVAILABLE")
        self.status_var.set("ERROR")

        self.pill_server.configure(text=" 🔴 SERVER: MISSING ", style="NodeDanger.TLabel")
        self.pill_ml.configure(text=" 🟡 ML: UNKNOWN ", style="NodeWarn.TLabel")
        self._add_event("[ERROR] app.py not found. Please start local Flask server.")

    def _set_backend_error(self, message: str) -> None:
        self.server_var.set("ERROR")
        self.ml_var.set("UNAVAILABLE")
        self.status_var.set("ERROR")

        self.pill_server.configure(text=" 🔴 SERVER: ERROR ", style="NodeDanger.TLabel")
        self.pill_ml.configure(text=" 🔴 ML: ERROR ", style="NodeDanger.TLabel")
        self._add_event(f"[ERROR] Backend failure: {message}")

    # =========================================================================
    # PRESETS & CONTROL ACTION HANDLERS
    # =========================================================================

    def _normal_preset(self) -> None:
        self.thread_var.set(6)
        self.interval_var.set(10.0)
        self.jitter_var.set(2.5)
        self.duration_var.set(30.0)
        self._add_event("[PRESET] Loaded Normal Traffic profile (6 threads, 10s interval, 30s duration).")

    def _attack_preset(self) -> None:
        self.thread_var.set(5)
        self.interval_var.set(0.0)
        self.jitter_var.set(0.0)
        self.duration_var.set(15.0)
        self._add_event("[PRESET] Loaded Controlled Attack profile (5 threads, 0s interval, 15s duration).")

    # =========================================================================
    # SIMULATION EXECUTION & CONTROL
    # =========================================================================

    def start_simulation(self) -> None:
        """
        Validate settings and launch live SimulationEngine and LiveMLDefenseMonitor.
        """
        if self.running:
            return

        if self.server_var.get() != "ONLINE":
            messagebox.showerror(APP_NAME, "Local AegisGuard server is not online yet.")
            return

        try:
            threads = int(self.thread_var.get())
            interval = float(self.interval_var.get())
            jitter = float(self.jitter_var.get())
            duration = float(self.duration_var.get())
        except (TypeError, ValueError):
            messagebox.showerror(APP_NAME, "Enter valid numeric simulation settings.")
            return

        if threads <= 0 or duration <= 0 or interval < 0 or jitter < 0:
            messagebox.showerror(APP_NAME, "Invalid parameter values provided.")
            return

        if interval > 0 and jitter > interval:
            messagebox.showerror(APP_NAME, "Jitter cannot exceed request interval.")
            return

        # Reset server state prior to simulation session
        try:
            requests.post(RESET_URL, timeout=2.0)
        except requests.RequestException:
            pass

        # Create Engine and Monitor
        self.engine = SimulationEngine(
            f"{SERVER_URL}/",
            num_threads=threads,
            request_interval_seconds=interval,
            request_interval_jitter_seconds=jitter,
            random_seed=int(time.time()) % 100000,
        )

        self.monitor = LiveMLDefenseMonitor(
            self.engine,
            SERVER_URL,
            telemetry_window_seconds=2.0,
            analysis_interval_seconds=2.0,
        )

        self.incident_analyzer.reset()
        self.current_incident = None
        self.previous_risk_score = 0.0

        self.graph_times.clear()
        self.graph_rates.clear()
        self.graph_risks.clear()

        self.start_time = time.monotonic()

        try:
            self.engine.start()
            self.monitor.start()
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Could not start simulation:\n{exc}")
            self.engine = None
            self.monitor = None
            return

        self.running = True
        self.status_var.set("SIMULATION RUNNING")
        self.stop_button.configure(state="normal")

        self.pipeline_labels["node_traffic"].configure(style="NodeActive.TLabel")
        self.pipeline_labels["node_telemetry"].configure(style="NodeActive.TLabel")

        self._add_event(f"[SIM] Simulation started: {threads} threads, interval={interval:.2f}s, duration={duration:.0f}s.")
        self._schedule_auto_stop(duration)

    def _schedule_auto_stop(self, duration: float) -> None:
        """
        Check elapsed simulation duration and auto-stop when duration expires.
        """
        if not self.running or self.start_time is None:
            return

        elapsed = time.monotonic() - self.start_time
        if elapsed >= duration:
            self.stop_simulation(automatic=True)
            return

        self.root.after(400, lambda: self._schedule_auto_stop(duration))

    def stop_simulation(self, *, automatic: bool = False) -> None:
        """
        Stop the simulation engine, telemetry monitor, and update final stats.
        """
        if not self.running:
            return

        self.running = False

        if self.monitor is not None:
            try:
                self.monitor.stop()
            except Exception:
                pass

        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                pass

        snapshot = self.engine.snapshot() if self.engine is not None else None
        if snapshot is not None:
            self.success_var.set(f"{snapshot.success_count:,}")
            self.limited_var.set(f"{snapshot.rate_limited_count:,}")
            self.failed_var.set(f"{snapshot.failed_count:,}")
            self.request_var.set(f"{snapshot.requests_sent:,}")
            self.avg_response_var.set(f"{snapshot.average_response_ms:.2f} ms")

        self.stop_button.configure(state="disabled")
        self.status_var.set("READY")

        self.pipeline_labels["node_traffic"].configure(style="NodeNormal.TLabel")
        self.pipeline_labels["node_telemetry"].configure(style="NodeNormal.TLabel")

        if automatic:
            self._add_event("[SIM] Simulation completed (duration expired).")
        else:
            self._add_event("[SIM] Simulation stopped by operator.")

        self._evaluate_recovery()

    def reset_lab(self) -> None:
        """
        Reset lab environment, server rate limiters, graphs, and incident states.
        """
        if self.running:
            self.stop_simulation()

        try:
            res = requests.post(RESET_URL, timeout=2.0)
            res.raise_for_status()
        except requests.RequestException as exc:
            messagebox.showerror(APP_NAME, f"Lab reset failed:\n{exc}")
            return

        self.engine = None
        self.monitor = None
        self.incident_analyzer.reset()
        self.current_incident = None
        self.previous_risk_score = 0.0

        self.graph_times.clear()
        self.graph_rates.clear()
        self.graph_risks.clear()
        self.event_lines.clear()

        # Reset variables
        self.risk_var.set("0.00")
        self.risk_badge_var.set("LOW")
        self.rps_var.set("0.00 req/s")
        self.clients_var.set("0")
        self.request_var.set("0")
        self.analysis_var.set("0")

        self.success_var.set("0")
        self.limited_var.set("0")
        self.failed_var.set("0")
        self.avg_response_var.set("0.00 ms")

        self.prediction_var.set("NORMAL")
        self.defense_var.set("NORMAL")
        self.action_var.set("NORMAL_RATE_LIMIT")
        self.defense_policy_var.set("5 requests / 30 seconds")

        self.rate_limiter_policy_var.set("NORMAL_RATE_LIMIT")
        self.rate_limiter_limit_var.set("5 requests / 30 seconds")
        self.rate_limiter_restriction_var.set("INACTIVE")

        self.incident_id_var.set("—")
        self.incident_status_var.set("NO ACTIVE INCIDENT")
        self.incident_severity_var.set("—")
        self.incident_summary_var.set("Monitoring is ready. All traffic evaluated via Isolation Forest.")
        self.opened_at_var.set("—")
        self.recovered_at_var.set("—")
        self.lbl_incident_badge.configure(text=" NO ACTIVE INCIDENT ", style="NodeOk.TLabel")

        self.status_var.set("READY")

        self._clear_events()
        self._reset_pipeline_nodes()
        self._update_charts()

        self._add_event("[SYSTEM] Laboratory state and server rate limiters reset.")

    # =========================================================================
    # PERIODIC RUNTIME POLLING
    # =========================================================================

    def _poll_runtime(self) -> None:
        """
        Main Tkinter UI periodic polling loop (~350ms).
        Fetches snapshots from monitor and engine, updates UI widgets and graphs.
        """
        if self.closing:
            return

        try:
            if self.monitor is not None:
                snap = self.monitor.snapshot()
                if snap is not None:
                    self._update_from_snapshot(snap)

            if self.engine is not None:
                sim_snap = self.engine.snapshot()
                self.success_var.set(f"{sim_snap.success_count:,}")
                self.limited_var.set(f"{sim_snap.rate_limited_count:,}")
                self.failed_var.set(f"{sim_snap.failed_count:,}")
                self.request_var.set(f"{sim_snap.requests_sent:,}")
                self.avg_response_var.set(f"{sim_snap.average_response_ms:.2f} ms")

        except Exception as exc:
            self._add_event(f"[ERROR] UI polling error: {exc}")

        self.root.after(350, self._poll_runtime)

    # =========================================================================
    # SNAPSHOT PROCESSING & UI UPDATE
    # =========================================================================

    def _update_from_snapshot(self, snapshot: LiveMLSnapshot) -> None:
        """
        Process LiveMLSnapshot: Update dynamic variables, telemetry feature tab,
        defense pipeline nodes, graphs, and incident analyzer.
        """
        risk = float(snapshot.highest_risk_score)

        # Update dynamic labels
        self.risk_var.set(f"{risk:.2f}")
        self.rps_var.set(f"{snapshot.requests_per_second:.2f} req/s")
        self.clients_var.set(str(snapshot.active_clients))

        if self.monitor is not None:
            self.analysis_var.set(str(self.monitor.analysis_count))

        self.prediction_var.set(snapshot.highest_prediction)
        if snapshot.highest_prediction == "ANOMALY":
            self.lbl_prediction_badge.configure(style="NodeDanger.TLabel")
        else:
            self.lbl_prediction_badge.configure(style="NodeOk.TLabel")

        # Telemetry Feature Tab Variables
        self.tel_rps_var.set(f"{snapshot.requests_per_second:.2f} req/s")
        self.tel_inter_var.set(f"{snapshot.average_inter_request_time:.3f} s")
        self.tel_burst_var.set(f"{snapshot.burst_ratio:.2f}")
        self.tel_ratelimit_var.set(f"{snapshot.rate_limit_ratio * 100:.1f}%")
        self.tel_error_var.set(f"{snapshot.error_ratio * 100:.1f}%")
        self.tel_response_var.set(f"{snapshot.average_response_time_ms:.2f} ms")
        self.tel_clients_var.set(str(snapshot.active_clients))

        # Update Defense Display & Pipeline Nodes
        self._update_defense_display(risk, snapshot)

        # Append to graph queues
        self.graph_times.append(time.strftime("%H:%M:%S"))
        self.graph_rates.append(snapshot.requests_per_second)
        self.graph_risks.append(risk)

        # Update Charts
        self._update_charts()

        # Process Incidents
        self._process_incident(snapshot)

        self.previous_risk_score = risk

    # =========================================================================
    # DEFENSE DISPLAY & PIPELINE NODE UPDATE
    # =========================================================================

    def _update_defense_display(self, risk: float, snapshot: LiveMLSnapshot) -> None:
        """
        Derive defense levels and update architectural pipeline node colors & rate limiter card.
        """
        if risk >= 80.0:
            self.defense_var.set("HIGH_RISK")
            self.action_var.set("TEMPORARY_RESTRICTION")
            self.defense_policy_var.set("1 req / 30s + 20s Restriction")
            self.risk_badge_var.set("HIGH")
            self.lbl_risk_badge.configure(style="NodeDanger.TLabel")

            self.rate_limiter_policy_var.set("TEMPORARY_RESTRICTION")
            self.rate_limiter_limit_var.set("1 request / 30 seconds")
            self.rate_limiter_restriction_var.set("ACTIVE (20s)")

            self.pipeline_labels["node_ml"].configure(style="NodeDanger.TLabel")
            self.pipeline_labels["node_risk"].configure(style="NodeDanger.TLabel")
            self.pipeline_labels["node_defense"].configure(style="NodeDanger.TLabel")
            self.pipeline_labels["node_limiter"].configure(text=" 🗄️ RATE LIMITER \n   1 req / 30s ", style="NodeDanger.TLabel")
        elif risk >= 60.0:
            self.defense_var.set("SUSPICIOUS")
            self.action_var.set("STRICT_RATE_LIMIT")
            self.defense_policy_var.set("2 requests / 30 seconds")
            self.risk_badge_var.set("SUSPICIOUS")
            self.lbl_risk_badge.configure(style="NodeWarn.TLabel")

            self.rate_limiter_policy_var.set("STRICT_RATE_LIMIT")
            self.rate_limiter_limit_var.set("2 requests / 30 seconds")
            self.rate_limiter_restriction_var.set("INACTIVE")

            self.pipeline_labels["node_ml"].configure(style="NodeWarn.TLabel")
            self.pipeline_labels["node_risk"].configure(style="NodeWarn.TLabel")
            self.pipeline_labels["node_defense"].configure(style="NodeWarn.TLabel")
            self.pipeline_labels["node_limiter"].configure(text=" 🗄️ RATE LIMITER \n   2 req / 30s ", style="NodeWarn.TLabel")
        elif risk >= 30.0:
            self.defense_var.set("WATCH")
            self.action_var.set("INCREASED_MONITORING")
            self.defense_policy_var.set("4 requests / 30 seconds")
            self.risk_badge_var.set("WATCH")
            self.lbl_risk_badge.configure(style="NodeWarn.TLabel")

            self.rate_limiter_policy_var.set("INCREASED_MONITORING")
            self.rate_limiter_limit_var.set("4 requests / 30 seconds")
            self.rate_limiter_restriction_var.set("INACTIVE")

            self.pipeline_labels["node_ml"].configure(style="NodeOk.TLabel")
            self.pipeline_labels["node_risk"].configure(style="NodeWarn.TLabel")
            self.pipeline_labels["node_defense"].configure(style="NodeWarn.TLabel")
            self.pipeline_labels["node_limiter"].configure(text=" 🗄️ RATE LIMITER \n   4 req / 30s ", style="NodeWarn.TLabel")
        else:
            self.defense_var.set("NORMAL")
            self.action_var.set("NORMAL_RATE_LIMIT")
            self.defense_policy_var.set("5 requests / 30 seconds")
            self.risk_badge_var.set("LOW")
            self.lbl_risk_badge.configure(style="NodeOk.TLabel")

            self.rate_limiter_policy_var.set("NORMAL_RATE_LIMIT")
            self.rate_limiter_limit_var.set("5 requests / 30 seconds")
            self.rate_limiter_restriction_var.set("INACTIVE")

            self.pipeline_labels["node_ml"].configure(style="NodeOk.TLabel")
            self.pipeline_labels["node_risk"].configure(style="NodeOk.TLabel")
            self.pipeline_labels["node_defense"].configure(style="NodeOk.TLabel")
            self.pipeline_labels["node_limiter"].configure(text=" 🗄️ RATE LIMITER \n   5 req / 30s ", style="NodeOk.TLabel")

        # HTTP Response node update
        if snapshot.rate_limit_ratio > 0:
            self.pipeline_labels["node_http"].configure(text=" HTTP RESPONSE \n     429 ", style="NodeDanger.TLabel")
        else:
            self.pipeline_labels["node_http"].configure(text=" HTTP RESPONSE \n     200 ", style="NodeOk.TLabel")

    def _reset_pipeline_nodes(self) -> None:
        """
        Reset all pipeline nodes to neutral state.
        """
        for key, lbl in self.pipeline_labels.items():
            if key == "node_http":
                lbl.configure(text=" HTTP RESPONSE \n   200 / 429 ", style="NodeNormal.TLabel")
            elif key == "node_limiter":
                lbl.configure(text=" 🗄️ RATE LIMITER \n   5 req / 30s ", style="NodeNormal.TLabel")
            else:
                lbl.configure(style="NodeNormal.TLabel")

    # =========================================================================
    # INCIDENT LIFECYCLE PROCESSING
    # =========================================================================

    def _process_incident(self, snapshot: LiveMLSnapshot) -> None:
        """
        Feed live observations into IncidentAnalyzer and update incident UI.
        Matches opened/recovered timestamps and severity display of reference image.
        """
        risk = float(snapshot.highest_risk_score)

        if risk >= 60.0:
            if self.current_incident is None:
                incident = self.incident_analyzer.analyze(
                    prediction=snapshot.highest_prediction,
                    risk_score=risk,
                    risk_level=snapshot.highest_risk_level,
                    defense_level=snapshot.highest_risk_level,
                    defense_action=self.action_var.get(),
                    request_count=snapshot.request_count,
                    requests_per_second=snapshot.requests_per_second,
                    active_clients=snapshot.active_clients,
                    rate_limit_ratio=snapshot.rate_limit_ratio,
                    error_ratio=snapshot.error_ratio,
                    average_response_time_ms=snapshot.average_response_time_ms,
                )

                if incident is not None:
                    self.current_incident = incident
                    self.incident_id_var.set(incident.incident_id)
                    self.incident_status_var.set("🚨 INCIDENT OPEN")
                    self.incident_summary_var.set(incident.summary)
                    
                    sev = "HIGH" if risk >= 80.0 else "MEDIUM"
                    self.incident_severity_var.set(sev)
                    self.opened_at_var.set(time.strftime("%H:%M:%S"))
                    self.recovered_at_var.set("—")
                    self.lbl_incident_badge.configure(text=" 🚨 INCIDENT OPEN ", style="NodeDanger.TLabel")

                    self._add_event(f"[INCIDENT] {incident.incident_id} opened — Risk={incident.risk_score:.2f}, Severity {sev}.")
        elif self.current_incident is not None and risk < 40.0:
            recovered = self.incident_analyzer.mark_recovered()
            if recovered is not None:
                self.incident_status_var.set("✔ INCIDENT RECOVERED")
                self.incident_summary_var.set(recovered.summary)
                self.recovered_at_var.set(time.strftime("%H:%M:%S"))
                self.lbl_incident_badge.configure(text=" ✔ INCIDENT RECOVERED ", style="NodeOk.TLabel")
                self._add_event(f"[INCIDENT] {recovered.incident_id} recovered. Traffic risk returned to normal.")
                self.current_incident = None

    def _evaluate_recovery(self) -> None:
        """
        Mark active incident recovered upon simulation termination if appropriate.
        """
        if self.current_incident is None:
            return

        recovered = self.incident_analyzer.mark_recovered()
        if recovered is not None:
            self.incident_status_var.set("✔ INCIDENT RECOVERED")
            self.incident_summary_var.set(recovered.summary)
            self.recovered_at_var.set(time.strftime("%H:%M:%S"))
            self.lbl_incident_badge.configure(text=" ✔ INCIDENT RECOVERED ", style="NodeOk.TLabel")
            self._add_event(f"[INCIDENT] {recovered.incident_id} marked recovered post-simulation.")
            self.current_incident = None

    # =========================================================================
    # MATPLOTLIB CHART REDRAW (RESTORED LARGE EXPANSIVE PRESENTATION)
    # =========================================================================

    def _update_charts(self) -> None:
        """
        Redraw Matplotlib dual subplots (REAL-TIME TRAFFIC & ML RISK SCORE).
        Restores large, expansive, uncompressed SOC chart presentation.
        """
        if not hasattr(self, "canvas"):
            return

        # Clear subplots
        self.ax_rate.clear()
        self.ax_risk.clear()

        # Re-configure styling
        for ax in (self.ax_rate, self.ax_risk):
            ax.set_facecolor(PANEL)
            ax.tick_params(colors=MUTED, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(BORDER)
            ax.grid(True, alpha=0.15, color=BORDER, linestyle=":")

        rates = list(self.graph_rates)
        risks = list(self.graph_risks)

        if rates:
            x = list(range(len(rates)))

            # Subplot 1: REAL-TIME TRAFFIC
            self.ax_rate.plot(x, rates, color=CYAN, linewidth=2, label="Requests/sec")
            self.ax_rate.fill_between(x, rates, color=CYAN, alpha=0.18)
            self.ax_rate.set_ylim(0, max(200.0, max(rates) * 1.25))
            self.ax_rate.legend(loc="upper right", facecolor=PANEL, edgecolor=BORDER, labelcolor=TEXT, fontsize=8)

            # Subplot 2: ML RISK SCORE
            latest_risk = risks[-1] if risks else 0.0
            line_color = RED if latest_risk >= 80.0 else (ORANGE if latest_risk >= 60.0 else (AMBER if latest_risk >= 30.0 else GREEN))
            
            self.ax_risk.plot(x, risks, color=line_color, linewidth=2, label="Risk Score")
            self.ax_risk.fill_between(x, risks, color=line_color, alpha=0.15)

            # Clear Threshold Lines (Watch 30, Suspicious 60, High Risk 80)
            self.ax_risk.axhline(80, color=RED, linestyle="--", linewidth=1.0, alpha=0.8, label="High Risk (≥80)")
            self.ax_risk.axhline(60, color=ORANGE, linestyle="--", linewidth=1.0, alpha=0.8, label="Suspicious (≥60)")
            self.ax_risk.axhline(30, color=AMBER, linestyle="--", linewidth=1.0, alpha=0.8, label="Watch (≥30)")
            self.ax_risk.set_ylim(0, 105)
            self.ax_risk.legend(loc="upper right", facecolor=PANEL, edgecolor=BORDER, labelcolor=TEXT, fontsize=8)

        self.ax_rate.set_title("REAL-TIME TRAFFIC  (Request Rate: requests/sec)", color=TEXT, fontsize=8, loc="left", fontweight="bold")
        self.ax_risk.set_title("ML RISK SCORE  (0 – 100)", color=TEXT, fontsize=8, loc="left", fontweight="bold")
        self.ax_risk.set_xlabel("Time (seconds, 2-second windows)", color=MUTED, fontsize=8)

        self.figure.tight_layout(pad=1.4)
        self.canvas.draw_idle()

    # =========================================================================
    # EVENT CONSOLE LOGGING (SOC LOG STREAM WITH CLEAR LOG BUTTON)
    # =========================================================================

    def _add_event(self, message: str) -> None:
        """
        Append timestamped log message to SOC event console.
        """
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.event_lines.append(line)

        if not hasattr(self, "event_text"):
            return

        self.event_text.configure(state="normal")
        self.event_text.delete("1.0", "end")
        self.event_text.insert("end", "\n".join(self.event_lines))
        self.event_text.see("end")
        self.event_text.configure(state="disabled")

    def _clear_events(self) -> None:
        """
        Clear event console. Bound to [ Clear Log ] button.
        """
        self.event_lines.clear()
        if not hasattr(self, "event_text"):
            return

        self.event_text.configure(state="normal")
        self.event_text.delete("1.0", "end")
        self.event_text.configure(state="disabled")

    # =========================================================================
    # THREAD-SAFE UI DISPATCHER
    # =========================================================================

    def _ui_call(self, callback, *args) -> None:
        """
        Thread-safe callback invocation on Tkinter main thread.
        Safeguarded against shutdown race conditions.
        """
        if self.closing:
            return
        try:
            self.root.after(0, callback, *args)
        except Exception:
            pass

    # =========================================================================
    # WINDOW SHUTDOWN CLEANUP
    # =========================================================================

    def _on_close(self) -> None:
        """
        Cleanly shut down simulation, monitor threads, and server subprocess on exit.
        """
        self.closing = True

        if self.running:
            self.stop_simulation()

        if self.server_started_by_gui and self.server_process is not None:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=3)
            except Exception:
                try:
                    self.server_process.kill()
                except Exception:
                    pass

        self.root.destroy()


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

def main() -> None:
    """
    Launch AegisGuard GUI application.
    """
    matplotlib.use("TkAgg")

    root = tb.Window(themename="darkly")
    AegisGuardGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()