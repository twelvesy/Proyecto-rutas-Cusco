"""
interfaz.py — Sistema de Gestión de Rutas Óptimas en Cusco
===========================================================
PyQt5 + QtWebEngineWidgets · Mapa Leaflet interactivo
UNSAAC — Programación III, 2026
"""

import sys, os, json, time
_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_DIR, ".."))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QGroupBox, QCheckBox, QListWidget, QStackedWidget,
)
from PyQt5.QtCore  import Qt, QUrl, QObject, pyqtSlot, pyqtSignal
from PyQt5.QtGui   import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWebChannel import QWebChannel

from datos.grafo_base      import cargar_nodos, construir_grafo
from algoritmos.ordenacion import (cargar_pedidos, gnome_sort_prioridad,
                                   comb_sot_peso, shell_sort_valor)
from algoritmos.backtracking    import backtracking_rutas_con_restricciones
from algoritmos.greedy          import (greedy_pedido_mas_cercano,
                                        greedy_repartidor_mas_cercano)
from algoritmos.dinamica        import knapsack_tabulacion, knapsack_memoizacion

# ─────────────────────────────────────────────────────────────────
C = {
    "bg_app"  : "#0d1117", "bg_side" : "#161b22",
    "bg_panel": "#1c2128", "bg_card" : "#21262d",
    "border"  : "#30363d", "accent"  : "#58a6ff",
    "green"   : "#3fb950", "yellow"  : "#d29922",
    "red"     : "#f85149", "purple"  : "#bc8cff",
    "orange"  : "#e67e22", "text"    : "#e6edf3",
    "text_sub": "#8b949e", "text_dim": "#484f58",
}
MODULOS = [
    ("📦", "Ordenamientos",      "Gnome · Comb · Shell",   C["purple"], "O(n²)"),
    ("⚡",  "Greedy",             "Vecino más cercano",      C["orange"], "O(n²)"),
    ("🗺",  "Divide y Vencerás", "Segmentación geográfica", C["green"],  "O(n log n)"),
    ("⚖",  "Mochila DP",         "Knapsack 0/1",            C["accent"], "O(n·W)"),
    ("🚧", "Backtracking",       "Restricciones viales",    C["red"],    "O(V!)"),
]
COLORES_ZONA  = ["#2ecc71", "#e67e22", "#9b59b6", "#3498db"]
# Colores para las distintas rutas del backtracking (la mejor siempre es la 1ª = rojo)
COLORES_RUTA  = ["#f85149", "#58a6ff", "#3fb950", "#d29922", "#bc8cff",
                 "#e67e22", "#4ec9b0", "#ff79c6", "#8be9fd", "#ffb86c"]

# ── Estilos reutilizables ─────────────────────────────────────────
STYLE_COMBO = f"""
    QComboBox {{background:{C['bg_card']};color:{C['text']};
        border:1px solid {C['border']};border-radius:4px;padding:4px 8px;font-size:11px;}}
    QComboBox QAbstractItemView {{background:{C['bg_card']};color:{C['text']};
        selection-background-color:{C['bg_panel']};border:1px solid {C['border']};}}
    QComboBox::drop-down {{border:none;}}"""
STYLE_SPIN = f"""
    QSpinBox, QDoubleSpinBox {{background:{C['bg_card']};color:{C['text']};
        border:1px solid {C['border']};border-radius:4px;padding:4px 8px;font-size:11px;}}"""
STYLE_GROUP = f"""
    QGroupBox {{color:{C['text_sub']};border:1px solid {C['border']};
        border-radius:5px;margin-top:8px;font-size:10px;padding-top:6px;}}
    QGroupBox::title {{subcontrol-origin:margin;left:8px;padding:0 4px;}}"""
STYLE_CHECK = f"""
    QCheckBox {{color:{C['text']};font-size:10px;spacing:6px;}}
    QCheckBox::indicator {{width:14px;height:14px;border:1px solid {C['border']};
        border-radius:3px;background:{C['bg_card']};}}
    QCheckBox::indicator:checked {{background:{C['accent']};border-color:{C['accent']};}}"""
STYLE_LIST = f"""
    QListWidget {{background:{C['bg_card']};color:{C['text']};
        border:1px solid {C['border']};border-radius:4px;font-size:10px;outline:none;}}
    QListWidget::item:selected {{background:{C['bg_panel']};color:{C['accent']};}}
    QListWidget::item:hover {{background:{C['bg_panel']};}}"""

def _btn_run(color):
    return (f"QPushButton{{background:{color};color:#fff;border:none;border-radius:5px;"
            f"padding:8px 0;font-size:12px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{color}cc;}}"
            f"QPushButton:pressed{{background:{color}88;}}")
def _btn_sm():
    return (f"QPushButton{{background:{C['bg_card']};color:{C['text_sub']};"
            f"border:1px solid {C['border']};border-radius:4px;padding:4px 10px;font-size:10px;}}"
            f"QPushButton:hover{{color:{C['text']};border-color:{C['accent']};}}")

def _lbl(text, color=None, bold=False, size=9):
    l = QLabel(text)
    st = f"color:{color or C['text_sub']};font-size:{size}px;"
    if bold: st += "font-weight:bold;"
    l.setStyleSheet(st); return l

def _sep():
    f = QFrame(); f.setFixedHeight(1)
    f.setStyleSheet(f"background:{C['border']};"); return f

def _vsep():
    f = QFrame(); f.setFixedWidth(1)
    f.setStyleSheet(f"background:{C['border']};"); return f

# ── Bridge Qt ↔ JS ────────────────────────────────────────────────
class Bridge(QObject):
    nodo_clickeado = pyqtSignal(int)
    def __init__(self, app_ref):
        super().__init__(); self._app = app_ref
    @pyqtSlot(int)
    def on_nodo_click(self, nodo_id):
        self.nodo_clickeado.emit(nodo_id)

