"""
interfaz.py — Sistema de Gestión de Rutas Óptimas en Cusco
===========================================================
PyQt5 + QtWebEngineWidgets · Mapa Leaflet interactivo
UNSAAC — Programación III, 2026
Versión 2.0 — Paneles de control configurables por módulo
"""

import sys, os, json, time
_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_DIR, ".."))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QTextEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
    QListWidget, QListWidgetItem, QStackedWidget, QSizePolicy,
    QAbstractItemView, QMessageBox
)
from PyQt5.QtCore  import Qt, QUrl, QObject, pyqtSlot, pyqtSignal
from PyQt5.QtGui   import QFont, QColor, QPalette
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWebChannel import QWebChannel

from datos.grafo_base      import cargar_nodos, construir_grafo, haversine
from algoritmos.ordenacion import (cargar_pedidos, gnome_sort_prioridad,
                                   comb_sot_peso, shell_sort_valor)
from algoritmos.divide_venceras  import procesar_divide_y_venceras
from algoritmos.backtracking     import backtracking_rutas_con_restricciones
from algoritmos.dinamica         import optimizar_carga_mochila
from algoritmos.greedy           import (greedy_pedido_mas_cercano,
                                         greedy_repartidor_mas_cercano)

# ─────────────────────────────────────────────────────────────────
#  PALETA
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
    ("📦", "Ordenamientos",     "Gnome · Comb · Shell",    C["purple"], "O(n²)"),
    ("⚡", "Greedy",             "Vecino más cercano",       C["orange"], "O(n²)"),
    ("🗺", "Divide y Vencerás", "Segmentación geográfica",  C["green"],  "O(n log n)"),
    ("⚖",  "Mochila DP",        "Knapsack 0/1",             C["accent"], "O(n·W)"),
    ("🚧", "Backtracking",      "Restricciones viales",     C["red"],    "O(V!)"),
]
COLORES_ZONA = ["#2ecc71", "#e67e22", "#9b59b6", "#3498db"]

# ─────────────────────────────────────────────────────────────────
#  ESTILOS COMUNES
# ─────────────────────────────────────────────────────────────────
STYLE_COMBO = f"""
    QComboBox {{
        background:{C['bg_card']}; color:{C['text']};
        border:1px solid {C['border']}; border-radius:4px;
        padding:4px 8px; font-size:11px;
    }}
    QComboBox QAbstractItemView {{
        background:{C['bg_card']}; color:{C['text']};
        selection-background-color:{C['bg_panel']};
        border:1px solid {C['border']};
    }}
    QComboBox::drop-down {{ border:none; }}
"""
STYLE_SPIN = f"""
    QSpinBox, QDoubleSpinBox {{
        background:{C['bg_card']}; color:{C['text']};
        border:1px solid {C['border']}; border-radius:4px;
        padding:4px 8px; font-size:11px;
    }}
"""
STYLE_BTN_RUN = lambda color: f"""
    QPushButton {{
        background:{color}; color:#fff;
        border:none; border-radius:5px;
        padding:8px 0; font-size:12px; font-weight:bold;
    }}
    QPushButton:hover {{ background:{color}cc; }}
    QPushButton:pressed {{ background:{color}99; }}
"""
STYLE_BTN_SMALL = f"""
    QPushButton {{
        background:{C['bg_card']}; color:{C['text_sub']};
        border:1px solid {C['border']}; border-radius:4px;
        padding:4px 10px; font-size:10px;
    }}
    QPushButton:hover {{ color:{C['text']}; border-color:{C['accent']}; }}
"""
STYLE_LIST = f"""
    QListWidget {{
        background:{C['bg_card']}; color:{C['text']};
        border:1px solid {C['border']}; border-radius:4px;
        font-size:10px; outline:none;
    }}
    QListWidget::item:selected {{
        background:{C['bg_panel']}; color:{C['accent']};
    }}
    QListWidget::item:hover {{ background:{C['bg_panel']}; }}
"""
STYLE_GROUP = f"""
    QGroupBox {{
        color:{C['text_sub']}; border:1px solid {C['border']};
        border-radius:5px; margin-top:8px; font-size:10px;
        padding-top:6px;
    }}
    QGroupBox::title {{ subcontrol-origin:margin; left:8px; padding:0 4px; }}
"""
STYLE_CHECK = f"""
    QCheckBox {{ color:{C['text']}; font-size:10px; spacing:6px; }}
    QCheckBox::indicator {{
        width:14px; height:14px; border:1px solid {C['border']};
        border-radius:3px; background:{C['bg_card']};
    }}
    QCheckBox::indicator:checked {{ background:{C['accent']}; border-color:{C['accent']}; }}
"""

def lbl(text, color=None, bold=False, size=9, parent=None):
    l = QLabel(text, parent)
    st = f"color:{color or C['text_sub']}; font-size:{size}px;"
    if bold: st += "font-weight:bold;"
    l.setStyleSheet(st)
    return l

def sep_h():
    f = QFrame(); f.setFixedHeight(1)
    f.setStyleSheet(f"background:{C['border']};")
    return f

# ─────────────────────────────────────────────────────────────────
#  BRIDGE Qt ↔ JS
# ─────────────────────────────────────────────────────────────────
class Bridge(QObject):
    nodo_clickeado = pyqtSignal(int)

    def __init__(self, app_ref):
        super().__init__()
        self._app = app_ref

    @pyqtSlot(int)
    def on_nodo_click(self, nodo_id):
        self.nodo_clickeado.emit(nodo_id)

    @pyqtSlot(result=str)
    def get_nodos_json(self):
        return json.dumps(self._app.nodos_datos)

