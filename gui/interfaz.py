"""
gui/interfaz.py
===============
Interfaz principal del Sistema de Gestión de Rutas Óptimas — Cusco
UNSAAC · Programación III · 2026
 
Tecnología de mapa: Folium (Leaflet.js / OpenStreetMap) renderizado
dentro de un panel tkinter mediante tkinterweb o webbrowser externo.
 
Layout:
  ┌────────────────────────────────────────────────┐
  │  TOPBAR                                        │
  ├─────────────┬──────────────────────────────────┤
  │  PANEL IZQ  │   MAPA FOLIUM (HTML interactivo) │
  │  • Módulos  │                                  │
  │  • Params   │                                  │
  │  • Log/Big-O│                                  │
  └─────────────┴──────────────────────────────────┘
"""
 
import tkinter as tk
from tkinter import ttk, font as tkFont
import os
import sys
import webbrowser
import tempfile
import time
import json
 
# ── Ajuste de path para importar módulos hermanos ──────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
 
from datos.grafo_base import cargar_nodos, construir_grafo
from algoritmos.ordenacion import cargar_pedidos, gnome_sort_prioridad, comb_sot_peso, shell_sort_valor
from algoritmos.divide_venceras import procesar_divide_y_venceras
from algoritmos.backtracking import backtracking_rutas_con_restricciones
from algoritmos.dinamica import optimizar_carga_mochila
from algoritmos.greedy import greedy_pedido_mas_cercano
 
# ── Intentar importar folium ────────────────────────────────────────────────
try:
    import folium
    from folium.plugins import MiniMap, Fullscreen
    FOLIUM_OK = True
except ImportError:
    FOLIUM_OK = False
 
# ── Intentar importar tkinterweb para mapa embebido ────────────────────────
try:
    from tkinterweb import HtmlFrame
    TKWEB_OK = True
except ImportError:
    TKWEB_OK = False
 
 
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                       PALETA DE COLORES                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝
C = {
    "bg":       "#0d1117",
    "surface":  "#161b22",
    "surface2": "#1f2937",
    "border":   "#30363d",
    "text":     "#e6edf3",
    "muted":    "#7d8590",
    "accent":   "#f0883e",
    "green":    "#3fb950",
    "blue":     "#58a6ff",
    "purple":   "#bc8cff",
    "red":      "#f85149",
    "yellow":   "#d29922",
}
 