# ─────────────────────────────────────────────────────────────────
class SistemaRutasCusco(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UNSAAC — Sistema de Rutas Óptimas · Cusco  |  Programación III 2026")
        self.resize(1500, 900); self.setMinimumSize(1200, 720)
        self._apply_theme()

        self.nodos_datos   = cargar_nodos()
        self.G             = construir_grafo(self.nodos_datos, distancia_maxima=2500)
        self.dicc_nodos    = {n["id"]: n for n in self.nodos_datos}
        self.pedidos       = cargar_pedidos()
        self.modulo_activo = -1
        self._bloqueos_sel = []   # lista de pares [u, v]

        self._build_ui()

        self.bridge  = Bridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.mapa_view.page().setWebChannel(self.channel)
        self.bridge.nodo_clickeado.connect(self._on_nodo_click)
        self._load_map()

    # ── Tema ──────────────────────────────────────────────────────
    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow,QWidget{{background:{C['bg_app']};color:{C['text']};}}
            QScrollBar:vertical{{background:{C['bg_card']};width:7px;border-radius:3px;}}
            QScrollBar::handle:vertical{{background:{C['border']};border-radius:3px;min-height:20px;}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
            QScrollBar:horizontal{{background:{C['bg_card']};height:7px;border-radius:3px;}}
            QScrollBar::handle:horizontal{{background:{C['border']};border-radius:3px;}}
            QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{{width:0;}}
            QTextEdit{{background:{C['bg_app']};color:{C['green']};
                border:1px solid {C['border']};border-radius:4px;
                font-family:Consolas,monospace;font-size:10px;padding:4px;}}
            QToolTip{{background:{C['bg_card']};color:{C['text']};
                border:1px solid {C['border']};padding:4px;}}""")

    # ── Layout raíz ───────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(0,0,0,0); v.setSpacing(0)
        v.addWidget(self._build_topbar()); v.addWidget(_sep())
        body = QHBoxLayout(); body.setContentsMargins(0,0,0,0); body.setSpacing(0)
        body.addWidget(self._build_sidebar()); body.addWidget(_vsep())
        body.addWidget(self._build_center(), stretch=1); body.addWidget(_vsep())
        body.addWidget(self._build_right())
        w = QWidget(); w.setLayout(body); v.addWidget(w, stretch=1)

    # ── Topbar ────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = QFrame(); bar.setFixedHeight(50)
        bar.setStyleSheet(f"background:{C['bg_panel']};")
        lay = QHBoxLayout(bar); lay.setContentsMargins(16,0,16,0)
        ico = QLabel("🗺"); ico.setFont(QFont("Segoe UI",16))
        ico.setStyleSheet(f"color:{C['accent']};"); lay.addWidget(ico)
        t = QLabel("  Sistema de Gestión de Rutas Óptimas — Cusco")
        t.setFont(QFont("Segoe UI",12,QFont.Bold))
        t.setStyleSheet(f"color:{C['text']};"); lay.addWidget(t)
        s = QLabel("  UNSAAC · Programación III · 2026")
        s.setFont(QFont("Segoe UI",8))
        s.setStyleSheet(f"color:{C['text_sub']};"); lay.addWidget(s)
        lay.addStretch()
        st = QLabel(f"Nodos: {self.G.number_of_nodes()}  │  "
                    f"Aristas: {self.G.number_of_edges()}  │  "
                    f"Pedidos: {len(self.pedidos)}")
        st.setFont(QFont("Consolas",9)); st.setStyleSheet(f"color:{C['text_sub']};")
        lay.addWidget(st)
        for tx, col in [("v4.0", C["accent"]), ("2026", C["green"])]:
            b = QLabel(f"  {tx}  "); b.setFont(QFont("Consolas",9,QFont.Bold))
            b.setStyleSheet(f"background:{col};color:#fff;border-radius:3px;padding:2px 6px;")
            lay.addWidget(b)
        return bar

    # ── Sidebar ───────────────────────────────────────────────────
    def _build_sidebar(self):
        side = QFrame(); side.setFixedWidth(240)
        side.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(side); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        lay.addWidget(_sep())
        hdr = QLabel("  MÓDULOS"); hdr.setFont(QFont("Segoe UI",9,QFont.Bold))
        hdr.setStyleSheet(f"color:{C['text_dim']};padding:16px 20px 8px;"); lay.addWidget(hdr)
        cbs = [self._show_ord, self._show_gr, self._show_dv, self._show_mo, self._show_bt]
        self.btn_mods = []
        for i, ((ico,nom,sub,col,bigo), cb) in enumerate(zip(MODULOS, cbs)):
            b = self._mod_btn(i, ico, nom, sub, col, bigo, cb)
            lay.addWidget(b); self.btn_mods.append((b, col))
        lay.addWidget(_sep()); lay.addSpacing(8)
        hdr2 = QLabel("  Alumnos"); hdr2.setFont(QFont("Segoe UI",9,QFont.Bold))
        hdr2.setStyleSheet(f"color:{C['text_dim']};padding:4px 20px;"); lay.addWidget(hdr2)
        for tx, col2 in [("Condori Lima Crhistian", C["text"]),
                          ("Diaz Gutierrez Lizardo", C["text"]),
                          ("Ramos Mamani Yovana",    C["text"])]:
            l = QLabel(f"  {tx}"); l.setFont(QFont("Segoe UI",8))
            l.setStyleSheet(f"color:{col2};padding:2px 20px;"); lay.addWidget(l)
        lay.addStretch(); lay.addWidget(_sep())
        br = QPushButton("↺  Reiniciar mapa"); br.setStyleSheet(_btn_sm()+"QPushButton{margin:8px 10px;}")
        br.clicked.connect(self._reset_mapa); lay.addWidget(br); lay.addSpacing(8)
        return side

    def _mod_btn(self, idx, ico, nom, sub, col, bigo, cmd):
        fr = QFrame(); fr.setFixedHeight(60); fr.setCursor(Qt.PointingHandCursor)
        fr.setStyleSheet(f"background:{C['bg_side']};border:none;")
        lay = QHBoxLayout(fr); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        ind = QFrame(); ind.setFixedWidth(4); ind.setStyleSheet(f"background:{C['bg_side']};")
        lay.addWidget(ind)
        cnt = QWidget(); cnt.setStyleSheet("background:transparent;")
        cl = QVBoxLayout(cnt); cl.setContentsMargins(12,8,12,8); cl.setSpacing(2)
        r1 = QHBoxLayout(); r1.setContentsMargins(0,0,0,0)
        ln = QLabel(f"{ico}  {nom}"); ln.setFont(QFont("Segoe UI",10,QFont.Bold))
        ln.setStyleSheet(f"color:{C['text']};"); r1.addWidget(ln); r1.addStretch()
        lb = QLabel(bigo); lb.setFont(QFont("Consolas",8))
        lb.setStyleSheet(f"color:{col};"); r1.addWidget(lb); cl.addLayout(r1)
        ls = QLabel(sub); ls.setFont(QFont("Segoe UI",8))
        ls.setStyleSheet(f"color:{C['text_sub']};"); cl.addWidget(ls)
        lay.addWidget(cnt, stretch=1)
        fr._ind = ind; fr._col = col; fr._idx = idx
        def _ent(e,f=fr,i=ind,c=col):
            f.setStyleSheet(f"background:{C['bg_card']};border:none;"); i.setStyleSheet(f"background:{c};")
        def _lve(e,f=fr,i=ind,c=col,n=idx):
            bg = C["bg_panel"] if self.modulo_activo==n else C["bg_side"]
            f.setStyleSheet(f"background:{bg};border:none;")
            i.setStyleSheet(f"background:{c if self.modulo_activo==n else C['bg_side']};")
        def _clk(e,n=idx,fn=cmd): self._activar_mod(n); fn()
        fr.enterEvent=_ent; fr.leaveEvent=_lve; fr.mousePressEvent=_clk
        return fr

    def _activar_mod(self, idx):
        if self.modulo_activo >= 0:
            prev, _ = self.btn_mods[self.modulo_activo]
            prev.setStyleSheet(f"background:{C['bg_side']};border:none;")
            prev._ind.setStyleSheet(f"background:{C['bg_side']};")
        self.modulo_activo = idx
        btn, col = self.btn_mods[idx]
        btn.setStyleSheet(f"background:{C['bg_panel']};border:none;")
        btn._ind.setStyleSheet(f"background:{col};")

    # ── Centro: mapa ──────────────────────────────────────────────
    def _build_center(self):
        fr = QFrame(); fr.setStyleSheet(f"background:{C['bg_app']};")
        lay = QVBoxLayout(fr); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        # Barra título
        bar = QFrame(); bar.setFixedHeight(36); bar.setStyleSheet(f"background:{C['bg_panel']};")
        bl = QHBoxLayout(bar); bl.setContentsMargins(12,0,12,0)
        self.lbl_mapa = QLabel("📍  Mapa Interactivo — Cusco (OpenStreetMap)")
        self.lbl_mapa.setFont(QFont("Segoe UI",10,QFont.Bold))
        self.lbl_mapa.setStyleSheet(f"color:{C['text']};"); bl.addWidget(self.lbl_mapa); bl.addStretch()
        bk = QLabel("  Haversine WGS-84 · NetworkX  "); bk.setFont(QFont("Consolas",8))
        bk.setStyleSheet(f"background:#0d2818;color:{C['green']};border-radius:3px;padding:2px 6px;")
        bl.addWidget(bk); lay.addWidget(bar); lay.addWidget(_sep())
        # Mapa
        self.mapa_view = QWebEngineView()
        self.mapa_view.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.mapa_view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        lay.addWidget(self.mapa_view, stretch=1)
        # Leyenda
        leg = QFrame(); leg.setFixedHeight(28); leg.setStyleSheet(f"background:{C['bg_panel']};")
        ll = QHBoxLayout(leg); ll.setContentsMargins(12,0,12,0); ll.setSpacing(0)
        items = [("●","#e74c3c"," Nodo"), ("●",C["green"]," Inicio/Fin"),
                 ("━",C["red"]," ⛔ Bloqueado"), ("━","#58a6ff"," Mejor ruta"),
                 ("━","#aaaaaa"," Ruta alternativa")]
        for sym,col,desc in items:
            s = QLabel(sym); s.setFont(QFont("Consolas",12)); s.setStyleSheet(f"color:{col};"); ll.addWidget(s)
            d = QLabel(desc); d.setFont(QFont("Segoe UI",8))
            d.setStyleSheet(f"color:{C['text_sub']};padding-right:10px;"); ll.addWidget(d)
        ll.addStretch()
        lay.addWidget(_sep()); lay.addWidget(leg)
        return fr

    # ── Panel derecho ─────────────────────────────────────────────
    def _build_right(self):
        fr = QFrame(); fr.setFixedWidth(340); fr.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(fr); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        lay.addWidget(_sep())
        hdr = QLabel("  PANEL DE CONTROL"); hdr.setFont(QFont("Segoe UI",9,QFont.Bold))
        hdr.setStyleSheet(f"color:{C['text_dim']};padding:12px 16px 6px;"); lay.addWidget(hdr)
        self.stack = QStackedWidget(); self.stack.setStyleSheet(f"background:{C['bg_side']};")
        self.stack.addWidget(self._panel_bienvenida())   # 0
        self.stack.addWidget(self._panel_ordenamiento()) # 1
        self.stack.addWidget(self._panel_greedy())       # 2
        self.stack.addWidget(self._panel_divide())       # 3
        self.stack.addWidget(self._panel_mochila())      # 4
        self.stack.addWidget(self._panel_backtracking()) # 5
        lay.addWidget(self.stack)
        lay.addWidget(_sep())
        hdr2 = QLabel("  RESULTADOS"); hdr2.setFont(QFont("Segoe UI",9,QFont.Bold))
        hdr2.setStyleSheet(f"color:{C['text_dim']};padding:8px 16px 4px;"); lay.addWidget(hdr2)
        self.txt_log = QTextEdit(); self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Consolas",9))
        self.txt_log.setStyleSheet(
            f"QTextEdit{{background:{C['bg_app']};color:{C['green']};"
            f"border:1px solid {C['border']};border-radius:4px;padding:6px;margin:4px 10px;}}")
        self.txt_log.setText("Sistema iniciado.\nSelecciona un módulo del panel izquierdo.")
        lay.addWidget(self.txt_log, stretch=1)
        lay.addWidget(_sep())
        lf = QLabel(f"  Nodos: {self.G.number_of_nodes()}  │  "
                    f"Aristas: {self.G.number_of_edges()}  │  Pedidos: {len(self.pedidos)}")
        lf.setFont(QFont("Consolas",8)); lf.setStyleSheet(f"color:{C['text_dim']};padding:4px 16px;")
        lay.addWidget(lf); lay.addSpacing(4)
        return fr

    # ═══════════════════════════════════════════════════════════
    #  PANELES POR MÓDULO
    # ═══════════════════════════════════════════════════════════
    def _panel_bienvenida(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(16,12,16,12)
        l = QLabel("← Selecciona un módulo\npara ver sus opciones.")
        l.setFont(QFont("Segoe UI",10)); l.setStyleSheet(f"color:{C['text_sub']};")
        l.setAlignment(Qt.AlignCenter); lay.addWidget(l); lay.addStretch()
        return w

    def _panel_ordenamiento(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)
        g = QGroupBox("Criterio de ordenación"); g.setStyleSheet(STYLE_GROUP)
        gl = QVBoxLayout(g); gl.setSpacing(4)
        self.combo_ord = QComboBox(); self.combo_ord.setStyleSheet(STYLE_COMBO)
        self.combo_ord.addItems(["Prioridad  (Gnome Sort — O(n²))",
                                  "Peso kg    (Comb Sort — O(n log²n))",
                                  "Valor S/.  (Shell Sort — O(n log²n))",
                                  "Todos (comparar los 3)"])
        gl.addWidget(self.combo_ord); lay.addWidget(g)
        g2 = QGroupBox("Resaltar en mapa"); g2.setStyleSheet(STYLE_GROUP)
        gl2 = QVBoxLayout(g2); gl2.setSpacing(4)
        self.combo_ord_campo = QComboBox(); self.combo_ord_campo.setStyleSheet(STYLE_COMBO)
        self.combo_ord_campo.addItems(["Nodos Origen","Nodos Destino","Ambos"])
        gl2.addWidget(self.combo_ord_campo); lay.addWidget(g2)
        g3 = QGroupBox("Búsqueda rápida por ID"); g3.setStyleSheet(STYLE_GROUP)
        gl3 = QVBoxLayout(g3); gl3.setSpacing(4); gl3.addWidget(_lbl("ID de pedido:"))
        self.spin_bid = QSpinBox(); self.spin_bid.setRange(1,25); self.spin_bid.setValue(1)
        self.spin_bid.setStyleSheet(STYLE_SPIN); gl3.addWidget(self.spin_bid)
        bb = QPushButton("🔍  Buscar pedido"); bb.setStyleSheet(_btn_sm())
        bb.clicked.connect(self._buscar_pedido); gl3.addWidget(bb); lay.addWidget(g3)
        lay.addStretch()
        btn = QPushButton("▶  Ejecutar ordenamiento"); btn.setStyleSheet(_btn_run(C["purple"]))
        btn.clicked.connect(self.run_ordenamiento); lay.addWidget(btn)
        return w

    def _panel_greedy(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)
        g = QGroupBox("Nodo de inicio del repartidor"); g.setStyleSheet(STYLE_GROUP)
        gl = QVBoxLayout(g); gl.setSpacing(4); gl.addWidget(_lbl("Nodo de inicio:"))
        self.combo_gr_inicio = QComboBox(); self.combo_gr_inicio.setStyleSheet(STYLE_COMBO)
        for n in self.nodos_datos: self.combo_gr_inicio.addItem(f"[{n['id']:2}] {n['nombre']}", n["id"])
        gl.addWidget(self.combo_gr_inicio); lay.addWidget(g)
        g2 = QGroupBox("Cantidad de pedidos"); g2.setStyleSheet(STYLE_GROUP)
        gl2 = QVBoxLayout(g2); gl2.setSpacing(4); gl2.addWidget(_lbl("Primeros N pedidos:"))
        self.spin_gr_n = QSpinBox(); self.spin_gr_n.setRange(1,len(self.pedidos))
        self.spin_gr_n.setValue(8); self.spin_gr_n.setStyleSheet(STYLE_SPIN); gl2.addWidget(self.spin_gr_n)
        lay.addWidget(g2)
        g3 = QGroupBox("Pedido urgente (asignación)"); g3.setStyleSheet(STYLE_GROUP)
        gl3 = QVBoxLayout(g3); gl3.setSpacing(4); gl3.addWidget(_lbl("Pedido urgente:"))
        self.combo_gr_urg = QComboBox(); self.combo_gr_urg.setStyleSheet(STYLE_COMBO)
        for p in self.pedidos: self.combo_gr_urg.addItem(f"#{p['id']} {p['cliente']} (P{p['prioridad']})", p["id"])
        gl3.addWidget(self.combo_gr_urg); lay.addWidget(g3)
        lay.addStretch()
        btn = QPushButton("▶  Ejecutar Greedy"); btn.setStyleSheet(_btn_run(C["orange"]))
        btn.clicked.connect(self.run_greedy); lay.addWidget(btn)
        return w

    def _panel_divide(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)
        g = QGroupBox("Configuración"); g.setStyleSheet(STYLE_GROUP)
        gl = QVBoxLayout(g); gl.setSpacing(4)
        gl.addWidget(_lbl("Número de repartidores:"))
        self.spin_dv_reps = QSpinBox(); self.spin_dv_reps.setRange(2,4); self.spin_dv_reps.setValue(3)
        self.spin_dv_reps.setStyleSheet(STYLE_SPIN); gl.addWidget(self.spin_dv_reps)
        gl.addWidget(_lbl("Profundidad recursiva:"))
        self.spin_dv_prof = QSpinBox(); self.spin_dv_prof.setRange(1,3); self.spin_dv_prof.setValue(2)
        self.spin_dv_prof.setStyleSheet(STYLE_SPIN); gl.addWidget(self.spin_dv_prof); lay.addWidget(g)
        g2 = QGroupBox("Visualización"); g2.setStyleSheet(STYLE_GROUP)
        gl2 = QVBoxLayout(g2); gl2.setSpacing(4)
        self.chk_dv_rutas = QCheckBox("Mostrar rutas de cada zona")
        self.chk_dv_rutas.setStyleSheet(STYLE_CHECK); self.chk_dv_rutas.setChecked(True)
        gl2.addWidget(self.chk_dv_rutas); lay.addWidget(g2)
        lay.addStretch()
        btn = QPushButton("▶  Ejecutar Divide y Vencerás"); btn.setStyleSheet(_btn_run(C["green"]))
        btn.clicked.connect(self.run_divide); lay.addWidget(btn)
        return w

    def _panel_mochila(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)
        g = QGroupBox("Capacidad del vehículo"); g.setStyleSheet(STYLE_GROUP)
        gl = QVBoxLayout(g); gl.setSpacing(4); gl.addWidget(_lbl("Capacidad máxima (kg):"))
        self.spin_mo_cap = QDoubleSpinBox(); self.spin_mo_cap.setRange(1.0,100.0)
        self.spin_mo_cap.setValue(15.0); self.spin_mo_cap.setSingleStep(0.5)
        self.spin_mo_cap.setSuffix(" kg"); self.spin_mo_cap.setStyleSheet(STYLE_SPIN)
        gl.addWidget(self.spin_mo_cap); lay.addWidget(g)
        g2 = QGroupBox("Filtrar por prioridad"); g2.setStyleSheet(STYLE_GROUP)
        gl2 = QVBoxLayout(g2); gl2.setSpacing(4)
        self.chk_mo_p1 = QCheckBox("Prioridad 1 — Urgente")
        self.chk_mo_p2 = QCheckBox("Prioridad 2 — Normal")
        self.chk_mo_p3 = QCheckBox("Prioridad 3 — Puede esperar")
        for ch in [self.chk_mo_p1,self.chk_mo_p2,self.chk_mo_p3]:
            ch.setChecked(True); ch.setStyleSheet(STYLE_CHECK); gl2.addWidget(ch)
        lay.addWidget(g2)
        g3 = QGroupBox("Método DP"); g3.setStyleSheet(STYLE_GROUP)
        gl3 = QVBoxLayout(g3)
        self.combo_mo_met = QComboBox(); self.combo_mo_met.setStyleSheet(STYLE_COMBO)
        self.combo_mo_met.addItems(["Tabulación (bottom-up)","Memoización (top-down)"])
        gl3.addWidget(self.combo_mo_met); lay.addWidget(g3)
        lay.addStretch()
        btn = QPushButton("▶  Ejecutar Mochila DP"); btn.setStyleSheet(_btn_run(C["accent"]))
        btn.clicked.connect(self.run_mochila); lay.addWidget(btn)
        return w

    # ── Panel Backtracking: limpio, sin animación ─────────────────
    def _panel_backtracking(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)

        g = QGroupBox("Nodo de origen"); g.setStyleSheet(STYLE_GROUP)
        gl = QVBoxLayout(g); gl.setSpacing(4); gl.addWidget(_lbl("Nodo inicio:"))
        self.combo_bt_ini = QComboBox(); self.combo_bt_ini.setStyleSheet(STYLE_COMBO)
        for n in self.nodos_datos: self.combo_bt_ini.addItem(f"[{n['id']:2}] {n['nombre']}", n["id"])
        self.combo_bt_ini.setCurrentIndex(2)   # San Blas
        gl.addWidget(self.combo_bt_ini); lay.addWidget(g)

        g2 = QGroupBox("Nodo de destino"); g2.setStyleSheet(STYLE_GROUP)
        gl2 = QVBoxLayout(g2); gl2.setSpacing(4); gl2.addWidget(_lbl("Nodo destino:"))
        self.combo_bt_dst = QComboBox(); self.combo_bt_dst.setStyleSheet(STYLE_COMBO)
        for n in self.nodos_datos: self.combo_bt_dst.addItem(f"[{n['id']:2}] {n['nombre']}", n["id"])
        self.combo_bt_dst.setCurrentIndex(8)   # Wanchaq
        gl2.addWidget(self.combo_bt_dst); lay.addWidget(g2)

        # ── Bloqueos ──────────────────────────────────────────────
        g3 = QGroupBox("Calles bloqueadas ⛔"); g3.setStyleSheet(STYLE_GROUP)
        gl3 = QVBoxLayout(g3); gl3.setSpacing(5)
        gl3.addWidget(_lbl("Bloqueos actuales:"))
        self.list_blq = QListWidget(); self.list_blq.setFixedHeight(68)
        self.list_blq.setStyleSheet(STYLE_LIST); gl3.addWidget(self.list_blq)

        # Selector de arista a bloquear
        row = QHBoxLayout(); row.setSpacing(4)
        self.combo_blq1 = QComboBox(); self.combo_blq1.setStyleSheet(STYLE_COMBO)
        self.combo_blq2 = QComboBox(); self.combo_blq2.setStyleSheet(STYLE_COMBO)
        for n in self.nodos_datos:
            tag = f"[{n['id']}] {n['nombre'][:11]}"
            self.combo_blq1.addItem(tag, n["id"])
            self.combo_blq2.addItem(tag, n["id"])
        self.combo_blq2.setCurrentIndex(2)   # San Blas por defecto
        row.addWidget(self.combo_blq1, stretch=1)
        lbl_dash = QLabel("↔"); lbl_dash.setStyleSheet(f"color:{C['text_sub']};")
        row.addWidget(lbl_dash)
        row.addWidget(self.combo_blq2, stretch=1)
        gl3.addLayout(row)

        row2 = QHBoxLayout(); row2.setSpacing(4)
        btn_add = QPushButton("+ Agregar bloqueo"); btn_add.setStyleSheet(_btn_sm())
        btn_add.clicked.connect(self._agregar_bloqueo)
        btn_rm  = QPushButton("✕ Quitar");          btn_rm.setStyleSheet(_btn_sm())
        btn_rm.clicked.connect(self._quitar_bloqueo)
        row2.addWidget(btn_add); row2.addWidget(btn_rm); gl3.addLayout(row2)
        lay.addWidget(g3)

        g4 = QGroupBox("Límite de rutas"); g4.setStyleSheet(STYLE_GROUP)
        gl4 = QVBoxLayout(g4); gl4.setSpacing(4)
        gl4.addWidget(_lbl("Máximo de rutas a encontrar:"))
        self.spin_bt_max = QSpinBox(); self.spin_bt_max.setRange(1,20); self.spin_bt_max.setValue(5)
        self.spin_bt_max.setStyleSheet(STYLE_SPIN); gl4.addWidget(self.spin_bt_max)
        lay.addWidget(g4)

        lay.addStretch()
        btn = QPushButton("▶  Calcular rutas"); btn.setStyleSheet(_btn_run(C["red"]))
        btn.clicked.connect(self.run_backtracking); lay.addWidget(btn)
        return w

    # ═══════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════
    def _agregar_bloqueo(self):
        n1 = self.combo_blq1.currentData(); n2 = self.combo_blq2.currentData()
        if n1 == n2: return
        par = sorted([n1, n2])
        if par in self._bloqueos_sel: return
        self._bloqueos_sel.append(par)
        nm1 = self.dicc_nodos[par[0]]["nombre"]; nm2 = self.dicc_nodos[par[1]]["nombre"]
        self.list_blq.addItem(f"⛔  {nm1[:14]}  ↔  {nm2[:14]}")

    def _quitar_bloqueo(self):
        row = self.list_blq.currentRow()
        if row >= 0: self.list_blq.takeItem(row); self._bloqueos_sel.pop(row)

    def _buscar_pedido(self):
        pid = self.spin_bid.value()
        p = next((x for x in self.pedidos if x["id"]==pid), None)
        if not p: self._log(f"Pedido #{pid} no encontrado."); return
        no = self.dicc_nodos.get(p["origen"],{})
        nd = self.dicc_nodos.get(p["destino"],{})
        txt  = f"═══ BÚSQUEDA #{ pid } ═══\n\n"
        txt += f"Cliente  : {p['cliente']}\n"
        txt += f"Prioridad: {p['prioridad']} ({'Urgente' if p['prioridad']==1 else 'Normal' if p['prioridad']==2 else 'Puede esperar'})\n"
        txt += f"Peso     : {p['peso']} kg\n"
        txt += f"Valor    : S/. {p['valor']}\n\n"
        txt += f"Origen  : [{p['origen']}] {no.get('nombre','?')}\n"
        txt += f"Destino : [{p['destino']}] {nd.get('nombre','?')}\n"
        self._log(txt)
        self._js(f"marcaPedido({json.dumps([p['origen'], p['destino']])});")
        self.lbl_mapa.setText(f"📍  Pedido #{pid} — {no.get('nombre','?')} → {nd.get('nombre','?')}")

    def _on_nodo_click(self, nodo_id): pass   # reservado para uso futuro

    def _show_ord(self): self.stack.setCurrentIndex(1)
    def _show_gr(self):  self.stack.setCurrentIndex(2)
    def _show_dv(self):  self.stack.setCurrentIndex(3)
    def _show_mo(self):  self.stack.setCurrentIndex(4)
    def _show_bt(self):  self.stack.setCurrentIndex(5)

    def _js(self, code): self.mapa_view.page().runJavaScript(code)
    def _log(self, t):   self.txt_log.setText(t); self.txt_log.verticalScrollBar().setValue(0)

    def _reset_mapa(self):
        self._js("limpiarTodo();")
        self.lbl_mapa.setText("📍  Mapa Interactivo — Cusco (OpenStreetMap)")
        self._log("Mapa reiniciado.")

    # ═══════════════════════════════════════════════════════════
    #  MAPA LEAFLET
    # ═══════════════════════════════════════════════════════════
    def _load_map(self):
        nodos_js   = json.dumps(self.nodos_datos)
        aristas_js = json.dumps([{"f":u,"t":v,"p":round(d["peso"],1)}
                                  for u,v,d in self.G.edges(data=True)])
        colores_js = json.dumps(COLORES_RUTA)

        html = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<style>
  html,body,#map{{margin:0;padding:0;width:100%;height:100%;background:#0d1117;}}
  .nlbl{{background:rgba(13,17,23,0.85);color:#e6edf3;font:10px 'Segoe UI',sans-serif;
    border:1px solid #30363d;border-radius:3px;padding:1px 5px;white-space:nowrap;}}
  .leaflet-popup-content-wrapper{{background:#1c2128;color:#e6edf3;
    border:1px solid #30363d;border-radius:6px;font-size:12px;}}
  .leaflet-popup-tip{{background:#1c2128;}}
</style></head><body><div id="map"></div>
<script>
const NODOS={nodos_js}, ARISTAS={aristas_js};
const COLORES_RUTA={colores_js};
const ND={{}};
NODOS.forEach(n=>ND[n.id]=n);

const map=L.map('map',{{center:[-13.522,-71.972],zoom:14}});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{attribution:'© OpenStreetMap',maxZoom:19}}).addTo(map);

let lBase=L.layerGroup().addTo(map);
let lRutas=L.layerGroup().addTo(map);
let lBloqueos=L.layerGroup().addTo(map);

// Bridge
let bridge=null;
new QWebChannel(qt.webChannelTransport,ch=>{{bridge=ch.objects.bridge;}});

// ── Ícono circular ──────────────────────────────────────────────
function mkIcon(color,sz){{
  sz=sz||10;
  return L.divIcon({{className:'',
    html:`<div style="width:${{sz+4}}px;height:${{sz+4}}px;border-radius:50%;
      background:${{color}};border:2.5px solid rgba(255,255,255,0.85);
      box-shadow:0 0 7px ${{color}}99;"></div>`,
    iconAnchor:[(sz+4)/2,(sz+4)/2]
  }});
}}

// ── Grafo base ──────────────────────────────────────────────────
function dibujarBase(){{
  lBase.clearLayers();
  ARISTAS.forEach(a=>{{
    const n1=ND[a.f],n2=ND[a.t];
    if(!n1||!n2) return;
    L.polyline([[n1.lat,n1.lon],[n2.lat,n2.lon]],
      {{color:'#2d3748',weight:1.5,opacity:0.75}}).addTo(lBase);
  }});
  NODOS.forEach(n=>{{
    const mk=L.marker([n.lat,n.lon],{{icon:mkIcon('#e74c3c',8)}})
      .bindPopup(`<b>[#${{n.id}}] ${{n.nombre}}</b><br>Zona: ${{n.zona}}`)
      .addTo(lBase);
    mk.on('click',()=>{{if(bridge)bridge.on_nodo_click(n.id);}});
    L.marker([n.lat,n.lon],{{icon:L.divIcon({{className:'',
      html:`<div class="nlbl">${{n.nombre}}</div>`,iconAnchor:[-8,16]}}),interactive:false
    }}).addTo(lBase);
  }});
}}
dibujarBase();

function limpiarRutas(){{ lRutas.clearLayers(); }}
function limpiarBloqueos(){{ lBloqueos.clearLayers(); }}
function limpiarTodo(){{ dibujarBase(); limpiarRutas(); limpiarBloqueos(); }}

// ── Bloqueos: línea roja gruesa + icono ⛔ ──────────────────────
function dibujarBloqueos(pares){{
  lBloqueos.clearLayers();
  pares.forEach(par=>{{
    const n1=ND[par[0]], n2=ND[par[1]];
    if(!n1||!n2) return;
    // Halo rojo de fondo
    L.polyline([[n1.lat,n1.lon],[n2.lat,n2.lon]],
      {{color:'#f85149',weight:10,opacity:0.25}}).addTo(lBloqueos);
    // Línea discontinua roja
    L.polyline([[n1.lat,n1.lon],[n2.lat,n2.lon]],
      {{color:'#f85149',weight:4,dashArray:'10,7',opacity:1}})
      .bindPopup('<b style="color:#f85149">⛔ CALLE BLOQUEADA</b>')
      .addTo(lBloqueos);
    // Icono central
    const mx=(n1.lat+n2.lat)/2, my=(n1.lon+n2.lon)/2;
    L.marker([mx,my],{{icon:L.divIcon({{className:'',
      html:'<div style="font-size:20px;filter:drop-shadow(0 0 5px #f85149);">⛔</div>',
      iconAnchor:[10,10]}}),interactive:false,zIndexOffset:2000}}).addTo(lBloqueos);
    // Etiqueta "BLOQUEADO" en los extremos
    [n1,n2].forEach(nd=>{{
      L.marker([nd.lat,nd.lon],{{icon:L.divIcon({{className:'',
        html:'<div style="background:#f85149;color:#fff;font-size:9px;font-weight:bold;'
            +'border-radius:3px;padding:1px 4px;white-space:nowrap;">BLOQUEADO</div>',
        iconAnchor:[-4,-16]}}),interactive:false,zIndexOffset:1500}}).addTo(lBloqueos);
    }});
  }});
}}

// ── Todas las rutas del backtracking ───────────────────────────
// rutas: array de {{camino:[ids], distancia_m:float}}
// La primera (índice 0) es la mejor ruta → se dibuja más gruesa y con color 0
function dibujarRutasBT(rutas, bloqueadas){{
  limpiarRutas();
  // Primero redibujar bloqueos para que queden encima de todo
  dibujarBloqueos(bloqueadas);

  // Rutas alternativas (del final al inicio → la mejor queda encima)
  for(let i=rutas.length-1; i>=0; i--){{
    const r=rutas[i];
    const coords=r.camino.map(id=>[ND[id].lat,ND[id].lon]);
    const esMejor=(i===0);
    const col=COLORES_RUTA[i%COLORES_RUTA.length];
    const w=esMejor?5:2.5;
    const op=esMejor?1:0.55;
    const dash=esMejor?null:'6,5';

    L.polyline(coords,{{color:col,weight:w,opacity:op,dashArray:dash}})
      .bindPopup(`<b>Ruta #${{i+1}}</b> ${{esMejor?'✅ MEJOR':''}}<br>${{r.distancia_m}} m`)
      .addTo(lRutas);

    // Nodos de la ruta
    r.camino.forEach((id,ii)=>{{
      if(!ND[id]) return;
      const esExtremo=(ii===0||ii===r.camino.length-1);
      if(!esExtremo && !esMejor) return;  // intermedios solo en mejor ruta
      const ncol = ii===0?'#3fb950':(ii===r.camino.length-1?'#58a6ff':col);
      const sz   = esExtremo?13:9;
      const pop  = ii===0?`<b>INICIO</b><br>${{ND[id].nombre}}`
                 : ii===r.camino.length-1?`<b>DESTINO</b><br>${{ND[id].nombre}}`
                 : ND[id].nombre;
      L.marker([ND[id].lat,ND[id].lon],{{icon:mkIcon(ncol,sz)}})
        .bindPopup(pop).addTo(lRutas);
    }});
  }}

  // Leyenda de colores en el log (no en el mapa)
}}

// ── Búsqueda de pedido (marca origen y destino) ─────────────────
function marcaPedido(ids){{
  limpiarRutas();
  if(ids.length>1){{
    const coords=ids.map(id=>[ND[id].lat,ND[id].lon]);
    L.polyline(coords,{{color:'#d29922',weight:3,opacity:0.9,dashArray:'6,4'}}).addTo(lRutas);
  }}
  ids.forEach((id,i)=>{{
    if(!ND[id]) return;
    const col=i===0?'#3fb950':'#58a6ff';
    L.marker([ND[id].lat,ND[id].lon],{{icon:mkIcon(col,12)}})
      .bindPopup(`<b>${{i===0?'ORIGEN':'DESTINO'}}</b><br>${{ND[id].nombre}}`).addTo(lRutas);
  }});
}}

// ── Otras funciones de módulos ──────────────────────────────────
function dibujarZonas(zonas,colores,mostrarRutas){{
  limpiarRutas();
  zonas.forEach((zona,zi)=>{{
    const col=colores[zi%colores.length];
    if(mostrarRutas&&zona.length>1){{
      const coords=zona.map(id=>[ND[id].lat,ND[id].lon]);
      L.polyline(coords,{{color:col,weight:2,opacity:0.6,dashArray:'5,4'}}).addTo(lRutas);
    }}
    zona.forEach(id=>{{
      if(!ND[id]) return;
      L.circleMarker([ND[id].lat,ND[id].lon],
        {{radius:11,color:col,fillColor:col,fillOpacity:0.55,weight:2}})
        .bindPopup(`<b>${{ND[id].nombre}}</b><br>Zona ${{zi+1}}`).addTo(lRutas);
    }});
  }});
}}
function dibujarMochila(ids,color){{
  limpiarRutas();
  ids.forEach((id,i)=>{{
    if(!ND[id]) return;
    L.marker([ND[id].lat,ND[id].lon],{{icon:mkIcon(color,13)}})
      .bindPopup(`<b>${{ND[id].nombre}}</b><br>Pedido seleccionado ${{i+1}}`).addTo(lRutas);
  }});
}}
function dibujarGreedy(ids,color){{
  limpiarRutas();
  if(ids.length>1){{
    const coords=ids.map(id=>[ND[id].lat,ND[id].lon]);
    L.polyline(coords,{{color:color,weight:3,dashArray:'8,4',opacity:0.9}}).addTo(lRutas);
  }}
  ids.forEach((id,i)=>{{
    if(!ND[id]) return;
    L.marker([ND[id].lat,ND[id].lon],{{icon:mkIcon(color,11)}})
      .bindPopup(`<b>[${{i+1}}] ${{ND[id].nombre}}</b>`).addTo(lRutas);
  }});
}}
function dibujarOrden(ids,color){{
  limpiarRutas();
  ids.forEach((id,i)=>{{
    if(!ND[id]) return;
    L.circleMarker([ND[id].lat,ND[id].lon],
      {{radius:10,color:color,fillColor:color,fillOpacity:0.6,weight:2}})
      .bindPopup(`<b>[${{i+1}}] ${{ND[id].nombre}}</b>`).addTo(lRutas);
  }});
}}
</script></body></html>"""
        self.mapa_view.setHtml(html, QUrl("about:blank"))

    # ═══════════════════════════════════════════════════════════
    #  EJECUTAR MÓDULOS
    # ═══════════════════════════════════════════════════════════
    def run_ordenamiento(self):
        crit  = self.combo_ord.currentIndex()
        campo = self.combo_ord_campo.currentIndex()
        t0 = time.perf_counter()
        if crit==0: res=gnome_sort_prioridad(self.pedidos); met,cv,col="Gnome Sort","prioridad",C["purple"]
        elif crit==1: res=comb_sot_peso(self.pedidos); met,cv,col="Comb Sort","peso",C["purple"]
        elif crit==2: res=shell_sort_valor(self.pedidos); met,cv,col="Shell Sort","valor",C["purple"]
        else:
            r_p=gnome_sort_prioridad(self.pedidos); r_w=comb_sot_peso(self.pedidos); r_v=shell_sort_valor(self.pedidos)
            t_ms=round((time.perf_counter()-t0)*1000,3)
            self.lbl_mapa.setText("📦  Comparación de los 3 ordenamientos")
            self._js(f"dibujarOrden({json.dumps([p['origen'] for p in r_p])}, '{C['purple']}');")
            txt = f"═══ TODOS LOS ORDENAMIENTOS ═══\nTiempo: {t_ms} ms\n\n"
            for tit,dat,c in [("GNOME SORT — Prioridad",r_p,"prioridad"),
                               ("COMB SORT — Peso",r_w,"peso"),("SHELL SORT — Valor",r_v,"valor")]:
                txt += f"{tit}:\n"
                for p in dat[:5]: txt += f"  #{p['id']:<3} {p['cliente']:<14} {c}={p[c]}\n"
                txt += f"  ... ({len(dat)} pedidos)\n\n"
            self._log(txt); return
        t_ms = round((time.perf_counter()-t0)*1000,3)
        if campo==0: ids=[p["origen"] for p in res]
        elif campo==1: ids=[p["destino"] for p in res]
        else:
            ids=[]
            for p in res:
                if p["origen"] not in ids: ids.append(p["origen"])
                if p["destino"] not in ids: ids.append(p["destino"])
        self.lbl_mapa.setText(f"📦  {met} — por {cv}")
        self._js(f"dibujarOrden({json.dumps(ids)}, '{col}');")
        txt = f"═══ {met.upper()} ═══\nCriterio: {cv}\nTiempo: {t_ms} ms\nPedidos: {len(res)}\n\n"
        txt += f"{'#':<4}{'ID':<4}{'Cliente':<15}{cv}\n" + "─"*36 + "\n"
        for i,p in enumerate(res): txt += f"{i+1:<4}#{p['id']:<4}{p['cliente']:<15}{p[cv]}\n"
        self._log(txt)

    def run_greedy(self):
        nid = self.combo_gr_inicio.currentData(); n_p = self.spin_gr_n.value()
        pid = self.combo_gr_urg.currentData(); ini = self.dicc_nodos[nid]
        t0 = time.perf_counter()
        ruta = greedy_pedido_mas_cercano(ini["lat"],ini["lon"],self.pedidos[:n_p],self.nodos_datos)
        t_ms = round((time.perf_counter()-t0)*1000,3)
        ped_u = next((p for p in self.pedidos if p["id"]==pid), self.pedidos[0])
        reps = [{"nombre":"Repartidor 1","lat":-13.5170,"lon":-71.9787},
                {"nombre":"Repartidor 2","lat":-13.5300,"lon":-71.9600},
                {"nombre":"Repartidor 3","lat":-13.5250,"lon":-71.9820}]
        rep, dr = greedy_repartidor_mas_cercano(ped_u, reps, self.nodos_datos)
        self.lbl_mapa.setText(f"⚡  Greedy — Inicio: {ini['nombre']}")
        ids = [nid]
        for p in ruta:
            if p["origen"] not in ids: ids.append(p["origen"])
            if p["destino"] not in ids: ids.append(p["destino"])
        self._js(f"dibujarGreedy({json.dumps(ids)}, '{C['orange']}');")
        txt = f"═══ GREEDY ═══\nInicio: [{nid}] {ini['nombre']}\nPedidos: {n_p}\nTiempo: {t_ms} ms\n\n"
        txt += "RUTA (pedido más cercano):\n" + "─"*34 + "\n"
        for i,p in enumerate(ruta): txt += f"{i+1:<4}#{p['id']:<4}{p['cliente']:<14}P{p['prioridad']}\n"
        txt += f"\nASIGNACIÓN URGENTE:\n  #{ped_u['id']} {ped_u['cliente']}\n"
        if rep: txt += f"  Asignado: {rep['nombre']}  ({dr:.1f} m)\n"
        self._log(txt)

    def run_divide(self):
        n_r = self.spin_dv_reps.value(); prof = self.spin_dv_prof.value()
        mr  = self.chk_dv_rutas.isChecked()
        res = self._procesar_dv(n_r, prof)
        self.lbl_mapa.setText(f"🗺  Divide y Vencerás — {n_r} repartidores, prof. {prof}")
        self._js(f"dibujarZonas({json.dumps(res['zonas'])},{json.dumps(COLORES_ZONA)},{'true' if mr else 'false'});")
        txt = f"═══ DIVIDE Y VENCERÁS ═══\nZonas: {res['num_zonas']}\nTiempo: {res['tiempo_ms']} ms\n\n"
        for rep, d in res["asignaciones"].items():
            nms = [self.dicc_nodos[uid]["nombre"] for uid in d["ruta"]]
            txt += f"Rep. {rep}: {len(d['ruta'])} nodos — {d['distancia_m']} m\n"
            for n in nms: txt += f"  → {n}\n"
            txt += "\n"
        self._log(txt)

    def _procesar_dv(self, n_r, prof):
        import algoritmos.divide_venceras as dv, time as tm
        t0 = tm.perf_counter()
        dv.UBICACIONES = {nid:{"lat":d["lat"],"lon":d["lon"]} for nid,d in self.G.nodes(data=True)}
        zonas = dv.dividir_zona(list(self.G.nodes()), 0, prof)
        asig = {}
        for iz, zona in enumerate(zonas):
            ir = (iz % n_r) + 1; asig.setdefault(ir, []); asig[ir].extend(zona)
        asignaciones = {}
        for ir, locs in asig.items():
            if len(locs) < 2: asignaciones[ir] = {"ruta":locs,"distancia_m":0.0}; continue
            r = dv.greedy_vecino_mas_cercano(locs[0], locs[1:])
            asignaciones[ir] = {"ruta":r["ruta"],"distancia_m":r["distancia_m"]}
        return {"zonas":zonas,"asignaciones":asignaciones,"num_zonas":len(zonas),
                "num_repartidores":n_r,"tiempo_ms":round((tm.perf_counter()-t0)*1000,4),
                "complejidad":"O(n log n) + O(k²)"}

    def run_mochila(self):
        cap = self.spin_mo_cap.value(); met = self.combo_mo_met.currentIndex()
        pris = [i+1 for i,c in enumerate([self.chk_mo_p1,self.chk_mo_p2,self.chk_mo_p3]) if c.isChecked()]
        peds = [p for p in self.pedidos if p["prioridad"] in pris]
        if not peds: self._log("Selecciona al menos una prioridad."); return
        t0 = time.perf_counter()
        if met==0: sel,peso,val = knapsack_tabulacion(peds, cap); mt="Tabulación"
        else:      sel,peso,val = knapsack_memoizacion(peds, cap); mt="Memoización"
        t_ms = round((time.perf_counter()-t0)*1000,3)
        self.lbl_mapa.setText(f"⚖  Mochila DP ({mt}) — S/.{val}  |  {peso}/{cap} kg")
        self._js(f"dibujarMochila({json.dumps([p['origen'] for p in sel])}, '{C['accent']}');")
        txt = f"═══ MOCHILA DP ({mt}) ═══\nCapacidad: {cap} kg\nDisponibles: {len(peds)}\n"
        txt += f"Seleccionados: {len(sel)}\nTiempo: {t_ms} ms\n\n► Valor: S/.{val}\n► Peso: {peso} kg\n\n"
        txt += "PEDIDOS:\n" + "─"*40 + "\n"
        for i,p in enumerate(sel): txt += f"{i+1:<4}#{p['id']:<4}{p['cliente']:<14}{p['peso']}kg  S/.{p['valor']}\n"
        self._log(txt)

    # ── Backtracking ──────────────────────────────────────────────
    def run_backtracking(self):
        inicio  = self.combo_bt_ini.currentData()
        destino = self.combo_bt_dst.currentData()
        max_r   = self.spin_bt_max.value()
        if inicio == destino:
            self._log("El nodo de inicio y destino deben ser distintos."); return

        bloqueadas = [list(b) for b in self._bloqueos_sel]
        nm_i = self.dicc_nodos[inicio]["nombre"]
        nm_d = self.dicc_nodos[destino]["nombre"]

        # 1) Dibujar bloqueos inmediatamente
        self._js(f"limpiarRutas(); dibujarBloqueos({json.dumps(bloqueadas)});")

        # 2) Calcular rutas
        t0 = time.perf_counter()
        res = backtracking_rutas_con_restricciones(
            self.G, inicio=inicio, destino=destino,
            aristas_bloqueadas=bloqueadas, max_rutas=max_r)
        t_ms = round((time.perf_counter()-t0)*1000,3)

        # 3) Pasar TODAS las rutas al mapa + los bloqueos para redibujarlos encima
        rutas_js    = json.dumps([{"camino": r["camino"], "distancia_m": r["distancia_m"]}
                                   for r in res["rutas"]])
        bloq_js     = json.dumps(bloqueadas)
        self._js(f"dibujarRutasBT({rutas_js}, {bloq_js});")

        # 4) Actualizar título
        self.lbl_mapa.setText(
            f"🚧  Backtracking: {nm_i} → {nm_d}  "
            f"({res['total_rutas']} rutas  |  {len(bloqueadas)} bloqueos)")

        # 5) Log de resultados
        txt  = "═══ BACKTRACKING ═══\n\n"
        txt += f"Origen    : [{inicio}] {nm_i}\n"
        txt += f"Destino   : [{destino}] {nm_d}\n"
        txt += f"Bloqueadas: {len(bloqueadas)} aristas\n"
        txt += f"Rutas enc.: {res['total_rutas']}\n"
        txt += f"Nodos eval: {res['nodos_explorados']}\n"
        txt += f"Tiempo    : {t_ms} ms\n"

        if bloqueadas:
            txt += "\n⛔ BLOQUEOS:\n"
            for b in bloqueadas:
                n1 = self.dicc_nodos.get(b[0],{}).get("nombre","?")
                n2 = self.dicc_nodos.get(b[1],{}).get("nombre","?")
                txt += f"  {n1}  ↔  {n2}\n"

        if res["rutas"]:
            txt += "\n"
            for i, r in enumerate(res["rutas"]):
                es_mejor = (i == 0)
                nms = [self.dicc_nodos[u]["nombre"] for u in r["camino"]]
                col_nombre = ["🔴","🔵","🟢","🟡","🟣","🟠"][i % 6]
                txt += f"{col_nombre} Ruta {i+1}{'  ← MEJOR' if es_mejor else ''}:\n"
                txt += "  " + " → ".join(nms) + "\n"
                txt += f"  Distancia: {r['distancia_m']} m\n\n"
        else:
            txt += "\n❌ Sin rutas disponibles.\nRevisa los bloqueos o cambia nodos.\n"
        self._log(txt)


# ─────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Rutas Óptimas Cusco")
    app.setStyle("Fusion")
    win = SistemaRutasCusco(); win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
