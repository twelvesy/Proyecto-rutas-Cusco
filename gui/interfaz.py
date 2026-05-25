"""
interfaz.py — Dashboard Logístico de Cusco (Tkinter)
=====================================================
Interfaz moderna con mapa de fondo generado, sidebar animado,
panel de métricas Big-O, y visualización interactiva del grafo.
"""

import tkinter as tk
from tkinter import font as tkfont
import os
import sys
import math
import time
import threading

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_DIR, ".."))

from datos.grafo_base import cargar_nodos, construir_grafo
from algoritmos.ordenacion import (cargar_pedidos, gnome_sort_prioridad,
                                    comb_sot_peso, shell_sort_valor)
from algoritmos.divide_venceras import procesar_divide_y_venceras
from algoritmos.backtracking import backtracking_rutas_con_restricciones
from algoritmos.dinamica import optimizar_carga_mochila

# ══════════════════════════════════════════════════════════════
#  PALETA DE COLORES
# ══════════════════════════════════════════════════════════════
C = {
    "bg_app":      "#0d1117",
    "bg_sidebar":  "#161b22",
    "bg_panel":    "#1c2128",
    "bg_card":     "#21262d",
    "bg_canvas":   "#0d1117",
    "border":      "#30363d",
    "accent":      "#58a6ff",
    "accent2":     "#3fb950",
    "accent3":     "#d29922",
    "accent4":     "#f85149",
    "accent5":     "#bc8cff",
    "text_main":   "#e6edf3",
    "text_sub":    "#8b949e",
    "text_dim":    "#484f58",
    # Módulos
    "mod_orden":   "#8957e5",
    "mod_greedy":  "#e67e22",
    "mod_divide":  "#2ecc71",
    "mod_dp":      "#3498db",
    "mod_back":    "#e74c3c",
    # Zonas
    "zona0":       "#2ecc71",
    "zona1":       "#e67e22",
    "zona2":       "#9b59b6",
    "zona3":       "#3498db",
}

COLORES_ZONA = [C["zona0"], C["zona1"], C["zona2"], C["zona3"]]

MODULOS = [
    ("📦", "Ordenamientos",    "Almacén", C["mod_orden"],  "O(n²)"),
    ("🗺", "Divide y Vencerás","Zonas",   C["mod_divide"], "O(n log n)"),
    ("🚧", "Backtracking",     "Vial",    C["mod_back"],   "O(V!)"),
    ("⚖", "Mochila DP",       "Carga",   C["mod_dp"],     "O(n·W)"),
    ("⚡", "Greedy",           "Ruta",    C["mod_greedy"], "O(n²)"),
]