ZONE_COLORS   = ["#3fb950", "#58a6ff", "#bc8cff", "#f0883e", "#d29922"]
FOLIUM_COLORS = ["green",   "blue",   "purple",  "orange",  "darkred"]
 
 
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    GENERADOR DE MAPAS FOLIUM                            ║
# ╚══════════════════════════════════════════════════════════════════════════╝
class MapaFolium:
    """Genera mapas HTML con Folium y los devuelve como ruta de archivo."""
 
    CENTRO_CUSCO = [-13.5200, -71.9720]
    ZOOM         = 14
 
    def __init__(self, nodos_datos, grafo):
        self.nodos_datos = nodos_datos
        self.grafo       = grafo
        self.dicc        = {n["id"]: n for n in nodos_datos}
 
    # ── Mapa base (nodos + aristas) ─────────────────────────────────────
    def _base(self, tiles="CartoDB dark_matter"):
        m = folium.Map(
            location=self.CENTRO_CUSCO,
            zoom_start=self.ZOOM,
            tiles=tiles,
            attr="© CARTO · © OpenStreetMap",
        )
        Fullscreen(position="topright").add_to(m)
        MiniMap(toggle_display=True).add_to(m)
        return m
 
    def _aristas(self, m, color="#30363d", weight=1.5, opacity=0.5):
        for u, v in self.grafo.edges():
            n1, n2 = self.dicc[u], self.dicc[v]
            folium.PolyLine(
                [[n1["lat"], n1["lon"]], [n2["lat"], n2["lon"]]],
                color=color, weight=weight, opacity=opacity,
            ).add_to(m)
 
    def _nodos_base(self, m, color="#f0883e", radius=7):
        for n in self.nodos_datos:
            folium.CircleMarker(
                location=[n["lat"], n["lon"]],
                radius=radius,
                color="white",
                weight=1.5,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                tooltip=f"{n['id']}: {n['nombre']} ({n['zona']})",
                popup=folium.Popup(
                    f"<b>{n['nombre']}</b><br>"
                    f"ID: {n['id']} · Zona: {n['zona']}<br>"
                    f"Lat: {n['lat']:.5f}<br>"
                    f"Lon: {n['lon']:.5f}<br>"
                    f"Conexiones: {self.grafo.degree(n['id'])}",
                    max_width=200,
                ),
            ).add_to(m)
        return m
 
    def generar_base(self):
        m = self._base()
        self._aristas(m)
        self._nodos_base(m)
        return self._guardar(m)
 
    def generar_ordenacion(self, pedidos_ordenados, criterio, top=5):
        m = self._base()
        self._aristas(m)
        self._nodos_base(m, color="#2a3540", radius=5)
        colores = FOLIUM_COLORS[:top]
        for i, p in enumerate(pedidos_ordenados[:top]):
            no = self.dicc[p["origen"]]
            nd = self.dicc[p["destino"]]
            col = colores[i % len(colores)]
            folium.CircleMarker(
                [no["lat"], no["lon"]], radius=11,
                color="white", weight=2, fill=True,
                fill_color=ZONE_COLORS[i % len(ZONE_COLORS)], fill_opacity=1,
                tooltip=f"#{p['id']} {p['cliente']} | {criterio}={p[criterio]}",
                popup=folium.Popup(
                    f"<b>#{p['id']} {p['cliente']}</b><br>"
                    f"Criterio [{criterio}]: <b>{p[criterio]}</b><br>"
                    f"Peso: {p['peso']} kg · Valor: S/.{p['valor']}<br>"
                    f"Prioridad: {p['prioridad']}",
                    max_width=220,
                ),
            ).add_to(m)
            folium.CircleMarker(
                [nd["lat"], nd["lon"]], radius=7,
                color="white", weight=1.5, fill=True,
                fill_color=ZONE_COLORS[i % len(ZONE_COLORS)], fill_opacity=0.6,
                tooltip=f"Destino: {nd['nombre']}",
            ).add_to(m)
            folium.PolyLine(
                [[no["lat"], no["lon"]], [nd["lat"], nd["lon"]]],
                color=ZONE_COLORS[i % len(ZONE_COLORS)],
                weight=2.5, opacity=0.7, dash_array="8 5",
            ).add_to(m)
        return self._guardar(m)
 
    def generar_greedy(self, ruta_greedy, pos_inicial):
        m = self._base()
        self._aristas(m)
        self._nodos_base(m, color="#2a3540", radius=5)
        prev = pos_inicial
        for i, paso in enumerate(ruta_greedy):
            no = self.dicc[paso["pedido"]["origen"]]
            nd = self.dicc[paso["pedido"]["destino"]]
            folium.PolyLine(
                [prev, [no["lat"], no["lon"]]],
                color="#f0883e", weight=3.5, opacity=0.85,
                tooltip=f"Paso {i+1} → {paso['pedido']['cliente']}",
            ).add_to(m)
            folium.PolyLine(
                [[no["lat"], no["lon"]], [nd["lat"], nd["lon"]]],
                color="#3fb950", weight=2, opacity=0.6, dash_array="6 4",
                tooltip=f"Entrega #{paso['pedido']['id']}",
            ).add_to(m)
            folium.CircleMarker(
                [no["lat"], no["lon"]], radius=9,
                color="white", weight=2, fill=True,
                fill_color="#f0883e", fill_opacity=1,
                popup=folium.Popup(
                    f"<b>Paso {i+1}: {paso['pedido']['cliente']}</b><br>"
                    f"Pedido #{paso['pedido']['id']}<br>"
                    f"Dist. al origen: {paso['dist']} m<br>"
                    f"Peso: {paso['pedido']['peso']} kg · Valor: S/.{paso['pedido']['valor']}",
                    max_width=220,
                ),
            ).add_to(m)
            prev = [nd["lat"], nd["lon"]]
        folium.Marker(
            pos_inicial, icon=folium.Icon(color="green", icon="play"),
            tooltip="Punto de inicio del repartidor",
        ).add_to(m)
        return self._guardar(m)
 
    def generar_divide(self, resultado, num_reps):
        m = self._base()
        self._aristas(m)
        colores_rep = ZONE_COLORS
        for idx_rep, (rep_id, datos) in enumerate(resultado["asignaciones"].items()):
            col = colores_rep[idx_rep % len(colores_rep)]
            fcol = FOLIUM_COLORS[idx_rep % len(FOLIUM_COLORS)]
            ruta = datos["ruta"]
            for uid in ruta:
                n = self.dicc[uid]
                folium.CircleMarker(
                    [n["lat"], n["lon"]], radius=10,
                    color="white", weight=2, fill=True,
                    fill_color=col, fill_opacity=0.92,
                    tooltip=f"Rep.{rep_id} — {n['nombre']}",
                    popup=folium.Popup(
                        f"<b>{n['nombre']}</b><br>Zona Repartidor {rep_id}<br>"
                        f"Zona geográfica: {n['zona']}",
                        max_width=180,
                    ),
                ).add_to(m)
            for i in range(len(ruta) - 1):
                a, b = self.dicc[ruta[i]], self.dicc[ruta[i+1]]
                folium.PolyLine(
                    [[a["lat"], a["lon"]], [b["lat"], b["lon"]]],
                    color=col, weight=3.5, opacity=0.9,
                    tooltip=f"Rep.{rep_id} — tramo {i+1}",
                ).add_to(m)
        return self._guardar(m)
 
    def generar_mochila(self, resultado, pedidos_total):
        m = self._base()
        self._aristas(m)
        incluidos_ids = {p["id"] for p in resultado["pedidos_incluidos"]}
        for p in pedidos_total:
            no = self.dicc[p["origen"]]
            nd = self.dicc[p["destino"]]
            incluido = p["id"] in incluidos_ids
            col  = "#f0883e" if incluido else "#2a3540"
            fcol = 1.0      if incluido else 0.4
            folium.CircleMarker(
                [no["lat"], no["lon"]], radius=10 if incluido else 6,
                color="white" if incluido else "#555",
                weight=2 if incluido else 1,
                fill=True, fill_color=col, fill_opacity=fcol,
                tooltip=f"{'✓' if incluido else '✗'} #{p['id']} {p['cliente']}",
                popup=folium.Popup(
                    f"<b>{'INCLUIDO' if incluido else 'EXCLUIDO'}</b><br>"
                    f"{p['cliente']} — #{p['id']}<br>"
                    f"Peso: {p['peso']} kg · Valor: S/.{p['valor']}<br>"
                    f"Prioridad: {p['prioridad']}",
                    max_width=200,
                ),
            ).add_to(m)
            if incluido:
                folium.PolyLine(
                    [[no["lat"], no["lon"]], [nd["lat"], nd["lon"]]],
                    color="#f0883e", weight=2.5, opacity=0.7, dash_array="6 3",
                ).add_to(m)
        return self._guardar(m)
 
    def generar_backtracking(self, resultado, inicio_id, destino_id, bloqueadas):
        m = self._base()
        self._aristas(m)
        self._nodos_base(m, color="#2a3540", radius=5)
 
        # Aristas bloqueadas en rojo
        for u, v in bloqueadas:
            if u in self.dicc and v in self.dicc:
                n1, n2 = self.dicc[u], self.dicc[v]
                folium.PolyLine(
                    [[n1["lat"], n1["lon"]], [n2["lat"], n2["lon"]]],
                    color="#f85149", weight=6, opacity=0.9,
                    dash_array="10 6",
                    tooltip="⛔ CALLE BLOQUEADA",
                ).add_to(m)
                for n in [n1, n2]:
                    folium.CircleMarker(
                        [n["lat"], n["lon"]], radius=8,
                        color="#f85149", weight=2.5,
                        fill=True, fill_color="#f85149", fill_opacity=0.9,
                        tooltip=f"⛔ {n['nombre']} — tramo bloqueado",
                    ).add_to(m)
 
        # Rutas alternativas (naranja la mejor, azul las demás)
        rutas = resultado.get("rutas", [])
        for i, r in enumerate(rutas[:3]):
            col = "#f0883e" if i == 0 else "#58a6ff"
            wt  = 4.5 if i == 0 else 2
            op  = 0.95 if i == 0 else 0.45
            camino = r["camino"]
            for j in range(len(camino) - 1):
                a, b = self.dicc[camino[j]], self.dicc[camino[j+1]]
                folium.PolyLine(
                    [[a["lat"], a["lon"]], [b["lat"], b["lon"]]],
                    color=col, weight=wt, opacity=op,
                    tooltip=f"Ruta {i+1} ({r['distancia_m']} m)",
                ).add_to(m)
 
        # Inicio y destino
        ni, nf = self.dicc[inicio_id], self.dicc[destino_id]
        folium.Marker(
            [ni["lat"], ni["lon"]],
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
            tooltip=f"Inicio: {ni['nombre']}",
        ).add_to(m)
        folium.Marker(
            [nf["lat"], nf["lon"]],
            icon=folium.Icon(color="red", icon="flag", prefix="fa"),
            tooltip=f"Destino: {nf['nombre']}",
        ).add_to(m)
        return self._guardar(m)
 
    @staticmethod
    def _guardar(m):
        """Guarda el mapa en un archivo temporal y devuelve la ruta."""
        tmp = tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, prefix="cusco_mapa_"
        )
        m.save(tmp.name)
        tmp.close()
        return tmp.name
 
 
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                        INTERFAZ PRINCIPAL                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝
class InterfazLogisticaCusco:
 
    def __init__(self, root):
        self.root = root
        self.root.title("UNSAAC — Sistema de Gestión de Rutas Óptimas · Cusco")
        self.root.geometry("1440x860")
        self.root.configure(bg=C["bg"])
        self.root.resizable(True, True)
 
        # ── Carga de datos ─────────────────────────────────────────────
        self.nodos_datos  = cargar_nodos()
        self.G            = construir_grafo(self.nodos_datos, distancia_maxima=2500)
        self.dicc_nodos   = {n["id"]: n for n in self.nodos_datos}
        self.pedidos_todos = cargar_pedidos()
        self.mapa_html_path = None
 
        if FOLIUM_OK:
            self.mapa = MapaFolium(self.nodos_datos, self.G)
        else:
            self.mapa = None
 
        # ── Construir UI ───────────────────────────────────────────────
        self._topbar()
        self._layout()
        self._actualizar_estado_grafo()
 
        # ── Mapa inicial ───────────────────────────────────────────────
        self.root.after(300, self._cargar_mapa_base)
 
    # ──────────────────────────────────────────────────────────────────
    # UI: TOPBAR
    # ──────────────────────────────────────────────────────────────────
    def _topbar(self):
        bar = tk.Frame(self.root, bg=C["surface"], height=50,
                       highlightbackground=C["border"], highlightthickness=1)
        bar.pack(side=tk.TOP, fill=tk.X)
        bar.pack_propagate(False)
 
        tk.Label(bar, text="UNSAAC", font=("Courier", 12, "bold"),
                 fg=C["accent"], bg=C["surface"]).pack(side=tk.LEFT, padx=(18, 6), pady=12)
        tk.Label(bar, text="│", fg=C["border"], bg=C["surface"],
                 font=("Courier", 14)).pack(side=tk.LEFT, pady=12)
        tk.Label(bar, text="Sistema de Gestión de Rutas Óptimas · Cusco",
                 font=("Courier", 10), fg=C["muted"],
                 bg=C["surface"]).pack(side=tk.LEFT, padx=(8, 0), pady=12)
 
        self.lbl_estado = tk.Label(
            bar, text="● SISTEMA ACTIVO",
            font=("Courier", 9, "bold"), fg=C["green"], bg=C["surface"]
        )
        self.lbl_estado.pack(side=tk.RIGHT, padx=18)
 
        tk.Label(bar, text="Programación III · 2026",
                 font=("Courier", 9), fg=C["muted"],
                 bg=C["surface"]).pack(side=tk.RIGHT, padx=(0, 12))
 
    # ──────────────────────────────────────────────────────────────────
    # UI: LAYOUT PRINCIPAL (sidebar + mapa)
    # ──────────────────────────────────────────────────────────────────
    def _layout(self):
        contenedor = tk.Frame(self.root, bg=C["bg"])
        contenedor.pack(fill=tk.BOTH, expand=True)
 
        # ── SIDEBAR ──────────────────────────────────────────────────
        self.sidebar = tk.Frame(
            contenedor, bg=C["surface"], width=370,
            highlightbackground=C["border"], highlightthickness=1
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self._sidebar_contenido()
 
        # ── PANEL MAPA ────────────────────────────────────────────────
        panel_mapa = tk.Frame(contenedor, bg=C["bg"])
        panel_mapa.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._panel_mapa(panel_mapa)
 
    def _sidebar_contenido(self):
        # ── Módulos ─────────────────────────────────────────────────
        sec1 = self._seccion(self.sidebar, "// módulos algorítmicos")
 
        MODULOS = [
            ("btn_ord",   "ORDENACIÓN & BÚSQUEDA",   "Gnome · Comb · Shell Sort",   "O(n²)",       C["purple"], self.panel_ordenacion),
            ("btn_gre",   "VORAZ (GREEDY)",           "Vecino más cercano",           "O(k²)",       C["green"],  self.panel_greedy),
            ("btn_div",   "DIVIDE Y VENCERÁS",        "Zonificación recursiva",       "O(n log n)",  C["blue"],   self.panel_divide),
            ("btn_moc",   "PROG. DINÁMICA (MOCHILA)", "Knapsack 0/1",                 "O(n·W)",      C["accent"], self.panel_mochila),
            ("btn_bck",   "BACKTRACKING DFS",         "Rutas con restricciones",      "O(V!)",       C["red"],    self.panel_backtracking),
        ]
        self.btns_mod = {}
        for key, titulo, sub, comp, color, cmd in MODULOS:
            btn = self._mod_btn(sec1, titulo, sub, comp, color, cmd)
            self.btns_mod[key] = btn
 
        # ── Panel de parámetros dinámicos ─────────────────────────
        self.sec_params = self._seccion(self.sidebar, "// parámetros")
        self.frame_params = tk.Frame(self.sec_params, bg=C["surface"])
        self.frame_params.pack(fill=tk.X, padx=4, pady=(0, 4))
        tk.Label(self.frame_params,
                 text="Selecciona un módulo para configurar.",
                 font=("Courier", 9), fg=C["muted"], bg=C["surface"]
                 ).pack(anchor=tk.W)
 
        # ── Log de auditoría ──────────────────────────────────────
        self._seccion(self.sidebar, "// auditoría técnica Big-O", add_frame=False)
        log_frame = tk.Frame(self.sidebar, bg=C["surface"])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))
 
        self.txt_log = tk.Text(
            log_frame, bg="#0d1117", fg=C["green"],
            font=("Courier", 9), wrap=tk.WORD,
            relief=tk.FLAT, bd=0, padx=8, pady=6,
            state=tk.DISABLED,
            selectbackground=C["surface2"],
        )
        sb = tk.Scrollbar(log_frame, command=self.txt_log.yview,
                          bg=C["surface"], troughcolor=C["bg"],
                          activebackground=C["muted"])
        self.txt_log.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
 
        # Tags de color para el log
        self.txt_log.tag_config("h1",   foreground=C["accent"],  font=("Courier", 9, "bold"))
        self.txt_log.tag_config("h2",   foreground=C["blue"],    font=("Courier", 9, "bold"))
        self.txt_log.tag_config("val",  foreground=C["purple"])
        self.txt_log.tag_config("ok",   foreground=C["green"])
        self.txt_log.tag_config("warn", foreground=C["yellow"])
        self.txt_log.tag_config("err",  foreground=C["red"])
        self.txt_log.tag_config("dim",  foreground=C["muted"])
 
        self._log_write([
            ("// sistema iniciado\n", "h1"),
            (f"Nodos cargados : {len(self.nodos_datos)}\n", "dim"),
            (f"Aristas grafo  : {self.G.number_of_edges()}\n", "dim"),
            (f"Pedidos        : {len(self.pedidos_todos)}\n", "dim"),
            (f"Folium         : {'OK' if FOLIUM_OK else 'NO INSTALADO'}\n",
             "ok" if FOLIUM_OK else "warn"),
            (f"tkinterweb     : {'OK' if TKWEB_OK else 'NO INSTALADO (se abre en navegador)'}\n",
             "ok" if TKWEB_OK else "warn"),
            ("\nSelecciona un módulo → EJECUTAR\n", "dim"),
        ])
 
        # ── Estado grafo (leyenda inferior) ──────────────────────
        self.frm_estado = tk.Frame(self.sidebar, bg=C["surface2"],
                                   highlightbackground=C["border"],
                                   highlightthickness=1)
        self.frm_estado.pack(fill=tk.X, padx=6, pady=6)
        self.lbl_grafo_info = tk.Label(
            self.frm_estado,
            text="", font=("Courier", 8),
            fg=C["muted"], bg=C["surface2"],
            justify=tk.LEFT, padx=8, pady=6
        )
        self.lbl_grafo_info.pack(anchor=tk.W)
 
    def _panel_mapa(self, parent):
        """Panel derecho con mapa embebido o botón para abrir en browser."""
        # ── Info overlay ──────────────────────────────────────────
        info_bar = tk.Frame(parent, bg=C["surface2"],
                            highlightbackground=C["border"],
                            highlightthickness=1)
        info_bar.pack(fill=tk.X, padx=6, pady=(6, 0))
 
        self.lbl_modulo  = tk.Label(info_bar, text="Módulo: Ninguno",
                                    font=("Courier", 9, "bold"),
                                    fg=C["accent"], bg=C["surface2"])
        self.lbl_modulo.pack(side=tk.LEFT, padx=12, pady=6)
 
        self.lbl_tiempo  = tk.Label(info_bar, text="Tiempo: —",
                                    font=("Courier", 9),
                                    fg=C["muted"], bg=C["surface2"])
        self.lbl_tiempo.pack(side=tk.LEFT, padx=12)
 
        self.btn_abrir   = tk.Button(
            info_bar, text="⊞  Abrir mapa completo en navegador",
            font=("Courier", 9, "bold"),
            fg=C["bg"], bg=C["blue"],
            relief=tk.FLAT, bd=0, padx=12, pady=3,
            cursor="hand2",
            command=self._abrir_browser
        )
        self.btn_abrir.pack(side=tk.RIGHT, padx=10, pady=6)
 
        # ── Área de mapa ──────────────────────────────────────────
        if TKWEB_OK:
            self.html_frame = HtmlFrame(parent, messages_enabled=False)
            self.html_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        else:
            # Fallback: canvas con instrucción
            self.canvas_fallback = tk.Canvas(
                parent, bg="#0d1117",
                highlightbackground=C["border"], highlightthickness=1
            )
            self.canvas_fallback.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
            self._canvas_msg("Mapa listo — haz clic en 'Abrir mapa completo en navegador'\n"
                             "o instala tkinterweb para mapa embebido:\n"
                             "  pip install tkinterweb")
 
    # ──────────────────────────────────────────────────────────────────
    # HELPERS UI
    # ──────────────────────────────────────────────────────────────────
    def _seccion(self, parent, titulo, add_frame=True):
        tk.Label(parent, text=titulo,
                 font=("Courier", 8, "bold"), fg=C["muted"],
                 bg=C["surface"], anchor=tk.W
                 ).pack(fill=tk.X, padx=12, pady=(10, 4))
        frm = tk.Frame(parent, bg=C["surface"],
                       highlightbackground=C["border"], highlightthickness=0)
        if add_frame:
            frm.pack(fill=tk.X, padx=8, pady=(0, 4))
        return frm
 
    def _mod_btn(self, parent, titulo, sub, comp, color, cmd):
        frm = tk.Frame(parent, bg=C["surface2"],
                       highlightbackground=C["border"],
                       highlightthickness=1)
        frm.pack(fill=tk.X, pady=3, padx=2)
 
        ind = tk.Label(frm, text="█", fg=color,
                       bg=C["surface2"], font=("Courier", 12))
        ind.pack(side=tk.LEFT, padx=(8, 4), pady=8)
 
        txt_frm = tk.Frame(frm, bg=C["surface2"])
        txt_frm.pack(side=tk.LEFT, expand=True, fill=tk.X, pady=4)
        tk.Label(txt_frm, text=titulo,
                 font=("Courier", 9, "bold"), fg=C["text"],
                 bg=C["surface2"], anchor=tk.W).pack(anchor=tk.W)
        tk.Label(txt_frm, text=sub,
                 font=("Courier", 8), fg=C["muted"],
                 bg=C["surface2"], anchor=tk.W).pack(anchor=tk.W)
 
        tk.Label(frm, text=comp,
                 font=("Courier", 8, "bold"), fg=C["yellow"],
                 bg=C["surface2"]).pack(side=tk.RIGHT, padx=10)
 
        for w in [frm, ind, txt_frm]:
            w.bind("<Button-1>", lambda e, c=cmd: c())
            w.bind("<Enter>",
                   lambda e, f=frm: f.config(highlightbackground=color))
            w.bind("<Leave>",
                   lambda e, f=frm: f.config(highlightbackground=C["border"]))
        return frm
 
    def _limpiar_params(self):
        for w in self.frame_params.winfo_children():
            w.destroy()
 
    def _row(self, parent, label):
        frm = tk.Frame(parent, bg=C["surface"])
        frm.pack(fill=tk.X, pady=3)
        tk.Label(frm, text=label, font=("Courier", 9),
                 fg=C["muted"], bg=C["surface"],
                 width=14, anchor=tk.W).pack(side=tk.LEFT)
        return frm
 
    def _select(self, row, opts, width=22):
        var = tk.StringVar(value=opts[0])
        cb  = ttk.Combobox(row, textvariable=var,
                            values=opts, width=width, state="readonly",
                            font=("Courier", 9))
        cb.pack(side=tk.LEFT, padx=4)
        return var
 
    def _spinbox(self, row, frm=1, to=25, val=8, w=6):
        var = tk.IntVar(value=val)
        sb  = tk.Spinbox(row, from_=frm, to=to, textvariable=var,
                          width=w, font=("Courier", 9),
                          bg=C["surface2"], fg=C["text"],
                          buttonbackground=C["border"],
                          relief=tk.FLAT)
        sb.pack(side=tk.LEFT, padx=4)
        return var
 
    def _btn_run(self, parent, label, color, cmd):
        tk.Button(
            parent, text=f"  {label}  ",
            font=("Courier", 9, "bold"),
            fg="#000", bg=color,
            relief=tk.FLAT, bd=0, pady=5,
            cursor="hand2", command=cmd
        ).pack(side=tk.LEFT, padx=(0, 6), pady=(6, 2))
 
    def _btn_reset(self, parent):
        tk.Button(
            parent, text="Reset mapa",
            font=("Courier", 8),
            fg=C["muted"], bg=C["surface2"],
            relief=tk.FLAT, bd=0, pady=5, padx=8,
            cursor="hand2",
            command=self._cargar_mapa_base
        ).pack(side=tk.LEFT, pady=(6, 2))
 
    def _canvas_msg(self, msg):
        self.canvas_fallback.delete("all")
        self.canvas_fallback.create_text(
            400, 300, text=msg, fill=C["muted"],
            font=("Courier", 11), justify=tk.CENTER
        )
 
    # ──────────────────────────────────────────────────────────────────
    # PANELS DE PARÁMETROS POR MÓDULO
    # ──────────────────────────────────────────────────────────────────
    def panel_ordenacion(self):
        self._limpiar_params()
        r1 = self._row(self.frame_params, "Criterio:")
        self.ord_crit = self._select(r1, ["prioridad", "peso", "valor"])
        r2 = self._row(self.frame_params, "Top nodos:")
        self.ord_top  = self._spinbox(r2, 3, 10, 5)
        r3 = tk.Frame(self.frame_params, bg=C["surface"]); r3.pack(anchor=tk.W, pady=2)
        self._btn_run(r3, "EJECUTAR", C["purple"], self.ejecutar_ordenacion)
        self._btn_reset(r3)
        self.lbl_modulo.config(text="Módulo: Ordenación")
 
    def panel_greedy(self):
        self._limpiar_params()
        nodos_opts = [f"{n['id']}: {n['nombre']}" for n in self.nodos_datos]
        r1 = self._row(self.frame_params, "Inicio:")
        self.gr_inicio = self._select(r1, nodos_opts, width=25)
        r2 = self._row(self.frame_params, "N pedidos:")
        self.gr_n = self._spinbox(r2, 1, 25, 8)
        r3 = tk.Frame(self.frame_params, bg=C["surface"]); r3.pack(anchor=tk.W, pady=2)
        self._btn_run(r3, "EJECUTAR", C["green"], self.ejecutar_greedy)
        self._btn_reset(r3)
        self.lbl_modulo.config(text="Módulo: Greedy")
 
    def panel_divide(self):
        self._limpiar_params()
        r1 = self._row(self.frame_params, "Repartidores:")
        self.dv_reps  = self._select(r1, ["2", "3", "4"])
        self.dv_reps.set("3")
        r2 = self._row(self.frame_params, "Prof. máx:")
        self.dv_prof  = self._select(r2, ["1", "2", "3"])
        self.dv_prof.set("2")
        r3 = tk.Frame(self.frame_params, bg=C["surface"]); r3.pack(anchor=tk.W, pady=2)
        self._btn_run(r3, "EJECUTAR", C["blue"], self.ejecutar_divide)
        self._btn_reset(r3)
        self.lbl_modulo.config(text="Módulo: Divide y Vencerás")
 
    def panel_mochila(self):
        self._limpiar_params()
        r1 = self._row(self.frame_params, "Cap. (kg):")
        self.mo_cap = self._spinbox(r1, 5, 100, 15)
        r2 = self._row(self.frame_params, "N pedidos:")
        self.mo_n   = self._spinbox(r2, 5, 25, 25)
        r3 = tk.Frame(self.frame_params, bg=C["surface"]); r3.pack(anchor=tk.W, pady=2)
        self._btn_run(r3, "EJECUTAR", C["accent"], self.ejecutar_mochila)
        self._btn_reset(r3)
        self.lbl_modulo.config(text="Módulo: Prog. Dinámica")
 
    def panel_backtracking(self):
        self._limpiar_params()
        nodos_opts = [f"{n['id']}: {n['nombre']}" for n in self.nodos_datos]
        r1 = self._row(self.frame_params, "Inicio:")
        self.bt_ini = self._select(r1, nodos_opts, width=25)
        self.bt_ini.set("3: San Blas")
        r2 = self._row(self.frame_params, "Destino:")
        self.bt_fin = self._select(r2, nodos_opts, width=25)
        self.bt_fin.set("9: Wanchaq")
        r3 = self._row(self.frame_params, "Bloqueo:")
        self.bt_blk = self._select(r3, [
            "1↔3 (Plaza↔San Blas)",
            "1↔2 (Plaza↔Mercado S.P.)",
            "Sin bloqueo"
        ], width=25)
        r4 = tk.Frame(self.frame_params, bg=C["surface"]); r4.pack(anchor=tk.W, pady=2)
        self._btn_run(r4, "EJECUTAR", C["red"], self.ejecutar_backtracking)
        self._btn_reset(r4)
        self.lbl_modulo.config(text="Módulo: Backtracking")
 
    # ──────────────────────────────────────────────────────────────────
    # LOG
    # ──────────────────────────────────────────────────────────────────
    def _log_write(self, partes):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.delete("1.0", tk.END)
        for texto, tag in partes:
            self.txt_log.insert(tk.END, texto, tag)
        self.txt_log.config(state=tk.DISABLED)
        self.txt_log.see(tk.END)
 
    # ──────────────────────────────────────────────────────────────────
    # MAPA
    # ──────────────────────────────────────────────────────────────────
    def _cargar_mapa(self, ruta_html):
        self.mapa_html_path = ruta_html
        if TKWEB_OK:
            self.html_frame.load_file(ruta_html)
        else:
            self._canvas_msg(
                f"Mapa generado:\n{os.path.basename(ruta_html)}\n\n"
                "Haz clic en 'Abrir mapa completo en navegador'"
            )
 
    def _cargar_mapa_base(self):
        if FOLIUM_OK:
            ruta = self.mapa.generar_base()
            self._cargar_mapa(ruta)
        elif not TKWEB_OK and hasattr(self, 'canvas_fallback'):
            self._canvas_msg("Instala folium:\n  pip install folium\n\n"
                             "Instala tkinterweb:\n  pip install tkinterweb")
 
    def _abrir_browser(self):
        if self.mapa_html_path and os.path.exists(self.mapa_html_path):
            webbrowser.open(f"file://{self.mapa_html_path}")
        else:
            self._cargar_mapa_base()
            self.root.after(500, self._abrir_browser)
 
    def _actualizar_estado_grafo(self):
        self.lbl_grafo_info.config(
            text=(f"  Nodos: {self.G.number_of_nodes()}   "
                  f"Aristas: {self.G.number_of_edges()}   "
                  f"Pedidos: {len(self.pedidos_todos)}   "
                  f"Dist.máx: 2500 m")
        )
 
    def _set_tiempo(self, ms):
        self.lbl_tiempo.config(text=f"Tiempo: {ms} ms")
 
    # ──────────────────────────────────────────────────────────────────
    # EJECUTORES DE MÓDULOS
    # ──────────────────────────────────────────────────────────────────
    def ejecutar_ordenacion(self):
        crit = self.ord_crit.get()
        top  = self.ord_top.get()
        t0 = time.perf_counter()
 
        if crit == "prioridad":
            sorted_p = gnome_sort_prioridad(self.pedidos_todos)
            algo, comp = "Gnome Sort", "O(n²)"
        elif crit == "peso":
            sorted_p = comb_sot_peso(self.pedidos_todos)
            algo, comp = "Comb Sort", "O(n²)"
        else:
            sorted_p = shell_sort_valor(self.pedidos_todos)
            algo, comp = "Shell Sort", "O(n log² n)"
 
        ms = round((time.perf_counter() - t0) * 1000, 4)
        self._set_tiempo(ms)
 
        if FOLIUM_OK:
            ruta = self.mapa.generar_ordenacion(sorted_p, crit, top)
            self._cargar_mapa(ruta)
 
        partes = [
            (f"// ordenación — {algo}\n", "h1"),
            (f"N={len(self.pedidos_todos)} · Complejidad: ", "dim"),
            (f"{comp}\n", "val"),
            (f"Tiempo: {ms} ms\n\n", "dim"),
            (f"Top {top} (criterio: {crit}):\n", "h2"),
        ]
        for p in sorted_p[:top]:
            partes.append((f"  → #{p['id']} {p['cliente']}: {crit}={p[crit]}\n", "ok"))
        partes.append(("\nTodos los pedidos:\n", "h2"))
        for p in sorted_p:
            pri = "🔴" if p["prioridad"]==1 else "🟡" if p["prioridad"]==2 else "⚪"
            partes.append((f"  {pri} #{p['id']:>2} {p['cliente']:<12} "
                           f"{crit}={p[crit]}\n", "dim"))
        self._log_write(partes)
 
    def ejecutar_greedy(self):
        ini_str  = self.gr_inicio.get()
        ini_id   = int(ini_str.split(":")[0])
        N        = self.gr_n.get()
        pedidos  = self.pedidos_todos[:N]
        inicio   = self.dicc_nodos[ini_id]
 
        t0 = time.perf_counter()
        pos_lat, pos_lon = inicio["lat"], inicio["lon"]
        pend  = list(pedidos)
        ruta  = []
        dist_total = 0
 
        from datos.grafo_base import haversine
        while pend:
            mejor, md = None, float("inf")
            for p in pend:
                no = self.dicc_nodos[p["origen"]]
                d  = haversine(pos_lat, pos_lon, no["lat"], no["lon"])
                if d < md:
                    md, mejor = d, p
            ruta.append({"pedido": mejor, "dist": round(md)})
            dist_total += md
            nd = self.dicc_nodos[mejor["destino"]]
            pos_lat, pos_lon = nd["lat"], nd["lon"]
            pend.remove(mejor)
 
        ms = round((time.perf_counter() - t0) * 1000, 4)
        self._set_tiempo(ms)
 
        if FOLIUM_OK:
            ruta_map = self.mapa.generar_greedy(ruta, [inicio["lat"], inicio["lon"]])
            self._cargar_mapa(ruta_map)
 
        partes = [
            ("// greedy — vecino más cercano\n", "h1"),
            (f"Inicio: {inicio['nombre']}\n", "dim"),
            (f"N pedidos: {N} · Complejidad: ", "dim"),
            ("O(k²)\n", "val"),
            (f"Tiempo: {ms} ms\n", "dim"),
            (f"Dist. total: {round(dist_total)} m\n\n", "dim"),
            ("Secuencia de entregas:\n", "h2"),
        ]
        for i, r in enumerate(ruta):
            partes.append((f"  Paso {i+1:>2}: {r['pedido']['cliente']:<12} "
                           f"#{r['pedido']['id']:>2} → {r['dist']} m\n", "ok"))
        partes.append(("\nOrden IDs: ", "h2"))
        partes.append((f"{' → '.join(str(r['pedido']['id']) for r in ruta)}\n", "val"))
        self._log_write(partes)
 
    def ejecutar_divide(self):
        num_reps = int(self.dv_reps.get())
        prof_max = int(self.dv_prof.get())
 
        t0 = time.perf_counter()
        resultado = procesar_divide_y_venceras(self.G, num_repartidores=num_reps)
        ms = round((time.perf_counter() - t0) * 1000, 4)
        self._set_tiempo(ms)
 
        if FOLIUM_OK:
            ruta_map = self.mapa.generar_divide(resultado, num_reps)
            self._cargar_mapa(ruta_map)
 
        partes = [
            ("// divide y vencerás — zonificación\n", "h1"),
            (f"Repartidores: {num_reps} · Zonas: {resultado['num_zonas']}\n", "dim"),
            (f"Complejidad: ", "dim"),
            ("O(n log n)", "val"),
            (" + O(k²) por zona\n", "dim"),
            (f"Tiempo: {ms} ms\n\n", "dim"),
        ]
        for rep_id, datos in resultado["asignaciones"].items():
            partes.append((f"Repartidor {rep_id} ({len(datos['ruta'])} nodos):\n", "h2"))
            nombres = [self.dicc_nodos[uid]["nombre"] for uid in datos["ruta"]]
            partes.append((f"  Dist: {datos['distancia_m']} m\n", "ok"))
            partes.append((f"  Ruta: {' → '.join(n.split()[0] for n in nombres)}\n", "dim"))
        self._log_write(partes)
 
    def ejecutar_mochila(self):
        cap = self.mo_cap.get()
        N   = self.mo_n.get()
        ped = self.pedidos_todos[:N]
 
        t0 = time.perf_counter()
        res = optimizar_carga_mochila(ped, float(cap))
        ms  = round((time.perf_counter() - t0) * 1000, 4)
        self._set_tiempo(ms)
 
        if FOLIUM_OK:
            ruta_map = self.mapa.generar_mochila(res, ped)
            self._cargar_mapa(ruta_map)
 
        partes = [
            ("// prog. dinámica — knapsack 0/1\n", "h1"),
            (f"Capacidad: {cap} kg · Pedidos: {N}\n", "dim"),
            (f"Complejidad: ", "dim"),
            (f"{res['complejidad']}\n", "val"),
            (f"Tiempo: {ms} ms\n\n", "dim"),
            ("Resultado óptimo:\n", "h2"),
            (f"  Valor máximo  : S/. {res['valor_maximo']:.2f}\n", "ok"),
            (f"  Peso total    : {res['peso_total']} kg / {cap} kg\n", "ok"),
            (f"  Pedidos cargados: {len(res['pedidos_incluidos'])} / {N}\n\n", "ok"),
            ("Pedidos incluidos:\n", "h2"),
        ]
        for p in res["pedidos_incluidos"]:
            partes.append((f"  ✓ {p['cliente']:<12} {p['peso']} kg  S/.{p['valor']}\n", "ok"))
        excl = [p for p in ped if p["id"] not in {x["id"] for x in res["pedidos_incluidos"]}]
        if excl:
            partes.append((f"\nExcluidos ({len(excl)}):\n", "h2"))
            for p in excl:
                partes.append((f"  ✗ {p['cliente']:<12} {p['peso']} kg\n", "warn"))
        self._log_write(partes)
 
    def ejecutar_backtracking(self):
        ini_id = int(self.bt_ini.get().split(":")[0])
        fin_id = int(self.bt_fin.get().split(":")[0])
        blk    = self.bt_blk.get()
 
        bloqueadas = []
        if "1↔3" in blk:
            bloqueadas = [[1, 3]]
        elif "1↔2" in blk:
            bloqueadas = [[1, 2]]
 
        t0  = time.perf_counter()
        res = backtracking_rutas_con_restricciones(
            self.G, inicio=ini_id, destino=fin_id,
            aristas_bloqueadas=bloqueadas, max_rutas=5
        )
        ms = round((time.perf_counter() - t0) * 1000, 4)
        self._set_tiempo(ms)
 
        if FOLIUM_OK:
            ruta_map = self.mapa.generar_backtracking(
                res, ini_id, fin_id, bloqueadas
            )
            self._cargar_mapa(ruta_map)
 
        ni, nf = self.dicc_nodos[ini_id], self.dicc_nodos[fin_id]
        partes = [
            ("// backtracking DFS — rutas con restricciones\n", "h1"),
            (f"De: {ni['nombre']} → {nf['nombre']}\n", "dim"),
            (f"Bloqueo: {blk if bloqueadas else 'ninguno'}\n", "warn" if bloqueadas else "dim"),
            (f"Nodos explorados: {res['nodos_explorados']}\n", "dim"),
            (f"Rutas halladas  : {res['total_rutas']}\n", "dim"),
            (f"Complejidad: ", "dim"),
            ("O(V!) podado a max=5\n", "val"),
            (f"Tiempo: {ms} ms\n\n", "dim"),
        ]
        if not res["rutas"]:
            partes.append(("✗ No se encontraron rutas alternativas.\n", "err"))
        else:
            for i, r in enumerate(res["rutas"]):
                partes.append((f"Ruta {i+1}{' ← ÓPTIMA' if i==0 else ''} — {r['distancia_m']} m\n", "h2"))
                nombres = [self.dicc_nodos[uid]["nombre"] for uid in r["camino"]]
                partes.append((f"  {' → '.join(nombres)}\n", "ok" if i==0 else "dim"))
        self._log_write(partes)
 
 