# ─────────────────────────────────────────────────────────────────
#  VENTANA PRINCIPAL
# ─────────────────────────────────────────────────────────────────
class SistemaRutasCusco(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UNSAAC — Sistema de Rutas Óptimas · Cusco  |  Programación III 2026")
        self.resize(1500, 900)
        self.setMinimumSize(1200, 720)
        self._apply_theme()

        self.nodos_datos   = cargar_nodos()
        self.G             = construir_grafo(self.nodos_datos, distancia_maxima=2500)
        self.dicc_nodos    = {n["id"]: n for n in self.nodos_datos}
        self.pedidos       = cargar_pedidos()
        self.modulo_activo = -1

        # Estado de selección desde mapa (para backtracking)
        self._click_mode   = None   # None | "inicio" | "destino" | "bloqueo"
        self._bloqueos_sel = []     # lista de pares [u,v]

        self._build_ui()

        self.bridge  = Bridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.mapa_view.page().setWebChannel(self.channel)
        self.bridge.nodo_clickeado.connect(self._on_nodo_click_from_map)

        self._load_map()

    # ════════════════════════════════════════════════════════════
    #  TEMA
    # ════════════════════════════════════════════════════════════
    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background:{C['bg_app']}; color:{C['text']}; }}
            QScrollBar:vertical {{ background:{C['bg_card']}; width:7px; border-radius:3px; }}
            QScrollBar::handle:vertical {{ background:{C['border']}; border-radius:3px; min-height:20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
            QScrollBar:horizontal {{ background:{C['bg_card']}; height:7px; border-radius:3px; }}
            QScrollBar::handle:horizontal {{ background:{C['border']}; border-radius:3px; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}
            QTextEdit {{ background:{C['bg_app']}; color:{C['green']};
                         border:1px solid {C['border']}; border-radius:4px;
                         font-family:Consolas,monospace; font-size:10px; padding:4px; }}
            QToolTip {{ background:{C['bg_card']}; color:{C['text']};
                        border:1px solid {C['border']}; padding:4px; }}
        """)

    # ════════════════════════════════════════════════════════════
    #  BUILD UI
    # ════════════════════════════════════════════════════════════
    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        vlay = QVBoxLayout(root)
        vlay.setContentsMargins(0,0,0,0); vlay.setSpacing(0)

        vlay.addWidget(self._build_topbar())
        vlay.addWidget(sep_h())

        body = QHBoxLayout(); body.setContentsMargins(0,0,0,0); body.setSpacing(0)

        # Sidebar (módulos)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._vsep())

        # Centro: mapa
        body.addWidget(self._build_center(), stretch=1)
        body.addWidget(self._vsep())

        # Derecha: panel control + logs
        body.addWidget(self._build_right())

        wrap = QWidget(); wrap.setLayout(body)
        vlay.addWidget(wrap, stretch=1)

    def _vsep(self):
        f = QFrame(); f.setFixedWidth(1)
        f.setStyleSheet(f"background:{C['border']};"); return f

    # ── TOPBAR ───────────────────────────────────────────────────
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

        stats = QLabel(f"Nodos: {self.G.number_of_nodes()}  │  "
                       f"Aristas: {self.G.number_of_edges()}  │  "
                       f"Pedidos: {len(self.pedidos)}")
        stats.setFont(QFont("Consolas",9))
        stats.setStyleSheet(f"color:{C['text_sub']};"); lay.addWidget(stats)

        for txt,col in [("v2.0",C["accent"]),("2026",C["green"])]:
            b = QLabel(f"  {txt}  "); b.setFont(QFont("Consolas",9,QFont.Bold))
            b.setStyleSheet(f"background:{col};color:#fff;border-radius:3px;padding:2px 6px;")
            lay.addWidget(b)
        return bar

    # ── SIDEBAR ──────────────────────────────────────────────────
    def _build_sidebar(self):
        side = QFrame(); side.setFixedWidth(240)
        side.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(side); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        lay.addWidget(sep_h())
        hdr = QLabel("  MÓDULOS"); hdr.setFont(QFont("Segoe UI",9,QFont.Bold))
        hdr.setStyleSheet(f"color:{C['text_dim']};padding:16px 20px 8px;"); lay.addWidget(hdr)

        acciones = [
            self._show_panel_ordenamiento,
            self._show_panel_greedy,
            self._show_panel_divide,
            self._show_panel_mochila,
            self._show_panel_backtracking,
        ]
        self.btn_mods = []
        for i, ((ico,nom,sub,col,bigo), cmd) in enumerate(zip(MODULOS, acciones)):
            btn = self._mod_btn(i, ico, nom, sub, col, bigo, cmd)
            lay.addWidget(btn); self.btn_mods.append((btn, col))

        lay.addWidget(sep_h())
        lay.addSpacing(8)

        info_hdr = QLabel("  DOCENTES"); info_hdr.setFont(QFont("Segoe UI",9,QFont.Bold))
        info_hdr.setStyleSheet(f"color:{C['text_dim']};padding:4px 20px;"); lay.addWidget(info_hdr)
        for txt,col2 in [
            ("M.Sc. Hector E. Ugarte R.", C["text"]),
            ("M.Sc. Boris Chullo Llave",  C["text"]),
            ("Entrega: 28 mayo 2026",     C["yellow"]),
        ]:
            l = QLabel(f"  {txt}"); l.setFont(QFont("Segoe UI",8))
            l.setStyleSheet(f"color:{col2};padding:2px 20px;"); lay.addWidget(l)

        lay.addStretch()
        lay.addWidget(sep_h())
        btn_r = QPushButton("↺  Reiniciar mapa")
        btn_r.setStyleSheet(STYLE_BTN_SMALL + "QPushButton{margin:8px 10px;}")
        btn_r.clicked.connect(self._reset_mapa); lay.addWidget(btn_r)
        lay.addSpacing(8)
        return side

    def _mod_btn(self, idx, ico, nom, sub, col, bigo, cmd):
        fr = QFrame(); fr.setFixedHeight(60); fr.setCursor(Qt.PointingHandCursor)
        fr.setStyleSheet(f"background:{C['bg_side']};border:none;")
        lay = QHBoxLayout(fr); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        ind = QFrame(); ind.setFixedWidth(4)
        ind.setStyleSheet(f"background:{C['bg_side']};"); lay.addWidget(ind)

        cnt = QWidget(); cnt.setStyleSheet("background:transparent;")
        clay = QVBoxLayout(cnt); clay.setContentsMargins(12,8,12,8); clay.setSpacing(2)

        r1 = QHBoxLayout(); r1.setContentsMargins(0,0,0,0)
        ln = QLabel(f"{ico}  {nom}"); ln.setFont(QFont("Segoe UI",10,QFont.Bold))
        ln.setStyleSheet(f"color:{C['text']};"); r1.addWidget(ln); r1.addStretch()
        lb = QLabel(bigo); lb.setFont(QFont("Consolas",8))
        lb.setStyleSheet(f"color:{col};"); r1.addWidget(lb)
        clay.addLayout(r1)

        ls = QLabel(sub); ls.setFont(QFont("Segoe UI",8))
        ls.setStyleSheet(f"color:{C['text_sub']};"); clay.addWidget(ls)
        lay.addWidget(cnt, stretch=1)

        fr._ind = ind; fr._col = col; fr._idx = idx

        def _enter(e,f=fr,i=ind,c=col): f.setStyleSheet(f"background:{C['bg_card']};border:none;"); i.setStyleSheet(f"background:{c};")
        def _leave(e,f=fr,i=ind,c=col,n=idx):
            bg = C["bg_panel"] if self.modulo_activo==n else C["bg_side"]
            f.setStyleSheet(f"background:{bg};border:none;")
            i.setStyleSheet(f"background:{c if self.modulo_activo==n else C['bg_side']};")
        def _click(e,n=idx,f=fr,i=ind,c=col,fn=cmd): self._activar_mod(n); fn()

        fr.enterEvent=_enter; fr.leaveEvent=_leave; fr.mousePressEvent=_click
        return fr

    def _activar_mod(self, idx):
        if self.modulo_activo >= 0:
            prev, pc = self.btn_mods[self.modulo_activo]
            prev.setStyleSheet(f"background:{C['bg_side']};border:none;")
            prev._ind.setStyleSheet(f"background:{C['bg_side']};")
        self.modulo_activo = idx
        btn, col = self.btn_mods[idx]
        btn.setStyleSheet(f"background:{C['bg_panel']};border:none;")
        btn._ind.setStyleSheet(f"background:{col};")

    # ── CENTRO (MAPA) ─────────────────────────────────────────────
    def _build_center(self):
        fr = QFrame(); fr.setStyleSheet(f"background:{C['bg_app']};")
        lay = QVBoxLayout(fr); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Título mapa
        bar = QFrame(); bar.setFixedHeight(36)
        bar.setStyleSheet(f"background:{C['bg_panel']};")
        blay = QHBoxLayout(bar); blay.setContentsMargins(12,0,12,0)
        self.lbl_mapa = QLabel("📍  Mapa Interactivo — Cusco (OpenStreetMap)")
        self.lbl_mapa.setFont(QFont("Segoe UI",10,QFont.Bold))
        self.lbl_mapa.setStyleSheet(f"color:{C['text']};"); blay.addWidget(self.lbl_mapa)
        blay.addStretch()
        self.lbl_click_mode = QLabel("")
        self.lbl_click_mode.setFont(QFont("Segoe UI",9))
        self.lbl_click_mode.setStyleSheet(f"color:{C['yellow']};"); blay.addWidget(self.lbl_click_mode)
        bk = QLabel("  Haversine WGS-84 · NetworkX  ")
        bk.setFont(QFont("Consolas",8))
        bk.setStyleSheet(f"background:#0d2818;color:{C['green']};border-radius:3px;padding:2px 6px;")
        blay.addWidget(bk); lay.addWidget(bar); lay.addWidget(sep_h())

        self.mapa_view = QWebEngineView()
        self.mapa_view.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.mapa_view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        lay.addWidget(self.mapa_view, stretch=1)

        # Leyenda
        leg = QFrame(); leg.setFixedHeight(28)
        leg.setStyleSheet(f"background:{C['bg_panel']};")
        llay = QHBoxLayout(leg); llay.setContentsMargins(12,0,12,0); llay.setSpacing(0)
        for sym,col,desc in [("●","#e74c3c"," Nodo"),("●",C["green"]," Inicio"),
                              ("●",C["accent"]," Destino"),("●",C["orange"]," Ruta activa"),
                              ("●","#9b59b6"," Zona 2"),("✖",C["red"]," Bloqueado")]:
            s=QLabel(sym); s.setFont(QFont("Consolas",11)); s.setStyleSheet(f"color:{col};"); llay.addWidget(s)
            d=QLabel(desc); d.setFont(QFont("Segoe UI",8))
            d.setStyleSheet(f"color:{C['text_sub']};padding-right:10px;"); llay.addWidget(d)
        llay.addStretch()
        lay.addWidget(sep_h()); lay.addWidget(leg)
        return fr

    # ── PANEL DERECHO ─────────────────────────────────────────────
    def _build_right(self):
        fr = QFrame(); fr.setFixedWidth(340)
        fr.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(fr); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        lay.addWidget(sep_h())

        # ── Stack de paneles de control por módulo ────────────────
        hdr_ctrl = QLabel("  PANEL DE CONTROL"); hdr_ctrl.setFont(QFont("Segoe UI",9,QFont.Bold))
        hdr_ctrl.setStyleSheet(f"color:{C['text_dim']};padding:12px 16px 6px;"); lay.addWidget(hdr_ctrl)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background:{C['bg_side']};")
        self.stack.addWidget(self._panel_bienvenida())  # 0
        self.stack.addWidget(self._panel_ordenamiento()) # 1
        self.stack.addWidget(self._panel_greedy())       # 2
        self.stack.addWidget(self._panel_divide())       # 3
        self.stack.addWidget(self._panel_mochila())      # 4
        self.stack.addWidget(self._panel_backtracking()) # 5
        lay.addWidget(self.stack)

        lay.addWidget(sep_h())

        # ── Resultados ────────────────────────────────────────────
        hdr_res = QLabel("  RESULTADOS"); hdr_res.setFont(QFont("Segoe UI",9,QFont.Bold))
        hdr_res.setStyleSheet(f"color:{C['text_dim']};padding:8px 16px 4px;"); lay.addWidget(hdr_res)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Consolas",9))
        self.txt_log.setStyleSheet(f"""
            QTextEdit{{background:{C['bg_app']};color:{C['green']};
                       border:1px solid {C['border']};border-radius:4px;
                       padding:6px;margin:4px 10px;}}
        """)
        self.txt_log.setText("Sistema iniciado.\nSelecciona un módulo del panel izquierdo.")
        lay.addWidget(self.txt_log, stretch=1)

        lay.addWidget(sep_h())
        # Resumen grafo
        for txt in [f"  Nodos: {self.G.number_of_nodes()}  │  Aristas: {self.G.number_of_edges()}  │  Pedidos: {len(self.pedidos)}"]:
            l=QLabel(txt); l.setFont(QFont("Consolas",8))
            l.setStyleSheet(f"color:{C['text_dim']};padding:4px 16px;"); lay.addWidget(l)
        lay.addSpacing(4)
        return fr

    # ────────────────────────────────────────────────────────────
    #  PANELES DE CONTROL POR MÓDULO
    # ────────────────────────────────────────────────────────────

    def _panel_bienvenida(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(16,12,16,12)
        l = QLabel("← Selecciona un módulo\npara ver sus opciones.")
        l.setFont(QFont("Segoe UI",10)); l.setStyleSheet(f"color:{C['text_sub']};")
        l.setAlignment(Qt.AlignCenter); lay.addWidget(l); lay.addStretch()
        return w

    # ── PANEL ORDENAMIENTOS ──────────────────────────────────────
    def _panel_ordenamiento(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)

        # Criterio
        grp = QGroupBox("Criterio de ordenación"); grp.setStyleSheet(STYLE_GROUP)
        glay = QVBoxLayout(grp); glay.setSpacing(4)
        self.combo_orden_criterio = QComboBox()
        self.combo_orden_criterio.addItems([
            "Prioridad  (Gnome Sort — O(n²))",
            "Peso kg    (Comb Sort — O(n log²n))",
            "Valor S/.  (Shell Sort — O(n log²n))",
            "Todos (comparar los 3)",
        ])
        self.combo_orden_criterio.setStyleSheet(STYLE_COMBO)
        glay.addWidget(self.combo_orden_criterio)
        lay.addWidget(grp)

        # Nodos a resaltar
        grp2 = QGroupBox("Resaltar en mapa"); grp2.setStyleSheet(STYLE_GROUP)
        glay2 = QVBoxLayout(grp2); glay2.setSpacing(4)
        self.combo_orden_campo = QComboBox()
        self.combo_orden_campo.addItems(["Nodos Origen", "Nodos Destino", "Ambos"])
        self.combo_orden_campo.setStyleSheet(STYLE_COMBO)
        glay2.addWidget(self.combo_orden_campo)
        lay.addWidget(grp2)

        # Búsqueda
        grp3 = QGroupBox("Búsqueda rápida"); grp3.setStyleSheet(STYLE_GROUP)
        glay3 = QVBoxLayout(grp3); glay3.setSpacing(4)
        glay3.addWidget(lbl("Buscar por ID de pedido:"))
        self.spin_buscar_id = QSpinBox()
        self.spin_buscar_id.setRange(1, 25); self.spin_buscar_id.setValue(1)
        self.spin_buscar_id.setStyleSheet(STYLE_SPIN)
        glay3.addWidget(self.spin_buscar_id)
        btn_buscar = QPushButton("🔍  Buscar pedido")
        btn_buscar.setStyleSheet(STYLE_BTN_SMALL)
        btn_buscar.clicked.connect(self._buscar_pedido)
        glay3.addWidget(btn_buscar)
        lay.addWidget(grp3)

        lay.addStretch()
        btn = QPushButton("▶  Ejecutar ordenamiento")
        btn.setStyleSheet(STYLE_BTN_RUN(C["purple"]))
        btn.clicked.connect(self.ejecutar_ordenamiento); lay.addWidget(btn)
        return w

    # ── PANEL GREEDY ─────────────────────────────────────────────
    def _panel_greedy(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)

        grp = QGroupBox("Punto de inicio del repartidor"); grp.setStyleSheet(STYLE_GROUP)
        glay = QVBoxLayout(grp); glay.setSpacing(4)
        glay.addWidget(lbl("Nodo de inicio:"))
        self.combo_greedy_inicio = QComboBox()
        self.combo_greedy_inicio.setStyleSheet(STYLE_COMBO)
        for n in self.nodos_datos:
            self.combo_greedy_inicio.addItem(f"[{n['id']:2}] {n['nombre']}", n["id"])
        glay.addWidget(self.combo_greedy_inicio)
        lay.addWidget(grp)

        grp2 = QGroupBox("Cantidad de pedidos"); grp2.setStyleSheet(STYLE_GROUP)
        glay2 = QVBoxLayout(grp2); glay2.setSpacing(4)
        glay2.addWidget(lbl("Primeros N pedidos a repartir:"))
        self.spin_greedy_n = QSpinBox()
        self.spin_greedy_n.setRange(1, len(self.pedidos))
        self.spin_greedy_n.setValue(8)
        self.spin_greedy_n.setStyleSheet(STYLE_SPIN)
        glay2.addWidget(self.spin_greedy_n)
        lay.addWidget(grp2)

        grp3 = QGroupBox("Pedido urgente (asignación)"); grp3.setStyleSheet(STYLE_GROUP)
        glay3 = QVBoxLayout(grp3); glay3.setSpacing(4)
        glay3.addWidget(lbl("Pedido urgente a asignar:"))
        self.combo_greedy_urgente = QComboBox()
        self.combo_greedy_urgente.setStyleSheet(STYLE_COMBO)
        for p in self.pedidos:
            self.combo_greedy_urgente.addItem(
                f"#{p['id']} {p['cliente']} (P{p['prioridad']})", p["id"])
        glay3.addWidget(self.combo_greedy_urgente)
        lay.addWidget(grp3)

        lay.addStretch()
        btn = QPushButton("▶  Ejecutar Greedy")
        btn.setStyleSheet(STYLE_BTN_RUN(C["orange"]))
        btn.clicked.connect(self.ejecutar_greedy); lay.addWidget(btn)
        return w

    # ── PANEL DIVIDE Y VENCERÁS ──────────────────────────────────
    def _panel_divide(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)

        grp = QGroupBox("Configuración de repartidores"); grp.setStyleSheet(STYLE_GROUP)
        glay = QVBoxLayout(grp); glay.setSpacing(4)
        glay.addWidget(lbl("Número de repartidores (zonas):"))
        self.spin_divide_reps = QSpinBox()
        self.spin_divide_reps.setRange(2, 4); self.spin_divide_reps.setValue(3)
        self.spin_divide_reps.setStyleSheet(STYLE_SPIN)
        glay.addWidget(self.spin_divide_reps)
        glay.addWidget(lbl("Profundidad de división recursiva:"))
        self.spin_divide_prof = QSpinBox()
        self.spin_divide_prof.setRange(1, 3); self.spin_divide_prof.setValue(2)
        self.spin_divide_prof.setStyleSheet(STYLE_SPIN)
        glay.addWidget(self.spin_divide_prof)
        lay.addWidget(grp)

        grp2 = QGroupBox("Visualización"); grp2.setStyleSheet(STYLE_GROUP)
        glay2 = QVBoxLayout(grp2); glay2.setSpacing(4)
        self.chk_divide_ruta = QCheckBox("Mostrar rutas de cada zona")
        self.chk_divide_ruta.setStyleSheet(STYLE_CHECK)
        self.chk_divide_ruta.setChecked(True)
        glay2.addWidget(self.chk_divide_ruta)
        lay.addWidget(grp2)

        lay.addStretch()
        btn = QPushButton("▶  Ejecutar Divide y Vencerás")
        btn.setStyleSheet(STYLE_BTN_RUN(C["green"]))
        btn.clicked.connect(self.ejecutar_divide_venceras); lay.addWidget(btn)
        return w

    # ── PANEL MOCHILA DP ─────────────────────────────────────────
    def _panel_mochila(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)

        grp = QGroupBox("Capacidad del vehículo"); grp.setStyleSheet(STYLE_GROUP)
        glay = QVBoxLayout(grp); glay.setSpacing(4)
        glay.addWidget(lbl("Capacidad máxima (kg):"))
        self.spin_mochila_cap = QDoubleSpinBox()
        self.spin_mochila_cap.setRange(1.0, 100.0)
        self.spin_mochila_cap.setValue(15.0)
        self.spin_mochila_cap.setSingleStep(0.5)
        self.spin_mochila_cap.setSuffix(" kg")
        self.spin_mochila_cap.setStyleSheet(STYLE_SPIN)
        glay.addWidget(self.spin_mochila_cap)
        lay.addWidget(grp)

        grp2 = QGroupBox("Filtrar pedidos por prioridad"); grp2.setStyleSheet(STYLE_GROUP)
        glay2 = QVBoxLayout(grp2); glay2.setSpacing(4)
        self.chk_mochila_p1 = QCheckBox("Prioridad 1 — Urgente")
        self.chk_mochila_p2 = QCheckBox("Prioridad 2 — Normal")
        self.chk_mochila_p3 = QCheckBox("Prioridad 3 — Puede esperar")
        for chk in [self.chk_mochila_p1, self.chk_mochila_p2, self.chk_mochila_p3]:
            chk.setChecked(True); chk.setStyleSheet(STYLE_CHECK)
            glay2.addWidget(chk)
        lay.addWidget(grp2)

        grp3 = QGroupBox("Método DP"); grp3.setStyleSheet(STYLE_GROUP)
        glay3 = QVBoxLayout(grp3)
        self.combo_mochila_met = QComboBox()
        self.combo_mochila_met.addItems(["Tabulación (bottom-up)", "Memoización (top-down)"])
        self.combo_mochila_met.setStyleSheet(STYLE_COMBO)
        glay3.addWidget(self.combo_mochila_met)
        lay.addWidget(grp3)

        lay.addStretch()
        btn = QPushButton("▶  Ejecutar Mochila DP")
        btn.setStyleSheet(STYLE_BTN_RUN(C["accent"]))
        btn.clicked.connect(self.ejecutar_mochila); lay.addWidget(btn)
        return w

    # ── PANEL BACKTRACKING ───────────────────────────────────────
    def _panel_backtracking(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg_side']};")
        lay = QVBoxLayout(w); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)

        grp = QGroupBox("Nodo de origen"); grp.setStyleSheet(STYLE_GROUP)
        glay = QVBoxLayout(grp); glay.setSpacing(4)
        glay.addWidget(lbl("Nodo inicio:"))
        self.combo_bt_inicio = QComboBox()
        self.combo_bt_inicio.setStyleSheet(STYLE_COMBO)
        for n in self.nodos_datos:
            self.combo_bt_inicio.addItem(f"[{n['id']:2}] {n['nombre']}", n["id"])
        self.combo_bt_inicio.setCurrentIndex(2)   # San Blas por defecto
        glay.addWidget(self.combo_bt_inicio)
        lay.addWidget(grp)

        grp2 = QGroupBox("Nodo de destino"); grp2.setStyleSheet(STYLE_GROUP)
        glay2 = QVBoxLayout(grp2); glay2.setSpacing(4)
        glay2.addWidget(lbl("Nodo destino:"))
        self.combo_bt_destino = QComboBox()
        self.combo_bt_destino.setStyleSheet(STYLE_COMBO)
        for n in self.nodos_datos:
            self.combo_bt_destino.addItem(f"[{n['id']:2}] {n['nombre']}", n["id"])
        self.combo_bt_destino.setCurrentIndex(8)  # Wanchaq por defecto
        glay2.addWidget(self.combo_bt_destino)
        lay.addWidget(grp2)

        grp3 = QGroupBox("Calles bloqueadas"); grp3.setStyleSheet(STYLE_GROUP)
        glay3 = QVBoxLayout(grp3); glay3.setSpacing(4)

        glay3.addWidget(lbl("Aristas bloqueadas actualmente:"))
        self.list_bloqueos = QListWidget()
        self.list_bloqueos.setFixedHeight(70)
        self.list_bloqueos.setStyleSheet(STYLE_LIST)
        glay3.addWidget(self.list_bloqueos)

        # Agregar bloqueo manual
        row = QHBoxLayout(); row.setSpacing(4)
        self.combo_blq_n1 = QComboBox(); self.combo_blq_n1.setStyleSheet(STYLE_COMBO)
        self.combo_blq_n2 = QComboBox(); self.combo_blq_n2.setStyleSheet(STYLE_COMBO)
        for n in self.nodos_datos:
            tag = f"[{n['id']}] {n['nombre'][:12]}"
            self.combo_blq_n1.addItem(tag, n["id"])
            self.combo_blq_n2.addItem(tag, n["id"])
        self.combo_blq_n1.setCurrentIndex(0)
        self.combo_blq_n2.setCurrentIndex(2)
        row.addWidget(self.combo_blq_n1, stretch=1)
        lbl_dash = QLabel("↔"); lbl_dash.setStyleSheet(f"color:{C['text_sub']};")
        row.addWidget(lbl_dash)
        row.addWidget(self.combo_blq_n2, stretch=1)
        glay3.addLayout(row)

        row2 = QHBoxLayout(); row2.setSpacing(4)
        btn_add = QPushButton("+ Agregar bloqueo")
        btn_add.setStyleSheet(STYLE_BTN_SMALL)
        btn_add.clicked.connect(self._agregar_bloqueo)
        btn_rem = QPushButton("✕ Quitar selección")
        btn_rem.setStyleSheet(STYLE_BTN_SMALL)
        btn_rem.clicked.connect(self._quitar_bloqueo)
        row2.addWidget(btn_add); row2.addWidget(btn_rem)
        glay3.addLayout(row2)
        lay.addWidget(grp3)

        grp4 = QGroupBox("Límite de rutas"); grp4.setStyleSheet(STYLE_GROUP)
        glay4 = QVBoxLayout(grp4); glay4.setSpacing(4)
        glay4.addWidget(lbl("Máximo de rutas a encontrar:"))
        self.spin_bt_max = QSpinBox()
        self.spin_bt_max.setRange(1,20); self.spin_bt_max.setValue(5)
        self.spin_bt_max.setStyleSheet(STYLE_SPIN)
        glay4.addWidget(self.spin_bt_max)
        lay.addWidget(grp4)

        lay.addStretch()
        btn = QPushButton("▶  Ejecutar Backtracking")
        btn.setStyleSheet(STYLE_BTN_RUN(C["red"]))
        btn.clicked.connect(self.ejecutar_backtracking); lay.addWidget(btn)
        return w

    # ────────────────────────────────────────────────────────────
    #  HELPERS PANEL
    # ────────────────────────────────────────────────────────────
    def _agregar_bloqueo(self):
        n1 = self.combo_blq_n1.currentData()
        n2 = self.combo_blq_n2.currentData()
        if n1 == n2:
            return
        par = sorted([n1, n2])
        if par in self._bloqueos_sel:
            return
        self._bloqueos_sel.append(par)
        nm1 = self.dicc_nodos[par[0]]["nombre"]
        nm2 = self.dicc_nodos[par[1]]["nombre"]
        self.list_bloqueos.addItem(f"[{par[0]}↔{par[1]}] {nm1[:10]}↔{nm2[:10]}")

    def _quitar_bloqueo(self):
        row = self.list_bloqueos.currentRow()
        if row >= 0:
            self.list_bloqueos.takeItem(row)
            self._bloqueos_sel.pop(row)

    def _buscar_pedido(self):
        pid = self.spin_buscar_id.value()
        p = next((x for x in self.pedidos if x["id"] == pid), None)
        if not p:
            self._log(f"Pedido #{pid} no encontrado.")
            return
        no = self.dicc_nodos.get(p["origen"], {})
        nd = self.dicc_nodos.get(p["destino"], {})
        txt  = f"═══ BÚSQUEDA PEDIDO #{pid} ═══\n\n"
        txt += f"Cliente : {p['cliente']}\n"
        txt += f"Prioridad: {p['prioridad']} ({'Urgente' if p['prioridad']==1 else 'Normal' if p['prioridad']==2 else 'Puede esperar'})\n"
        txt += f"Peso    : {p['peso']} kg\n"
        txt += f"Valor   : S/. {p['valor']}\n\n"
        txt += f"Origen  : [{p['origen']}] {no.get('nombre','?')}\n"
        txt += f"Destino : [{p['destino']}] {nd.get('nombre','?')}\n"
        self._log(txt)
        # resaltar en mapa
        ids_js = json.dumps([p["origen"], p["destino"]])
        self._run_js(f"dibujarCamino({ids_js}, '#d29922', 3);")
        self.lbl_mapa.setText(f"📍  Pedido #{pid} — {p['cliente']}: {no.get('nombre','?')} → {nd.get('nombre','?')}")

    # ────────────────────────────────────────────────────────────
    #  CLICK DESDE EL MAPA (Bridge)
    # ────────────────────────────────────────────────────────────
    def _on_nodo_click_from_map(self, nodo_id):
        nd = self.dicc_nodos.get(nodo_id)
        if not nd: return
        if self._click_mode == "inicio_bt":
            idx = next(i for i,n in enumerate(self.nodos_datos) if n["id"]==nodo_id)
            self.combo_bt_inicio.setCurrentIndex(idx)
            self.lbl_click_mode.setText("")
            self._click_mode = None
        elif self._click_mode == "destino_bt":
            idx = next(i for i,n in enumerate(self.nodos_datos) if n["id"]==nodo_id)
            self.combo_bt_destino.setCurrentIndex(idx)
            self.lbl_click_mode.setText("")
            self._click_mode = None
        elif self._click_mode == "inicio_greedy":
            idx = next(i for i,n in enumerate(self.nodos_datos) if n["id"]==nodo_id)
            self.combo_greedy_inicio.setCurrentIndex(idx)
            self.lbl_click_mode.setText("")
            self._click_mode = None

    # ────────────────────────────────────────────────────────────
    #  SHOW PANELS
    # ────────────────────────────────────────────────────────────
    def _show_panel_ordenamiento(self):  self.stack.setCurrentIndex(1)
    def _show_panel_greedy(self):        self.stack.setCurrentIndex(2)
    def _show_panel_divide(self):        self.stack.setCurrentIndex(3)
    def _show_panel_mochila(self):       self.stack.setCurrentIndex(4)
    def _show_panel_backtracking(self):  self.stack.setCurrentIndex(5)

    # ────────────────────────────────────────────────────────────
    #  MAPA LEAFLET
    # ────────────────────────────────────────────────────────────
    def _load_map(self):
        nodos_js  = json.dumps(self.nodos_datos)
        aristas = [{"from":u,"to":v,"peso":round(d["peso"],1)}
                   for u,v,d in self.G.edges(data=True)]
        aristas_js = json.dumps(aristas)

        html = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<style>
  html,body,#map{{margin:0;padding:0;width:100%;height:100%;background:#0d1117;}}
  .nodo-lbl{{
    background:rgba(13,17,23,0.82);color:#e6edf3;
    font:10px 'Segoe UI',sans-serif;
    border:1px solid #30363d;border-radius:3px;padding:1px 5px;white-space:nowrap;
  }}
  .leaflet-popup-content-wrapper{{background:#1c2128;color:#e6edf3;border:1px solid #30363d;border-radius:6px;}}
  .leaflet-popup-tip{{background:#1c2128;}}
</style>
</head><body><div id="map"></div>
<script>
const NODOS   = {nodos_js};
const ARISTAS = {aristas_js};
const ND = {{}};
NODOS.forEach(n => ND[n.id]=n);

const map = L.map('map',{{center:[-13.522,-71.972],zoom:14}});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{
  attribution:'© OpenStreetMap',maxZoom:19
}}).addTo(map);

let layerBase  = L.layerGroup().addTo(map);
let layerRuta  = L.layerGroup().addTo(map);
let layerExtra = L.layerGroup().addTo(map);
let bridge     = null;

new QWebChannel(qt.webChannelTransport, ch => {{
  bridge = ch.objects.bridge;
}});

function mkIcon(color, sz) {{
  sz = sz||10;
  return L.divIcon({{className:'',
    html:`<div style="width:${{sz+4}}px;height:${{sz+4}}px;border-radius:50%;
      background:${{color}};border:2px solid rgba(255,255,255,0.7);
      box-shadow:0 0 6px ${{color}}88;"></div>`,
    iconAnchor:[(sz+4)/2,(sz+4)/2]
  }});
}}

function dibujarBase() {{
  layerBase.clearLayers();
  ARISTAS.forEach(a=>{{
    const n1=ND[a.from],n2=ND[a.to];
    if(!n1||!n2) return;
    L.polyline([[n1.lat,n1.lon],[n2.lat,n2.lon]],
      {{color:'#2d3748',weight:1.5,opacity:0.8}}).addTo(layerBase);
  }});
  NODOS.forEach(n=>{{
    const mk = L.marker([n.lat,n.lon],{{icon:mkIcon('#e74c3c',8)}})
      .bindPopup(`<b>[#${{n.id}}] ${{n.nombre}}</b><br>Zona: ${{n.zona}}`)
      .addTo(layerBase);
    mk.on('click',()=>{{ if(bridge) bridge.on_nodo_click(n.id); }});
    L.marker([n.lat,n.lon],{{
      icon:L.divIcon({{className:'',
        html:`<div class="nodo-lbl">${{n.nombre}}</div>`,
        iconAnchor:[-8,16]}}),interactive:false
    }}).addTo(layerBase);
  }});
}}
dibujarBase();

// ── API Python → JS ──────────────────────────────────────────
function limpiarRuta(){{layerRuta.clearLayers();layerExtra.clearLayers();}}
function limpiarTodo(){{dibujarBase();limpiarRuta();}}

function dibujarCamino(ids,color,w){{
  limpiarRuta();
  if(ids.length>1){{
    const coords=ids.map(id=>[ND[id].lat,ND[id].lon]);
    L.polyline(coords,{{color:color,weight:w||4,opacity:0.95}}).addTo(layerRuta);
  }}
  ids.forEach((id,i)=>{{
    if(!ND[id]) return;
    const col=i===0?'#3fb950':(i===ids.length-1?'#58a6ff':color);
    L.marker([ND[id].lat,ND[id].lon],{{icon:mkIcon(col,12)}})
      .bindPopup(`<b>[${{i+1}}] ${{ND[id].nombre}}</b>`).addTo(layerRuta);
  }});
}}

function marcarBloqueados(pares){{
  pares.forEach(par=>{{
    const n1=ND[par[0]],n2=ND[par[1]];
    if(!n1||!n2) return;
    L.polyline([[n1.lat,n1.lon],[n2.lat,n2.lon]],
      {{color:'#f85149',weight:5,dashArray:'8,5',opacity:1}})
      .bindPopup('⛔ BLOQUEADO').addTo(layerExtra);
    const mx=(n1.lat+n2.lat)/2, my=(n1.lon+n2.lon)/2;
    L.marker([mx,my],{{icon:L.divIcon({{className:'',
      html:`<div style="font-size:16px;">⛔</div>`,
      iconAnchor:[8,8]}}),interactive:false}}).addTo(layerExtra);
  }});
}}

function dibujarZonas(zonas,colores,mostrarRutas){{
  limpiarRuta();
  zonas.forEach((zona,zi)=>{{
    const col=colores[zi%colores.length];
    if(mostrarRutas && zona.length>1){{
      const coords=zona.map(id=>[ND[id].lat,ND[id].lon]);
      L.polyline(coords,{{color:col,weight:2,opacity:0.6,dashArray:'5,4'}}).addTo(layerRuta);
    }}
    zona.forEach((id,ii)=>{{
      if(!ND[id]) return;
      L.circleMarker([ND[id].lat,ND[id].lon],
        {{radius:11,color:col,fillColor:col,fillOpacity:0.55,weight:2}})
        .bindPopup(`<b>${{ND[id].nombre}}</b><br>Zona ${{zi+1}}`).addTo(layerRuta);
    }});
  }});
}}

function dibujarPedidosMochila(ids,color){{
  limpiarRuta();
  ids.forEach((id,i)=>{{
    if(!ND[id]) return;
    L.marker([ND[id].lat,ND[id].lon],{{icon:mkIcon(color,13)}})
      .bindPopup(`<b>${{ND[id].nombre}}</b><br>Pedido seleccionado #${{i+1}}`).addTo(layerRuta);
  }});
}}

function dibujarGreedy(ids,color){{
  limpiarRuta();
  if(ids.length>1){{
    const coords=ids.map(id=>[ND[id].lat,ND[id].lon]);
    L.polyline(coords,{{color:color,weight:3,dashArray:'8,4',opacity:0.9}}).addTo(layerRuta);
  }}
  ids.forEach((id,i)=>{{
    if(!ND[id]) return;
    L.marker([ND[id].lat,ND[id].lon],{{icon:mkIcon(color,11)}})
      .bindPopup(`<b>[${{i+1}}] ${{ND[id].nombre}}</b>`).addTo(layerRuta);
  }});
}}

function dibujarOrdenamiento(ids,color){{
  limpiarRuta();
  ids.forEach((id,i)=>{{
    if(!ND[id]) return;
    L.circleMarker([ND[id].lat,ND[id].lon],
      {{radius:10,color:color,fillColor:color,fillOpacity:0.6,weight:2}})
      .bindPopup(`<b>[${{i+1}}] ${{ND[id].nombre}}</b>`).addTo(layerRuta);
  }});
}}
</script></body></html>"""
        self.mapa_view.setHtml(html, QUrl("about:blank"))

    def _run_js(self, js):
        self.mapa_view.page().runJavaScript(js)

    def _reset_mapa(self):
        self._click_mode = None
        self.lbl_click_mode.setText("")
        self._run_js("limpiarTodo();")
        self.lbl_mapa.setText("📍  Mapa Interactivo — Cusco (OpenStreetMap)")
        self._log("Mapa reiniciado.\nSelecciona un módulo y configura los parámetros.")

    def _log(self, texto):
        self.txt_log.setText(texto)
        self.txt_log.verticalScrollBar().setValue(0)

    # ════════════════════════════════════════════════════════════
    #  EJECUTAR MÓDULOS
    # ════════════════════════════════════════════════════════════

    # ── 1. ORDENAMIENTOS ─────────────────────────────────────────
    def ejecutar_ordenamiento(self):
        criterio = self.combo_orden_criterio.currentIndex()
        campo    = self.combo_orden_campo.currentIndex()
        t0       = time.perf_counter()

        if criterio == 0:
            resultado = gnome_sort_prioridad(self.pedidos)
            metodo, crit_txt, color = "Gnome Sort", "Prioridad", C["purple"]
        elif criterio == 1:
            resultado = comb_sot_peso(self.pedidos)
            metodo, crit_txt, color = "Comb Sort", "Peso (kg)", C["purple"]
        elif criterio == 2:
            resultado = shell_sort_valor(self.pedidos)
            metodo, crit_txt, color = "Shell Sort", "Valor (S/.)", C["purple"]
        else:
            r_p = gnome_sort_prioridad(self.pedidos)
            r_w = comb_sot_peso(self.pedidos)
            r_v = shell_sort_valor(self.pedidos)
            t_ms = round((time.perf_counter()-t0)*1000, 3)
            self.lbl_mapa.setText("📦  Ordenamientos — Comparación de 3 criterios")
            ids = [p["origen"] for p in r_p]
            self._run_js(f"dibujarOrdenamiento({json.dumps(ids)}, '{C['purple']}');")
            txt = "═══ MÓDULO 1: TODOS LOS ORDENAMIENTOS ═══\n\n"
            txt += f"Tiempo total: {t_ms} ms\n\n"
            for título, datos, campo_v in [
                ("GNOME SORT — Prioridad", r_p, "prioridad"),
                ("COMB SORT — Peso",       r_w, "peso"),
                ("SHELL SORT — Valor",     r_v, "valor"),
            ]:
                txt += f"{título}:\n"
                for p in datos[:5]:
                    txt += f"  #{p['id']:<3} {p['cliente']:<14} {campo_v}={p[campo_v]}\n"
                txt += f"  ... ({len(datos)} pedidos)\n\n"
            self._log(txt); return

        t_ms = round((time.perf_counter()-t0)*1000, 3)

        # Nodos a resaltar
        if campo == 0:
            ids = [p["origen"] for p in resultado]
        elif campo == 1:
            ids = [p["destino"] for p in resultado]
        else:
            ids = []
            for p in resultado:
                if p["origen"] not in ids:  ids.append(p["origen"])
                if p["destino"] not in ids: ids.append(p["destino"])

        self.lbl_mapa.setText(f"📦  {metodo} — ordenado por {crit_txt}")
        self._run_js(f"dibujarOrdenamiento({json.dumps(ids)}, '{color}');")

        txt  = f"═══ MÓDULO 1: {metodo.upper()} ═══\n\n"
        txt += f"Criterio  : {crit_txt}\n"
        txt += f"Tiempo    : {t_ms} ms\n"
        txt += f"Pedidos   : {len(resultado)}\n\n"
        txt += f"{'#':<4} {'ID':<4} {'Cliente':<15} {crit_txt}\n"
        txt += "─"*38 + "\n"
        for i, p in enumerate(resultado):
            val = p["prioridad"] if criterio==0 else p["peso"] if criterio==1 else p["valor"]
            txt += f"{i+1:<4} #{p['id']:<4} {p['cliente']:<15} {val}\n"
        self._log(txt)

    # ── 2. GREEDY ────────────────────────────────────────────────
    def ejecutar_greedy(self):
        nodo_id  = self.combo_greedy_inicio.currentData()
        n_peds   = self.spin_greedy_n.value()
        ped_id   = self.combo_greedy_urgente.currentData()

        inicio   = self.dicc_nodos[nodo_id]
        t0       = time.perf_counter()
        ruta     = greedy_pedido_mas_cercano(inicio["lat"], inicio["lon"],
                                              self.pedidos[:n_peds], self.nodos_datos)
        t_ms     = round((time.perf_counter()-t0)*1000, 3)

        ped_urg  = next((p for p in self.pedidos if p["id"]==ped_id), self.pedidos[0])
        repartidores = [
            {"nombre":"Repartidor 1","lat":-13.5170,"lon":-71.9787},
            {"nombre":"Repartidor 2","lat":-13.5300,"lon":-71.9600},
            {"nombre":"Repartidor 3","lat":-13.5250,"lon":-71.9820},
        ]
        rep_asig, dist_rep = greedy_repartidor_mas_cercano(ped_urg, repartidores, self.nodos_datos)

        self.lbl_mapa.setText(f"⚡  Greedy — Inicio: {inicio['nombre']}")
        ids = [nodo_id]
        for p in ruta:
            if p["origen"] not in ids: ids.append(p["origen"])
            if p["destino"] not in ids: ids.append(p["destino"])
        self._run_js(f"dibujarGreedy({json.dumps(ids)}, '{C['orange']}');")

        txt  = "═══ MÓDULO 2: GREEDY ═══\n\n"
        txt += f"Inicio    : [{nodo_id}] {inicio['nombre']}\n"
        txt += f"Pedidos   : {n_peds}\n"
        txt += f"Complejidad: O(n²)\n"
        txt += f"Tiempo    : {t_ms} ms\n\n"
        txt += "RUTA GREEDY (pedido más cercano):\n"
        txt += f"{'#':<4} {'ID':<4} {'Cliente':<14} {'Prior'}\n"
        txt += "─"*34 + "\n"
        for i, p in enumerate(ruta):
            txt += f"{i+1:<4} #{p['id']:<4} {p['cliente']:<14} P{p['prioridad']}\n"
        txt += f"\nASIGNACIÓN URGENTE:\n"
        txt += f"  Pedido  : #{ped_urg['id']} — {ped_urg['cliente']}\n"
        txt += f"  Origen  : {self.dicc_nodos.get(ped_urg['origen'],{}).get('nombre','?')}\n"
        if rep_asig:
            txt += f"  Asignado: {rep_asig['nombre']}\n"
            txt += f"  Distancia: {dist_rep:.1f} m\n"
        self._log(txt)

    # ── 3. DIVIDE Y VENCERÁS ─────────────────────────────────────
    def ejecutar_divide_venceras(self):
        n_reps      = self.spin_divide_reps.value()
        prof        = self.spin_divide_prof.value()
        mostrar_rut = self.chk_divide_ruta.isChecked()

        # Parchear profundidad máxima temporalmente
        from algoritmos import divide_venceras as dv_mod
        orig_prof = None
        resultado = procesar_divide_y_venceras.__wrapped__(self.G, n_reps, prof) \
            if hasattr(procesar_divide_y_venceras, '__wrapped__') \
            else self._procesar_dv(n_reps, prof)

        self.lbl_mapa.setText(f"🗺  Divide y Vencerás — {n_reps} repartidores, profundidad {prof}")
        zonas_js = json.dumps(resultado["zonas"])
        col_js   = json.dumps(COLORES_ZONA)
        self._run_js(f"dibujarZonas({zonas_js},{col_js},{'true' if mostrar_rut else 'false'});")

        txt  = "═══ MÓDULO 3: DIVIDE Y VENCERÁS ═══\n\n"
        txt += f"Repartidores: {n_reps}\n"
        txt += f"Profundidad : {prof}\n"
        txt += f"Zonas gen.  : {resultado['num_zonas']}\n"
        txt += f"Complejidad : {resultado['complejidad']}\n"
        txt += f"Tiempo      : {resultado['tiempo_ms']} ms\n\n"
        nombres_col = ["Verde","Naranja","Violeta","Azul"]
        for rep, datos in resultado["asignaciones"].items():
            nombres = [self.dicc_nodos[uid]["nombre"] for uid in datos["ruta"]]
            col_n   = nombres_col[(rep-1)%len(nombres_col)]
            txt += f"Repartidor {rep} ({col_n}):\n"
            txt += f"  Nodos   : {len(datos['ruta'])}\n"
            txt += f"  Distancia: {datos['distancia_m']} m\n"
            for n in nombres:
                txt += f"  → {n}\n"
            txt += "\n"
        self._log(txt)

    def _procesar_dv(self, n_reps, prof):
        """Llama a procesar_divide_y_venceras con profundidad dinámica."""
        from algoritmos.divide_venceras import (
            dividir_zona, greedy_vecino_mas_cercano, UBICACIONES
        )
        import algoritmos.divide_venceras as dv
        import time
        t0 = time.perf_counter()
        dv.UBICACIONES = {}
        for nid, datos in self.G.nodes(data=True):
            dv.UBICACIONES[nid] = {"lat": datos["lat"], "lon": datos["lon"]}
        todos = list(self.G.nodes())
        zonas = dv.dividir_zona(todos, 0, prof)
        asig_raw = {}
        for iz, zona in enumerate(zonas):
            ir = (iz % n_reps) + 1
            asig_raw.setdefault(ir, [])
            asig_raw[ir].extend(zona)
        asignaciones = {}
        for ir, locs in asig_raw.items():
            if len(locs) < 2:
                asignaciones[ir] = {"ruta": locs, "distancia_m": 0.0}
                continue
            r = dv.greedy_vecino_mas_cercano(locs[0], locs[1:])
            asignaciones[ir] = {"ruta": r["ruta"], "distancia_m": r["distancia_m"]}
        t_ms = round((time.perf_counter()-t0)*1000, 4)
        return {"zonas": zonas, "asignaciones": asignaciones,
                "num_zonas": len(zonas), "num_repartidores": n_reps,
                "tiempo_ms": t_ms,
                "complejidad": "O(n log n) división + O(k²) por zona",
                "algoritmo": "Divide y Vencerás — Segmentación Geográfica"}

    # ── 4. MOCHILA DP ────────────────────────────────────────────
    def ejecutar_mochila(self):
        capacidad = self.spin_mochila_cap.value()
        metodo    = self.combo_mochila_met.currentIndex()

        # Filtrar por prioridad
        prioridades = []
        if self.chk_mochila_p1.isChecked(): prioridades.append(1)
        if self.chk_mochila_p2.isChecked(): prioridades.append(2)
        if self.chk_mochila_p3.isChecked(): prioridades.append(3)
        pedidos_f = [p for p in self.pedidos if p["prioridad"] in prioridades]
        if not pedidos_f:
            self._log("Selecciona al menos un nivel de prioridad."); return

        from algoritmos.dinamica import knapsack_tabulacion, knapsack_memoizacion
        t0 = time.perf_counter()
        if metodo == 0:
            sel, peso, valor = knapsack_tabulacion(pedidos_f, capacidad)
            met_txt = "Tabulación (bottom-up)"
        else:
            sel, peso, valor = knapsack_memoizacion(pedidos_f, capacidad)
            met_txt = "Memoización (top-down)"
        t_ms = round((time.perf_counter()-t0)*1000, 3)

        self.lbl_mapa.setText(f"⚖  Mochila DP ({met_txt}) — S/. {valor}  |  {peso} kg / {capacidad} kg")
        ids_orig = [p["origen"] for p in sel]
        self._run_js(f"dibujarPedidosMochila({json.dumps(ids_orig)}, '{C['accent']}');")

        txt  = f"═══ MÓDULO 4: MOCHILA DP ═══\n\n"
        txt += f"Método    : {met_txt}\n"
        txt += f"Capacidad : {capacidad} kg\n"
        txt += f"Disponibles: {len(pedidos_f)} pedidos\n"
        txt += f"Seleccionados: {len(sel)}\n"
        txt += f"Tiempo    : {t_ms} ms\n\n"
        txt += f"► Valor máximo: S/. {valor}\n"
        txt += f"► Peso cargado: {peso} kg\n\n"
        txt += "PEDIDOS EN EL VEHÍCULO:\n"
        txt += f"{'#':<4} {'ID':<4} {'Cliente':<14} {'Peso':<8} Valor\n"
        txt += "─"*42 + "\n"
        for i, p in enumerate(sel):
            txt += f"{i+1:<4} #{p['id']:<4} {p['cliente']:<14} {p['peso']:<8}kg S/.{p['valor']}\n"
        self._log(txt)

    # ── 5. BACKTRACKING ──────────────────────────────────────────
    def ejecutar_backtracking(self):
        inicio  = self.combo_bt_inicio.currentData()
        destino = self.combo_bt_destino.currentData()
        max_r   = self.spin_bt_max.value()

        if inicio == destino:
            self._log("El nodo de inicio y destino deben ser diferentes."); return

        bloqueadas = [list(b) for b in self._bloqueos_sel]
        resultado  = backtracking_rutas_con_restricciones(
            self.G, inicio=inicio, destino=destino,
            aristas_bloqueadas=bloqueadas, max_rutas=max_r)

        nm_i = self.dicc_nodos[inicio]["nombre"]
        nm_d = self.dicc_nodos[destino]["nombre"]
        self.lbl_mapa.setText(
            f"🚧  Backtracking: {nm_i} → {nm_d}  ({resultado['total_rutas']} rutas)")

        # Limpiar y dibujar bloqueados
        self._run_js("limpiarRuta();")
        if bloqueadas:
            self._run_js(f"marcarBloqueados({json.dumps(bloqueadas)});")

        if resultado.get("mejor_ruta"):
            camino_js = json.dumps(resultado["mejor_ruta"]["camino"])
            self._run_js(f"dibujarCamino({camino_js}, '{C['red']}', 4);")

        txt  = "═══ MÓDULO 5: BACKTRACKING ═══\n\n"
        txt += f"Origen    : [{inicio}] {nm_i}\n"
        txt += f"Destino   : [{destino}] {nm_d}\n"
        txt += f"Bloqueadas: {len(bloqueadas)} aristas\n"
        txt += f"Máx. rutas: {max_r}\n"
        txt += f"Complejidad: O(V!) podado\n"
        txt += f"Nodos eval.: {resultado['nodos_explorados']}\n"
        txt += f"Tiempo    : {resultado['tiempo_ms']} ms\n\n"

        if bloqueadas:
            txt += "⛔ BLOQUEOS:\n"
            for b in bloqueadas:
                nm1 = self.dicc_nodos.get(b[0],{}).get("nombre","?")
                nm2 = self.dicc_nodos.get(b[1],{}).get("nombre","?")
                txt += f"  {nm1} ↔ {nm2}\n"
            txt += "\n"

        if resultado.get("mejor_ruta"):
            txt += f"Rutas encontradas: {resultado['total_rutas']}\n\n"
            txt += "MEJOR RUTA:\n"
            for uid in resultado["mejor_ruta"]["camino"]:
                txt += f"  → {self.dicc_nodos[uid]['nombre']}\n"
            txt += f"\nDistancia: {resultado['mejor_ruta']['distancia_m']} m\n\n"
            txt += "TODAS LAS RUTAS:\n"
            for i, r in enumerate(resultado["rutas"]):
                ns = [self.dicc_nodos[u]["nombre"] for u in r["camino"]]
                txt += f"  {i+1}. {' → '.join(ns)}\n     ({r['distancia_m']} m)\n"
        else:
            txt += "❌ No se encontraron rutas.\nRevisa los bloqueos o cambia origen/destino.\n"
        self._log(txt)


# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Rutas Óptimas Cusco")
    app.setStyle("Fusion")
    win = SistemaRutasCusco()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