class InterfazLogisticaCusco:
    def __init__(self, root):
        self.root = root
        self.root.title("UNSAAC — Sistema de Rutas Óptimas · Cusco")
        self.root.geometry("1440x860")
        self.root.configure(bg=C["bg_app"])
        self.root.resizable(True, True)
        self.root.minsize(1100, 700)

        # ── Datos ────────────────────────────────────────────────
        self.nodos_datos = cargar_nodos()
        self.G           = construir_grafo(self.nodos_datos, distancia_maxima=2500)
        self.dicc_nodos  = {n["id"]: n for n in self.nodos_datos}
        self.modulo_activo = None
        self.nodo_hover    = None
        self._foto_mapa    = None   # referencia PhotoImage para evitar GC

        # ── Estado de animación ──────────────────────────────────
        self._anim_nodos = {}       # {id: radio_actual}
        self._anim_running = False

        self._construir_ui()
        self.root.update()
        self._cargar_mapa_fondo()
        self.dibujar_grafo_base()
        self._bind_canvas_eventos()

    # ════════════════════════════════════════════════════════════
    #  UI PRINCIPAL
    # ════════════════════════════════════════════════════════════

    def _construir_ui(self):
        # ── Barra superior ───────────────────────────────────────
        self._barra_top()

        # ── Cuerpo ───────────────────────────────────────────────
        cuerpo = tk.Frame(self.root, bg=C["bg_app"])
        cuerpo.pack(fill=tk.BOTH, expand=True)

        # Sidebar izquierdo
        self.sidebar = tk.Frame(cuerpo, width=260, bg=C["bg_sidebar"])
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self._construir_sidebar(self.sidebar)

        # Área central (canvas)
        centro = tk.Frame(cuerpo, bg=C["bg_canvas"])
        centro.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._construir_canvas(centro)

        # Panel derecho
        self.panel_der = tk.Frame(cuerpo, width=300, bg=C["bg_sidebar"])
        self.panel_der.pack(side=tk.RIGHT, fill=tk.Y)
        self.panel_der.pack_propagate(False)
        self._construir_panel_derecho(self.panel_der)

    # ── Barra superior ───────────────────────────────────────────
    def _barra_top(self):
        barra = tk.Frame(self.root, bg=C["bg_panel"], height=52)
        barra.pack(fill=tk.X)
        barra.pack_propagate(False)

        # Borde inferior
        borde = tk.Frame(self.root, bg=C["border"], height=1)
        borde.pack(fill=tk.X)

        # Icono + título
        tk.Label(barra, text="  🗺", font=("Segoe UI", 18),
                 fg=C["accent"], bg=C["bg_panel"]).pack(side=tk.LEFT, padx=(16,4), pady=8)
        tk.Label(barra, text="Sistema de Gestión de Rutas Óptimas — Cusco",
                 font=("Segoe UI", 13, "bold"), fg=C["text_main"],
                 bg=C["bg_panel"]).pack(side=tk.LEFT, pady=8)
        tk.Label(barra, text="Universidad Nacional de San Antonio Abad del Cusco · Programación III",
                 font=("Segoe UI", 8), fg=C["text_sub"],
                 bg=C["bg_panel"]).pack(side=tk.LEFT, padx=16, pady=8)

        # Badges derecha
        for txt, col in [("v1.0", C["accent"]), ("2026", C["accent2"])]:
            lbl = tk.Label(barra, text=f" {txt} ", font=("Consolas", 9, "bold"),
                           fg="white", bg=col, padx=6, pady=2)
            lbl.pack(side=tk.RIGHT, padx=4, pady=14)

        # Stats rápidas
        self.lbl_stats = tk.Label(barra,
            text=f"  Nodos: {self.G.number_of_nodes()}  │  Aristas: {self.G.number_of_edges()}  │  Pedidos: 25  ",
            font=("Consolas", 9), fg=C["text_sub"], bg=C["bg_panel"])
        self.lbl_stats.pack(side=tk.RIGHT, padx=8)

    # ── Sidebar ──────────────────────────────────────────────────
    def _construir_sidebar(self, parent):
        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X)

        # Logo sección
        tk.Label(parent, text="MÓDULOS", font=("Segoe UI", 9, "bold"),
                 fg=C["text_dim"], bg=C["bg_sidebar"],
                 anchor=tk.W).pack(fill=tk.X, padx=20, pady=(18, 6))

        # Botones de módulos
        self.btns_modulo = []
        acciones = [
            self.ejecutar_ordenamiento,
            self.ejecutar_divide_y_venceras,
            self.ejecutar_backtracking,
            self.ejecutar_mochila,
            self.ejecutar_greedy,
        ]
        for i, ((ico, nombre, sub, color, bigo), cmd) in enumerate(zip(MODULOS, acciones)):
            btn_frame = tk.Frame(parent, bg=C["bg_sidebar"], cursor="hand2")
            btn_frame.pack(fill=tk.X, padx=10, pady=2)

            indicador = tk.Frame(btn_frame, width=4, bg=C["bg_sidebar"])
            indicador.pack(side=tk.LEFT, fill=tk.Y)

            contenido = tk.Frame(btn_frame, bg=C["bg_sidebar"], padx=12, pady=10)
            contenido.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            fila1 = tk.Frame(contenido, bg=C["bg_sidebar"])
            fila1.pack(fill=tk.X)
            tk.Label(fila1, text=f"{ico}  {nombre}", font=("Segoe UI", 10, "bold"),
                     fg=C["text_main"], bg=C["bg_sidebar"], anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(fila1, text=bigo, font=("Consolas", 8),
                     fg=color, bg=C["bg_sidebar"]).pack(side=tk.RIGHT)

            tk.Label(contenido, text=sub, font=("Segoe UI", 8),
                     fg=C["text_sub"], bg=C["bg_sidebar"], anchor=tk.W).pack(fill=tk.X)

            # Hover y click
            widgets = [btn_frame, indicador, contenido, fila1]
            for w in btn_frame.winfo_children() + [btn_frame]:
                pass

            def _make_handler(frame, ind, idx, color, cmd):
                def on_enter(e):
                    frame.config(bg=C["bg_card"])
                    for c in frame.winfo_children():
                        self._bg_rec(c, C["bg_card"])
                    ind.config(bg=color)
                def on_leave(e):
                    bg = C["bg_panel"] if self.modulo_activo == idx else C["bg_sidebar"]
                    frame.config(bg=bg)
                    for c in frame.winfo_children():
                        self._bg_rec(c, bg)
                    ind.config(bg=color if self.modulo_activo == idx else C["bg_sidebar"])
                def on_click(e):
                    self._seleccionar_modulo(idx, frame, ind, color)
                    cmd()
                return on_enter, on_leave, on_click

            on_e, on_l, on_c = _make_handler(btn_frame, indicador, i, color, cmd)
            for w in [btn_frame, contenido, fila1] + list(fila1.winfo_children()) + list(contenido.winfo_children()):
                w.bind("<Enter>", on_e)
                w.bind("<Leave>", on_l)
                w.bind("<Button-1>", on_c)

            self.btns_modulo.append((btn_frame, indicador, color))

        # Separador
        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X, padx=10, pady=16)
        tk.Label(parent, text="INFORMACIÓN", font=("Segoe UI", 9, "bold"),
                 fg=C["text_dim"], bg=C["bg_sidebar"], anchor=tk.W).pack(fill=tk.X, padx=20, pady=(0,8))

        info_lines = [
            ("Docentes:", C["text_sub"]),
            ("M.Sc. Hector E. Ugarte R.", C["text_main"]),
            ("M.Sc. Boris Chullo Llave", C["text_main"]),
            ("", C["text_sub"]),
            ("Entrega: 28 mayo 2026", C["accent3"]),
        ]
        for txt, col in info_lines:
            tk.Label(parent, text=txt, font=("Segoe UI", 8),
                     fg=col, bg=C["bg_sidebar"], anchor=tk.W).pack(fill=tk.X, padx=20)

        # Botón reset
        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X, padx=10, pady=12)
        btn_reset = tk.Button(parent, text="↺  Reiniciar Mapa",
                              font=("Segoe UI", 9), fg=C["text_sub"],
                              bg=C["bg_card"], activebackground=C["bg_panel"],
                              activeforeground=C["text_main"],
                              bd=0, padx=14, pady=8, cursor="hand2",
                              command=self._reset_mapa)
        btn_reset.pack(fill=tk.X, padx=10, pady=4)

    def _bg_rec(self, widget, color):
        try:
            widget.config(bg=color)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._bg_rec(child, color)

    def _seleccionar_modulo(self, idx, frame, ind, color):
        # Desactivar anterior
        if self.modulo_activo is not None and self.modulo_activo != idx:
            prev_frame, prev_ind, prev_color = self.btns_modulo[self.modulo_activo]
            prev_frame.config(bg=C["bg_sidebar"])
            self._bg_rec(prev_frame, C["bg_sidebar"])
            prev_ind.config(bg=C["bg_sidebar"])
        self.modulo_activo = idx
        frame.config(bg=C["bg_panel"])
        self._bg_rec(frame, C["bg_panel"])
        ind.config(bg=color)

    # ── Canvas central ───────────────────────────────────────────
    def _construir_canvas(self, parent):
        # Barra de título del mapa
        barra_mapa = tk.Frame(parent, bg=C["bg_panel"], height=38)
        barra_mapa.pack(fill=tk.X)
        barra_mapa.pack_propagate(False)

        self.lbl_titulo_mapa = tk.Label(barra_mapa,
            text="  📍  Grafo de Cusco — Nodos y Aristas",
            font=("Segoe UI", 10, "bold"), fg=C["text_main"], bg=C["bg_panel"],
            anchor=tk.W)
        self.lbl_titulo_mapa.pack(side=tk.LEFT, fill=tk.Y, padx=8)

        self.lbl_badge_mapa = tk.Label(barra_mapa,
            text=" Estructura: Grafo Ponderado No Dirigido ",
            font=("Consolas", 8), fg=C["accent2"], bg="#0d2818",
            padx=6, pady=2)
        self.lbl_badge_mapa.pack(side=tk.RIGHT, padx=12, pady=7)

        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X)

        # Canvas
        self.canvas = tk.Canvas(parent, bg=C["bg_canvas"], highlightthickness=0,
                                 cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Leyenda inferior
        leyenda = tk.Frame(parent, bg=C["bg_panel"], height=30)
        leyenda.pack(fill=tk.X)
        leyenda.pack_propagate(False)
        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X)

        items = [
            ("●", "#f39c12", " Nodo normal"),
            ("●", C["accent2"], " Inicio de ruta"),
            ("●", C["accent4"], " En ruta activa"),
            ("—", C["border"], " Arista normal"),
            ("- -", C["accent4"], " Arista bloqueada"),
        ]
        for sym, col, desc in items:
            tk.Label(leyenda, text=sym, fg=col, bg=C["bg_panel"],
                     font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=(10,0))
            tk.Label(leyenda, text=desc, fg=C["text_sub"], bg=C["bg_panel"],
                     font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0,6))

        # Tooltip flotante
        self.tooltip = tk.Label(self.root, text="", font=("Segoe UI", 8),
                                 fg=C["text_main"], bg=C["bg_card"],
                                 bd=1, relief=tk.FLAT, padx=8, pady=4)

    # ── Panel derecho ────────────────────────────────────────────
    def _construir_panel_derecho(self, parent):
        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X)

        # Big-O section
        tk.Label(parent, text="COMPLEJIDAD BIG-O", font=("Segoe UI", 9, "bold"),
                 fg=C["text_dim"], bg=C["bg_sidebar"],
                 anchor=tk.W).pack(fill=tk.X, padx=16, pady=(16, 8))

        bigo_data = [
            ("Ordenación (Gnome/Comb/Shell)", C["mod_orden"],
             "Tiempo: O(n²) / O(n log²n)", "Espacio: O(1)",
             "Algoritmos in-place, sin memoria extra"),
            ("Greedy — Vec. Cercano", C["mod_greedy"],
             "Tiempo: O(n²)", "Espacio: O(n)",
             "Buena aproximación, no garantiza óptimo"),
            ("Divide y Vencerás", C["mod_divide"],
             "Tiempo: O(n log n)", "Espacio: O(n log n)",
             "Paralelizable por zonas geográficas"),
            ("Programación Dinámica", C["mod_dp"],
             "Tiempo: O(n × W)", "Espacio: O(n × W)",
             "Óptimo global garantizado"),
            ("Backtracking", C["mod_back"],
             "Tiempo: O(V!)", "Espacio: O(V)",
             "Exhaustivo, práctico solo para grafos pequeños"),
        ]

        for nombre, color, t1, t2, nota in bigo_data:
            card = tk.Frame(parent, bg=C["bg_card"], pady=8, padx=12)
            card.pack(fill=tk.X, padx=10, pady=3)
            tk.Frame(card, bg=color, width=3, height=48).pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
            cuerpo_card = tk.Frame(card, bg=C["bg_card"])
            cuerpo_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            tk.Label(cuerpo_card, text=nombre, font=("Segoe UI", 8, "bold"),
                     fg=color, bg=C["bg_card"], anchor=tk.W).pack(fill=tk.X)
            tk.Label(cuerpo_card, text=t1, font=("Consolas", 8),
                     fg=C["accent"], bg=C["bg_card"], anchor=tk.W).pack(fill=tk.X)
            tk.Label(cuerpo_card, text=t2, font=("Consolas", 8),
                     fg=C["accent5"], bg=C["bg_card"], anchor=tk.W).pack(fill=tk.X)
            tk.Label(cuerpo_card, text=nota, font=("Segoe UI", 7),
                     fg=C["text_sub"], bg=C["bg_card"], anchor=tk.W).pack(fill=tk.X)

        # Separador
        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X, padx=10, pady=10)

        # Panel de resultados
        tk.Label(parent, text="ÚLTIMOS RESULTADOS", font=("Segoe UI", 9, "bold"),
                 fg=C["text_dim"], bg=C["bg_sidebar"],
                 anchor=tk.W).pack(fill=tk.X, padx=16, pady=(0, 6))

        frame_log = tk.Frame(parent, bg=C["bg_sidebar"])
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        sb = tk.Scrollbar(frame_log, bg=C["bg_card"])
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.txt_logs = tk.Text(frame_log, bg=C["bg_canvas"], fg=C["accent2"],
                                 font=("Consolas", 8), wrap=tk.WORD,
                                 bd=0, highlightthickness=1,
                                 highlightbackground=C["border"],
                                 yscrollcommand=sb.set,
                                 insertbackground=C["accent"],
                                 selectbackground=C["bg_card"])
        self.txt_logs.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.txt_logs.yview)

        # Resumen del grafo
        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X, padx=10, pady=4)
        resumen = tk.Frame(parent, bg=C["bg_sidebar"])
        resumen.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Label(resumen, text="RESUMEN DEL GRAFO", font=("Segoe UI", 8, "bold"),
                 fg=C["text_dim"], bg=C["bg_sidebar"],
                 anchor=tk.W).pack(fill=tk.X, pady=(4,2))
        for txt in [
            f"Nodos: {self.G.number_of_nodes()}",
            f"Aristas: {self.G.number_of_edges()}",
            f"Distancia máx: 2 500 m",
            f"Fórmula: Haversine (WGS84)",
        ]:
            tk.Label(resumen, text=txt, font=("Consolas", 8),
                     fg=C["text_sub"], bg=C["bg_sidebar"],
                     anchor=tk.W).pack(fill=tk.X)

        self._log("Sistema iniciado.\nSelecciona un módulo para ver resultados.")

    # ════════════════════════════════════════════════════════════
    #  MAPA
    # ════════════════════════════════════════════════════════════

    def _cargar_mapa_fondo(self):
        """Genera y carga la imagen de mapa de fondo en el canvas."""
        try:
            from PIL import Image, ImageTk
            from gui.mapa_cusco import generar_mapa

            ancho = self.canvas.winfo_width()  or 880
            alto  = self.canvas.winfo_height() or 660

            img = generar_mapa(ancho, alto)
            self._foto_mapa = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW,
                                      image=self._foto_mapa, tags="fondo")
            self.canvas.tag_lower("fondo")
        except Exception as e:
            # Si PIL falla, dibujamos fondo simple con cuadrícula
            self._dibujar_fondo_simple()

    def _dibujar_fondo_simple(self):
        """Fondo alternativo sin PIL."""
        ancho = self.canvas.winfo_width()  or 880
        alto  = self.canvas.winfo_height() or 660
        self.canvas.create_rectangle(0, 0, ancho, alto, fill=C["bg_canvas"], outline="")
        for xi in range(0, ancho, 40):
            self.canvas.create_line(xi, 0, xi, alto, fill="#161b22", width=1)
        for yi in range(0, alto, 40):
            self.canvas.create_line(0, yi, ancho, yi, fill="#161b22", width=1)

    def _coords(self, lat, lon):
        """Convierte lat/lon a píxeles en el canvas."""
        lats = [n["lat"] for n in self.nodos_datos]
        lons = [n["lon"] for n in self.nodos_datos]
        ancho = self.canvas.winfo_width()  or 880
        alto  = self.canvas.winfo_height() or 660
        mg = 70
        x = mg + (lon - min(lons)) / (max(lons) - min(lons)) * (ancho - mg*2)
        y = (alto - mg) - (lat - min(lats)) / (max(lats) - min(lats)) * (alto - mg*2)
        return int(x), int(y)

    def dibujar_grafo_base(self, conservar_fondo=False):
        """Dibuja el grafo sobre el mapa de fondo."""
        if not conservar_fondo:
            self.canvas.delete("grafo")
            self.canvas.delete("nodo")
            self.canvas.delete("etiqueta")
            self.canvas.delete("arista")
        else:
            self.canvas.delete("grafo")
            self.canvas.delete("nodo")
            self.canvas.delete("etiqueta")
            self.canvas.delete("arista")

        # Aristas
        for u, v, datos in self.G.edges(data=True):
            x1, y1 = self._coords(self.dicc_nodos[u]["lat"], self.dicc_nodos[u]["lon"])
            x2, y2 = self._coords(self.dicc_nodos[v]["lat"], self.dicc_nodos[v]["lon"])
            self.canvas.create_line(x1, y1, x2, y2, fill="#2d3748", width=1.5,
                                     smooth=True, tags="arista")
            # Distancia en la arista
            mx, my = (x1+x2)//2, (y1+y2)//2
            self.canvas.create_text(mx, my, text=f"{int(datos['peso'])}m",
                                     font=("Segoe UI", 6), fill="#4a5568", tags="arista")

        # Nodos
        for nodo in self.nodos_datos:
            self._dibujar_nodo(nodo, radio=7, color="#f39c12", tag="nodo")

    def _dibujar_nodo(self, nodo, radio=7, color="#f39c12", tag="nodo",
                       outline="white", outline_w=1.5, texto_color=C["text_main"]):
        x, y = self._coords(nodo["lat"], nodo["lon"])
        nid  = nodo["id"]

        # Halo exterior
        self.canvas.create_oval(x-radio-3, y-radio-3, x+radio+3, y+radio+3,
                                 fill="", outline=color, width=1,
                                 stipple="gray25", tags=tag)
        # Círculo principal
        self.canvas.create_oval(x-radio, y-radio, x+radio, y+radio,
                                 fill=color, outline=outline, width=outline_w,
                                 tags=(tag, f"nodo_{nid}"))
        # ID del nodo dentro
        self.canvas.create_text(x, y, text=str(nid),
                                 font=("Consolas", 6, "bold"),
                                 fill="black", tags=(tag, f"nodo_{nid}"))
        # Etiqueta exterior
        self.canvas.create_rectangle(x-30, y-radio-18, x+30, y-radio-6,
                                      fill="#0d1117cc" if True else "#0d1117",
                                      outline="", tags="etiqueta")
        self.canvas.create_text(x, y-radio-12,
                                 text=nodo["nombre"],
                                 font=("Segoe UI", 7, "bold"),
                                 fill=texto_color, tags="etiqueta")

    def _reset_mapa(self):
        self.modulo_activo = None
        for frame, ind, _ in self.btns_modulo:
            frame.config(bg=C["bg_sidebar"])
            self._bg_rec(frame, C["bg_sidebar"])
            ind.config(bg=C["bg_sidebar"])
        self.canvas.delete("all")
        self._cargar_mapa_fondo()
        self.dibujar_grafo_base()
        self.lbl_titulo_mapa.config(text="  📍  Grafo de Cusco — Nodos y Aristas")
        self.lbl_badge_mapa.config(text=" Estructura: Grafo Ponderado No Dirigido ",
                                    fg=C["accent2"], bg="#0d2818")
        self._log("Mapa reiniciado.")

    # ── Eventos del canvas ───────────────────────────────────────
    def _bind_canvas_eventos(self):
        self.canvas.bind("<Motion>", self._on_canvas_move)
        self.canvas.bind("<Leave>",  self._on_canvas_leave)

    def _on_canvas_move(self, event):
        x, y = event.x, event.y
        nodo_cercano = None
        dist_min = 18

        for nodo in self.nodos_datos:
            nx_, ny_ = self._coords(nodo["lat"], nodo["lon"])
            d = math.hypot(x - nx_, y - ny_)
            if d < dist_min:
                dist_min = d
                nodo_cercano = nodo

        if nodo_cercano and nodo_cercano != self.nodo_hover:
            self.nodo_hover = nodo_cercano
            n = nodo_cercano
            txt = (f"ID: {n['id']}  |  {n['nombre']}\n"
                   f"Zona: {n['zona']}  |  "
                   f"Lat: {n['lat']:.4f}  Lon: {n['lon']:.4f}\n"
                   f"Conexiones: {len(list(self.G.neighbors(n['id'])))}")
            self.tooltip.config(text=txt)
            self.tooltip.place(x=event.x_root - self.root.winfo_rootx() + 14,
                                y=event.y_root - self.root.winfo_rooty() + 14)
        elif not nodo_cercano:
            self.nodo_hover = None
            self.tooltip.place_forget()

    def _on_canvas_leave(self, e):
        self.nodo_hover = None
        self.tooltip.place_forget()

    # ════════════════════════════════════════════════════════════
    #  LOG
    # ════════════════════════════════════════════════════════════

    def _log(self, texto):
        self.txt_logs.config(state=tk.NORMAL)
        self.txt_logs.delete("1.0", tk.END)
        self.txt_logs.insert(tk.END, texto)
        self.txt_logs.see(tk.END)

    # ════════════════════════════════════════════════════════════
    #  DIBUJO UTILITARIOS
    # ════════════════════════════════════════════════════════════

    def _dibujar_arista_destacada(self, u, v, color, ancho=3, dash=None, flecha=None, tag="grafo"):
        x1, y1 = self._coords(self.dicc_nodos[u]["lat"], self.dicc_nodos[u]["lon"])
        x2, y2 = self._coords(self.dicc_nodos[v]["lat"], self.dicc_nodos[v]["lon"])
        kwargs = dict(fill=color, width=ancho, smooth=True, tags=tag)
        if dash:
            kwargs["dash"] = dash
        if flecha:
            kwargs["arrow"] = flecha
        self.canvas.create_line(x1, y1, x2, y2, **kwargs)

    def _dibujar_nodo_destacado(self, nodo_id, color, radio=10, tag="grafo"):
        nodo = self.dicc_nodos[nodo_id]
        x, y = self._coords(nodo["lat"], nodo["lon"])
        # Halo animado
        self.canvas.create_oval(x-radio-4, y-radio-4, x+radio+4, y+radio+4,
                                 fill="", outline=color, width=2, tags=tag)
        self.canvas.create_oval(x-radio, y-radio, x+radio, y+radio,
                                 fill=color, outline="white", width=2, tags=tag)
        self.canvas.create_text(x, y, text=str(nodo_id),
                                 font=("Consolas", 7, "bold"), fill="black", tags=tag)

    def _dibujar_camino(self, camino, color, ancho=3, tag="grafo"):
        for i in range(len(camino) - 1):
            self._dibujar_arista_destacada(camino[i], camino[i+1],
                                            color=color, ancho=ancho,
                                            flecha=tk.LAST, tag=tag)
        for nid in camino:
            self._dibujar_nodo_destacado(nid, color, tag=tag)

    def _titulo_modulo(self, texto, badge=None, badge_color=None, badge_bg=None):
        self.lbl_titulo_mapa.config(text=f"  {texto}")
        if badge:
            self.lbl_badge_mapa.config(
                text=f" {badge} ",
                fg=badge_color or C["accent"],
                bg=badge_bg or "#0a1f2e"
            )

    # ════════════════════════════════════════════════════════════
    #  MÓDULO 1 — ORDENAMIENTOS
    # ════════════════════════════════════════════════════════════

    def ejecutar_ordenamiento(self):
        pedidos = cargar_pedidos()
        t0 = time.perf_counter()
        op = gnome_sort_prioridad(pedidos)
        t1 = time.perf_counter()
        ope = comb_sot_peso(pedidos)
        t2 = time.perf_counter()
        ov = shell_sort_valor(pedidos)
        t3 = time.perf_counter()

        self.canvas.delete("grafo")
        self.dibujar_grafo_base()
        self._titulo_modulo("📦  Ordenamientos en Almacén",
                             "Gnome · Comb · Shell Sort",
                             C["mod_orden"], "#1a0a2e")

        # Resaltar nodos de los 5 pedidos más urgentes
        for i, p in enumerate(op[:5]):
            nid = p["origen"]
            if nid in self.dicc_nodos:
                intensidad = ["#8e44ad","#9b59b6","#a66bbe","#b17dcc","#bc8cff"][i]
                self._dibujar_nodo_destacado(nid, intensidad, radio=9+i, tag="grafo")

        t_gnome = round((t1-t0)*1000, 3)
        t_comb  = round((t2-t1)*1000, 3)
        t_shell = round((t3-t2)*1000, 3)

        txt  = "═══ MÓDULO 1: ORDENAMIENTOS ═══\n\n"
        txt += f"Total pedidos analizados: {len(pedidos)}\n\n"
        txt += f"① GNOME SORT — Por Prioridad\n"
        txt += f"   Complejidad: O(n²)\n"
        txt += f"   Tiempo real: {t_gnome} ms\n"
        txt += f"   [1=urgente → 3=puede esperar]\n"
        for p in op[:5]:
            txt += f"   #{p['id']:>2} {p['cliente']:<12} Prioridad {p['prioridad']}\n"
        txt += f"\n② COMB SORT — Por Peso\n"
        txt += f"   Complejidad: O(n²) / O(n log n) prom.\n"
        txt += f"   Tiempo real: {t_comb} ms\n"
        for p in ope[:5]:
            txt += f"   #{p['id']:>2} {p['cliente']:<12} {p['peso']} kg\n"
        txt += f"\n③ SHELL SORT — Por Valor\n"
        txt += f"   Complejidad: O(n log² n)\n"
        txt += f"   Tiempo real: {t_shell} ms\n"
        for p in ov[:5]:
            txt += f"   #{p['id']:>2} {p['cliente']:<12} S/. {p['valor']}\n"
        self._log(txt)

    # ════════════════════════════════════════════════════════════
    #  MÓDULO 2 — DIVIDE Y VENCERÁS
    # ════════════════════════════════════════════════════════════

    def ejecutar_divide_y_venceras(self):
        resultado = procesar_divide_y_venceras(self.G, num_repartidores=3)

        self.canvas.delete("grafo")
        self.dibujar_grafo_base()
        self._titulo_modulo("🗺  Zonificación — Divide y Vencerás",
                             f"Zonas: {resultado['num_zonas']} | Repartidores: 3",
                             C["mod_divide"], "#0a2010")

        # Colorear zonas con polígono de fondo semitransparente
        for idx, zona in enumerate(resultado["zonas"]):
            color = COLORES_ZONA[idx % len(COLORES_ZONA)]
            pts_poly = []
            for uid in zona:
                x, y = self._coords(self.dicc_nodos[uid]["lat"],
                                     self.dicc_nodos[uid]["lon"])
                pts_poly.extend([x, y])

            # Dibujar nodos de zona
            for uid in zona:
                x, y = self._coords(self.dicc_nodos[uid]["lat"],
                                     self.dicc_nodos[uid]["lon"])
                self.canvas.create_oval(x-10, y-10, x+10, y+10,
                                         fill=color, outline="white",
                                         width=1.5, tags="grafo")
                self.canvas.create_text(x, y, text=str(uid),
                                         font=("Consolas", 7, "bold"),
                                         fill="black", tags="grafo")

        # Rutas de cada repartidor
        for id_rep, datos in resultado["asignaciones"].items():
            ruta  = datos["ruta"]
            color = COLORES_ZONA[(id_rep - 1) % len(COLORES_ZONA)]
            for i in range(len(ruta) - 1):
                self._dibujar_arista_destacada(ruta[i], ruta[i+1],
                                                color=color, ancho=2,
                                                dash=(8, 4), flecha=tk.LAST)

        txt  = "═══ MÓDULO 2: DIVIDE Y VENCERÁS ═══\n\n"
        txt += f"Algoritmo: {resultado['algoritmo']}\n"
        txt += f"Complejidad: {resultado['complejidad']}\n"
        txt += f"Tiempo: {resultado['tiempo_ms']} ms\n"
        txt += f"Zonas generadas: {resultado['num_zonas']}\n\n"
        txt += "Estrategia: dividir por eje de mayor\n"
        txt += "extensión geográfica (lon o lat).\n\n"
        for rep, datos in resultado["asignaciones"].items():
            nombres = [self.dicc_nodos[uid]["nombre"] for uid in datos["ruta"]]
            color_n = ["Verde","Naranja","Violeta","Azul"][rep-1]
            txt += f"Rep {rep} ({color_n}):\n"
            txt += f"  Nodos: {len(datos['ruta'])}\n"
            txt += f"  Dist: {datos['distancia_m']} m\n"
            for n in nombres:
                txt += f"  → {n}\n"
            txt += "\n"
        self._log(txt)

    # ════════════════════════════════════════════════════════════
    #  MÓDULO 3 — BACKTRACKING
    # ════════════════════════════════════════════════════════════

    def ejecutar_backtracking(self):
        calles_bloqueadas = [[1, 3]]
        resultado = backtracking_rutas_con_restricciones(
            self.G, inicio=3, destino=9,
            aristas_bloqueadas=calles_bloqueadas, max_rutas=5
        )

        self.canvas.delete("grafo")
        self.dibujar_grafo_base()
        self._titulo_modulo("🚧  Contingencia Vial — Backtracking",
                             f"Rutas halladas: {resultado['total_rutas']}",
                             C["mod_back"], "#2a0a0a")

        # Arista bloqueada
        self._dibujar_arista_destacada(1, 3, color=C["accent4"],
                                        ancho=4, dash=(5, 4), tag="grafo")
        x1, y1 = self._coords(self.dicc_nodos[1]["lat"], self.dicc_nodos[1]["lon"])
        x2, y2 = self._coords(self.dicc_nodos[3]["lat"], self.dicc_nodos[3]["lon"])
        self.canvas.create_text((x1+x2)//2, (y1+y2)//2 - 14,
                                 text="⛔ BLOQUEADO",
                                 font=("Segoe UI", 8, "bold"),
                                 fill=C["accent4"], tags="grafo")

        # Rutas alternativas (gris)
        for r in resultado["rutas"][1:]:
            for i in range(len(r["camino"]) - 1):
                self._dibujar_arista_destacada(r["camino"][i], r["camino"][i+1],
                                                color="#4a5568", ancho=1,
                                                dash=(3, 3), tag="grafo")

        # Mejor ruta (rojo)
        if resultado["mejor_ruta"]:
            camino = resultado["mejor_ruta"]["camino"]
            self._dibujar_camino(camino, color=C["accent4"], ancho=3)

            # Nodo inicio (verde) y destino (azul)
            self._dibujar_nodo_destacado(camino[0],  C["accent2"], radio=11, tag="grafo")
            self._dibujar_nodo_destacado(camino[-1], C["accent"],  radio=11, tag="grafo")

        txt  = "═══ MÓDULO 3: BACKTRACKING VIAL ═══\n\n"
        txt += f"Algoritmo: {resultado['algoritmo']}\n"
        txt += f"Complejidad: {resultado['complejidad']}\n"
        txt += f"Nodos evaluados: {resultado['nodos_explorados']}\n"
        txt += f"Tiempo: {resultado['tiempo_ms']} ms\n\n"
        txt += "Tramo ⛔: Plaza de Armas ↔ San Blas\n"
        txt += "Origen  : San Blas (ID 3)\n"
        txt += "Destino : Wanchaq (ID 9)\n\n"
        if resultado["mejor_ruta"]:
            camino = resultado["mejor_ruta"]["camino"]
            txt += f"Rutas alternativas: {resultado['total_rutas']}\n\n"
            txt += "MEJOR RUTA:\n"
            for uid in camino:
                txt += f"  → {self.dicc_nodos[uid]['nombre']}\n"
            txt += f"\nDistancia: {resultado['mejor_ruta']['distancia_m']} m\n\n"
            txt += "TODAS LAS RUTAS:\n"
            for i, r in enumerate(resultado["rutas"]):
                ns = [self.dicc_nodos[u]["nombre"] for u in r["camino"]]
                txt += f"{i+1}. {' → '.join(ns)}\n   ({r['distancia_m']} m)\n"
        self._log(txt)

    # ════════════════════════════════════════════════════════════
    #  MÓDULO 4 — MOCHILA DP
    # ════════════════════════════════════════════════════════════

    def ejecutar_mochila(self):
        pedidos = cargar_pedidos()
        limite  = 15.0
        resultado = optimizar_carga_mochila(pedidos, limite)

        self.canvas.delete("grafo")
        self.dibujar_grafo_base()
        self._titulo_modulo("⚖  Optimización de Carga — Mochila DP",
                             f"Valor máx: S/. {resultado['valor_maximo']}",
                             C["mod_dp"], "#0a1830")

        # Resaltar orígenes de pedidos seleccionados
        for i, p in enumerate(resultado["pedidos_incluidos"]):
            nid = p["origen"]
            if nid in self.dicc_nodos:
                self._dibujar_nodo_destacado(nid, C["mod_dp"], radio=10, tag="grafo")
                x, y = self._coords(self.dicc_nodos[nid]["lat"],
                                     self.dicc_nodos[nid]["lon"])
                self.canvas.create_text(x, y+18, text=f"S/.{p['valor']}",
                                         font=("Consolas", 7), fill=C["accent"],
                                         tags="grafo")

        txt  = "═══ MÓDULO 4: MOCHILA (KNAPSACK 0/1) ═══\n\n"
        txt += f"Algoritmo: {resultado['algoritmo']}\n"
        txt += f"Complejidad: {resultado['complejidad']}\n"
        txt += f"Tiempo: {resultado['tiempo_ms']} ms\n\n"
        txt += f"Capacidad : {limite} kg\n"
        txt += f"Disponibles: {len(pedidos)} pedidos\n"
        txt += f"Seleccionados: {len(resultado['pedidos_incluidos'])}\n\n"
        txt += f"► Valor máximo: S/. {resultado['valor_maximo']}\n"
        txt += f"► Peso cargado: {resultado['peso_total']} kg\n\n"
        txt += "PEDIDOS EN EL VEHÍCULO:\n"
        for p in resultado["pedidos_incluidos"]:
            txt += f"  ✓ #{p['id']:>2} {p['cliente']:<12} {p['peso']}kg  S/.{p['valor']}\n"
        self._log(txt)

    # ════════════════════════════════════════════════════════════
    #  MÓDULO 5 — GREEDY
    # ════════════════════════════════════════════════════════════

    def ejecutar_greedy(self):
        from algoritmos.greedy import greedy_pedido_mas_cercano, greedy_repartidor_mas_cercano

        pedidos = cargar_pedidos()
        plaza   = self.dicc_nodos[1]
        t0 = time.perf_counter()
        ruta = greedy_pedido_mas_cercano(plaza["lat"], plaza["lon"],
                                          pedidos[:8], self.nodos_datos)
        t1 = time.perf_counter()

        repartidores = [
            {"nombre": "Repartidor 1", "lat": -13.5170, "lon": -71.9787},
            {"nombre": "Repartidor 2", "lat": -13.5300, "lon": -71.9600},
            {"nombre": "Repartidor 3", "lat": -13.5250, "lon": -71.9820},
        ]
        ped_urgente = next(p for p in pedidos if p["prioridad"] == 1)
        rep_asig, dist_rep = greedy_repartidor_mas_cercano(
            ped_urgente, repartidores, self.nodos_datos)

        self.canvas.delete("grafo")
        self.dibujar_grafo_base()
        self._titulo_modulo("⚡  Algoritmo Greedy — Vecino más Cercano",
                             "Estrategia local óptima", C["mod_greedy"], "#1e1000")

        # Dibujar ruta greedy sobre el mapa
        ids_visitados = []
        for p in ruta:
            if p["origen"] not in ids_visitados:
                ids_visitados.append(p["origen"])
            if p["destino"] not in ids_visitados:
                ids_visitados.append(p["destino"])

        for i in range(len(ids_visitados) - 1):
            if ids_visitados[i] in self.dicc_nodos and ids_visitados[i+1] in self.dicc_nodos:
                self._dibujar_arista_destacada(ids_visitados[i], ids_visitados[i+1],
                                                color=C["mod_greedy"], ancho=2,
                                                dash=(6, 3), flecha=tk.LAST, tag="grafo")

        for i, nid in enumerate(ids_visitados):
            if nid in self.dicc_nodos:
                self._dibujar_nodo_destacado(nid, C["mod_greedy"], radio=9, tag="grafo")
                x, y = self._coords(self.dicc_nodos[nid]["lat"],
                                     self.dicc_nodos[nid]["lon"])
                self.canvas.create_text(x+14, y-14, text=str(i+1),
                                         font=("Consolas", 7, "bold"),
                                         fill=C["mod_greedy"], tags="grafo")

        t_ms = round((t1-t0)*1000, 3)
        txt  = "═══ MÓDULO 5: GREEDY ═══\n\n"
        txt += "Estrategia: pedido más cercano primero\n"
        txt += "Complejidad: O(n²)\n"
        txt += f"Tiempo real: {t_ms} ms\n\n"
        txt += "RUTA DESDE PLAZA DE ARMAS:\n"
        for i, p in enumerate(ruta):
            txt += f"  {i+1}. #{p['id']:>2} {p['cliente']:<12} Prior.{p['prioridad']}\n"
        txt += f"\nASIGNACIÓN URGENTE:\n"
        txt += f"  Pedido: #{ped_urgente['id']} {ped_urgente['cliente']}\n"
        txt += f"  Asignado a: {rep_asig['nombre']}\n"
        txt += f"  Distancia: {dist_rep:.1f} m\n"
        self._log(txt)
