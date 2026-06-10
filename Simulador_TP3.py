"""
Simulador de Políticas Públicas - Economía para Ingenieros 2026
UNSTA · TP3
Alumnas: Abregú Candela · Amin Guadalupe · Pasteris Luciana
Prof. Raúl García

Intervenciones: SUBSIDIO y PRECIO MÁXIMO
Cálculo de excedentes, bienestar y variación social
"""

import io
import datetime
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Configuración de fuentes multiplataforma
import sys
if sys.platform == "win32":
    plt.rcParams['font.family'] = 'Segoe UI Symbol'
else:
    plt.rcParams['font.family'] = 'DejaVu Sans'

import streamlit as st

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image as RLImage, PageBreak,
)

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Simulador de Políticas Públicas - UNSTA",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.stApp { background-color: #f0f2f6; }
.block-container {
    background: #ffffff;
    border-radius: 12px;
    padding: 1.4rem 2rem 2rem 2rem !important;
    box-shadow: 0 2px 16px rgba(30,50,100,0.07);
}
[data-testid="stSidebar"] {
    background: #1e2a45 !important;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio label { color: #cbd5e1 !important; }
[data-testid="stSidebar"] input {
    background: #2d3f63 !important;
    color: #f1f5f9 !important;
    border: 1px solid #3b547a !important;
}
[data-testid="metric-container"] {
    background: #f8faff;
    border: 1px solid #dbeafe;
    border-radius: 10px;
    padding: 10px 14px;
}
.stTabs [data-baseweb="tab-list"] {
    background: #f1f5f9;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 6px 16px;
}
.stTabs [aria-selected="true"] {
    background: #2563eb !important;
    color: white !important;
}
.mod-header {
    background: linear-gradient(90deg,#1e3a8a 0%,#2563eb 100%);
    color: white !important;
    padding: 7px 18px;
    border-radius: 8px;
    margin: 18px 0 10px 0;
    font-size: 1.1rem;
    font-weight: 700;
}
.caja-info {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
}
.caja-warn {
    background: #fffbeb;
    border-left: 4px solid #f59e0b;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
}
.caja-success {
    background: #f0fdf4;
    border-left: 4px solid #22c55e;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════
st.title("🏛️ Simulador de Políticas Públicas")
st.markdown("**UNSTA · Economía para Ingenieros · Trabajo Práctico N°2**")
st.markdown("**Alumnas**: Abregú Candela · Amin Guadalupe · Pasteris Luciana | **Prof.** Raúl García")
st.markdown("*Políticas públicas bajo economía cerrada: Subsidio y Precio Máximo*")
st.divider()

# ══════════════════════════════════════════════════════════════════
# PALETA DE COLORES
# ══════════════════════════════════════════════════════════════════
COLOR_DEMANDA  = '#1a56db'
COLOR_OFERTA   = '#057a55'
COLOR_EQ       = '#e02424'
COLOR_NUEVO_EQ = '#7e3af2'
COLOR_ESCASEZ  = '#f59e0b'
COLOR_PERDIDA  = '#ef4444'
COLOR_GRIS     = '#9ca3af'
COLOR_EXCEDENTE = '#10b981'
COLOR_CS       = '#60a5fa'   # Azul claro para excedente consumidor
COLOR_PS       = '#34d399'   # Verde claro para excedente productor
COLOR_SUBSIDIO = '#f59e0b'   # Naranja para subsidio
COLOR_DWL      = '#ef4444'   # Rojo para pérdida social

# ══════════════════════════════════════════════════════════════════
# FUNCIONES ECONÓMICAS BASE
# ══════════════════════════════════════════════════════════════════

def validar_demanda(a, b):
    errs = []
    if b <= 0:
        errs.append("❌ La pendiente de demanda debe ser POSITIVA (Qd = a − b·P, con b > 0)")
    if a <= 0:
        errs.append("❌ El intercepto (a) debe ser positivo para que exista demanda a precio cero")
    return errs

def validar_oferta(c, d):
    errs = []
    if d <= 0:
        errs.append("❌ La pendiente de oferta debe ser POSITIVA (Qo = c + d·P, con d > 0)")
    return errs

def equilibrio(a, b, c, d):
    """Calcula precio y cantidad de equilibrio"""
    if b + d == 0:
        return None, None
    P = (a - c) / (b + d)
    Q = a - b * P
    if P < 0 or Q < 0:
        return None, None
    return P, Q

def precio_maximo_demanda(a, b):
    """Precio al cual la cantidad demandada es cero (P_max)"""
    if b == 0:
        return None
    return a / b

def precio_minimo_oferta(c, d):
    """Precio al cual la cantidad ofrecida es cero (P_min)"""
    if d == 0:
        return None
    # Si c >= 0, la oferta empieza en P=0 con Q=c
    # Si c < 0, la oferta empieza en P = -c/d
    if c >= 0:
        return 0
    else:
        return -c / d

def excedente_consumidor(a, b, P_eq, Q_eq):
    """CS = (P_max - P_eq) * Q_eq / 2"""
    P_max = precio_maximo_demanda(a, b)
    if P_max is None or P_eq >= P_max:
        return 0
    return (P_max - P_eq) * Q_eq / 2

def excedente_productor(c, d, P_eq, Q_eq):
    """PS = (P_eq - P_min) * Q_eq / 2"""
    P_min = precio_minimo_oferta(c, d)
    if P_min is None or P_eq <= P_min:
        return 0
    return (P_eq - P_min) * Q_eq / 2

def bienestar_total(CS, PS):
    return CS + PS

def rango_precios(a, b, P_eq, margen=0.35):
    """Genera rango de precios para graficar"""
    P_max_curva = a / b if b > 0 else P_eq * 2
    P_top = max(P_max_curva, P_eq) * (1 + margen)
    if P_top <= 0:
        P_top = 100.0
    return np.linspace(0, P_top, 300)


# ══════════════════════════════════════════════════════════════════
# GRÁFICOS
# ══════════════════════════════════════════════════════════════════

def _estilo_base(ax, titulo):
    ax.set_xlabel('Cantidad (Q)', fontsize=11, color='#374151')
    ax.set_ylabel('Precio (P)', fontsize=11, color='#374151')
    ax.set_title(titulo, fontsize=13, fontweight='bold', color='#111827', pad=10)
    ax.grid(True, alpha=0.25, linestyle='--', color='#d1d5db')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.tick_params(labelsize=9, colors='#374151')


def graficar_mercado_inicial(a, b, c, d, P_eq, Q_eq, CS, PS):
    """Gráfico del mercado con excedentes sombreados (sólidos)"""
    fig, ax = plt.subplots(figsize=(10, 6))
    Pr = rango_precios(a, b, P_eq)
    
    Qd = np.maximum(a - b * Pr, 0)
    Qo = np.maximum(c + d * Pr, 0)
    
    mask_d = Qd > 0
    mask_o = Qo > 0
    
    ax.plot(Qd[mask_d], Pr[mask_d], color=COLOR_DEMANDA, lw=2.5, label='Demanda: Qd = a − b·P')
    ax.plot(Qo[mask_o], Pr[mask_o], color=COLOR_OFERTA, lw=2.5, label='Oferta: Qo = c + d·P')
    
    # Excedente del consumidor (triángulo sobre P* hasta demanda)
    P_max_dem = precio_maximo_demanda(a, b)
    if P_max_dem and P_eq < P_max_dem and Q_eq > 0:
        P_grid = np.linspace(P_eq, P_max_dem, 50)
        Q_grid = a - b * P_grid
        ax.fill_betweenx(P_grid, 0, Q_grid, alpha=0.35, color=COLOR_CS, 
                         label=f'Excedente Consumidor = ${CS:,.0f}')
    
    # Excedente del productor (triángulo debajo de P* hasta oferta)
    P_min_of = precio_minimo_oferta(c, d)
    if P_min_of is not None and P_eq > P_min_of and Q_eq > 0:
        # Construir la curva de oferta desde P_min_of hasta P_eq
        P_grid_p = np.linspace(P_min_of, P_eq, 50)
        Q_grid_p = np.maximum(c + d * P_grid_p, 0)
        ax.fill_betweenx(P_grid_p, 0, Q_grid_p, alpha=0.35, color=COLOR_PS,
                         label=f'Excedente Productor = ${PS:,.0f}')
    
    # Punto de equilibrio
    ax.plot(Q_eq, P_eq, 'o', color=COLOR_EQ, ms=10, zorder=5, 
            label=f'Equilibrio (P*={P_eq:.2f}, Q*={Q_eq:.0f})')
    ax.axhline(P_eq, linestyle=':', alpha=0.5, color=COLOR_GRIS, linewidth=1)
    ax.axvline(Q_eq, linestyle=':', alpha=0.5, color=COLOR_GRIS, linewidth=1)
    
    _estilo_base(ax, "Mercado Competitivo - Excedentes")
    ax.legend(loc='upper right', fontsize=9, framealpha=0.92)
    fig.tight_layout()
    return fig

def graficar_subsidio(a, b, c, d, P_eq, Q_eq, s, Pc, Pv, Qs, 
                      CS_orig, PS_orig, CS_new, PS_new, gasto_fiscal, variacion):
    """
    Gráfico del subsidio:
    - Excedentes como áreas sólidas
    - Costo fiscal como hatch '---' sin fondo
    - Pérdida social (DWL) como triángulo hatch '///' sin fondo
    - Leyenda en 1 columna para mostrar todos los elementos
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    Pr = rango_precios(a, b, P_eq, margen=0.45)
    
    Qd = np.maximum(a - b * Pr, 0)
    Qo_orig = np.maximum(c + d * Pr, 0)
    Qo_sub = np.maximum(c + d * (Pr + s), 0)
    
    mask_d = Qd > 0
    mask_o = Qo_orig > 0
    mask_sub = Qo_sub > 0
    
    # Curvas
    ax.plot(Qd[mask_d], Pr[mask_d], color=COLOR_DEMANDA, lw=2.5, label='Demanda')
    ax.plot(Qo_orig[mask_o], Pr[mask_o], color=COLOR_OFERTA, lw=2.5, label='Oferta original')
    ax.plot(Qo_sub[mask_sub], Pr[mask_sub], color=COLOR_SUBSIDIO, lw=2.5, linestyle='--', 
            label=f'Oferta con subsidio (s = ${s:.2f})')
    
    # Punto de equilibrio original
    ax.plot(Q_eq, P_eq, 'o', color=COLOR_EQ, ms=8, zorder=5, label='Equilibrio original')
    ax.axhline(P_eq, linestyle=':', alpha=0.5, color=COLOR_GRIS, lw=1)
    ax.axvline(Q_eq, linestyle=':', alpha=0.5, color=COLOR_GRIS, lw=1)
    
    # Puntos con subsidio
    ax.plot(Qs, Pc, 'o', color=COLOR_NUEVO_EQ, ms=9, zorder=6, 
            label=f'Nuevo equilibrio (Pc={Pc:.2f}, Q={Qs:.0f})')
    ax.plot(Qs, Pv, 'o', color='#0e7c5e', ms=7, zorder=5, alpha=0.7)
    ax.axhline(Pc, linestyle=':', alpha=0.4, color=COLOR_GRIS, lw=1)
    ax.axvline(Qs, linestyle=':', alpha=0.4, color=COLOR_GRIS, lw=1)
    
    # ========== EXCEDENTES ==========
    P_max_dem = precio_maximo_demanda(a, b)
    if P_max_dem and Pc < P_max_dem and Qs > 0:
        P_grid_cs = np.linspace(Pc, P_max_dem, 50)
        Q_grid_cs = a - b * P_grid_cs
        ax.fill_betweenx(P_grid_cs, 0, Q_grid_cs, alpha=0.35, color=COLOR_CS,
                         label=f'Excedente Consumidor = ${CS_new:,.0f}')
    
    P_min_of = precio_minimo_oferta(c, d)
    if P_min_of is not None and Pv > P_min_of and Qs > 0:
        P_grid_ps = np.linspace(P_min_of, Pv, 50)
        Q_grid_ps = np.maximum(c + d * P_grid_ps, 0)
        ax.fill_betweenx(P_grid_ps, 0, Q_grid_ps, alpha=0.35, color=COLOR_PS,
                         label=f'Excedente Productor = ${PS_new:,.0f}')
    
    # ========== COSTO FISCAL ==========
    if Pv > Pc:
        rect = mpatches.Rectangle((0, Pc), Qs, Pv - Pc, 
                                   facecolor='none', 
                                   edgecolor=COLOR_SUBSIDIO,
                                   hatch='---', 
                                   linewidth=1.5,
                                   alpha=0.9)
        ax.add_patch(rect)
    
    # ========== PÉRDIDA SOCIAL (DWL) ==========
    dwl_valor = 0
    if Qs > Q_eq:
        Po_Qs = (Qs - c) / d if d > 0 else 0
        vertices = np.array([[Q_eq, P_eq], [Qs, Pc], [Qs, Po_Qs]])
        polygon = mpatches.Polygon(vertices, closed=True, 
                                    facecolor='none', 
                                    edgecolor='red',
                                    hatch='///',
                                    linewidth=2.0,
                                    alpha=0.9)
        ax.add_patch(polygon)
        dwl_valor = 0.5 * (Qs - Q_eq) * (P_eq - Po_Qs)
    
    # ========== LEYENDA: 1 COLUMNA (para que entren todos los elementos) ==========
    # Obtener handles y labels existentes
    handles, labels = ax.get_legend_handles_labels()
    
    # Agregar entradas para Costo Fiscal y DWL
    if Pv > Pc:
        # Crear proxy para costo fiscal
        costo_proxy = mpatches.Rectangle((0, 0), 1, 1, 
                                          facecolor='none', 
                                          edgecolor=COLOR_SUBSIDIO,
                                          hatch='---',
                                          linewidth=1.5)
        handles.append(costo_proxy)
        labels.append(f'Costo Fiscal = ${gasto_fiscal:,.0f}')
    
    if Qs > Q_eq:
        # Crear proxy para DWL
        dwl_proxy = mpatches.Polygon([[0,0], [1,0], [0.5,1]], 
                                      facecolor='none', 
                                      edgecolor='red',
                                      hatch='///',
                                      linewidth=2.0)
        handles.append(dwl_proxy)
        labels.append(f'Pérdida Social = ${dwl_valor:,.0f}')
    
    # Leyenda en UNA SOLA COLUMNA - así entran todos los elementos
    ax.legend(handles, labels, loc='upper right', fontsize=8, 
              framealpha=0.92, ncol=1,  # ← CAMBIADO a 1 columna
              handlelength=2.0)
    
    # Flecha del subsidio
    ax.annotate('', xy=(Qs * 0.25, Pc), xytext=(Qs * 0.25, Pv),
                arrowprops=dict(arrowstyle='<->', color='#000000', lw=2))
    ax.text(Qs * 0.22, (Pc + Pv)/2, f's = ${s:.2f}', 
            ha='right', va='center', fontsize=10, fontweight='bold')
    
    _estilo_base(ax, f"Subsidio por unidad (s = ${s:.2f})")
    fig.tight_layout()
    return fig

def graficar_precio_maximo(a, b, c, d, P_eq, Q_eq, P_max, Qd_pmax, Qo_pmax, 
                           escasez, efectivo, CS_orig, PS_orig, CS_new, PS_new, 
                           perdida_social, CS_polygon_points=None):
    """
    Gráfico de precio máximo:
    - Excedentes como áreas sólidas
    - Excedente del consumidor: polígono sobre P_max, entre oferta y demanda
    - Pérdida social como hatch '///' en leyenda (sin texto flotante)
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    Pr = rango_precios(a, b, P_eq, margen=0.35)
    
    Qd = np.maximum(a - b * Pr, 0)
    Qo = np.maximum(c + d * Pr, 0)
    
    mask_d = Qd > 0
    mask_o = Qo > 0
    
    ax.plot(Qd[mask_d], Pr[mask_d], color=COLOR_DEMANDA, lw=2.5, label='Demanda')
    ax.plot(Qo[mask_o], Pr[mask_o], color=COLOR_OFERTA, lw=2.5, label='Oferta')
    
    # Equilibrio original
    ax.plot(Q_eq, P_eq, 'o', color=COLOR_EQ, ms=8, zorder=5, 
            label=f'Equilibrio original (P*={P_eq:.2f})')
    ax.axhline(P_eq, linestyle=':', alpha=0.5, color=COLOR_GRIS, lw=1)
    ax.axvline(Q_eq, linestyle=':', alpha=0.5, color=COLOR_GRIS, lw=1)
    
    if efectivo:
        Q_transada = Qo_pmax
        
        # Línea del precio máximo
        ax.axhline(P_max, color=COLOR_PERDIDA, lw=2.5, label=f'Precio Máximo = ${P_max:.2f}')
        ax.plot(Qd_pmax, P_max, 's', color=COLOR_DEMANDA, ms=8, zorder=5, 
                label=f'Qd = {Qd_pmax:.0f}')
        ax.plot(Qo_pmax, P_max, 's', color=COLOR_OFERTA, ms=8, zorder=5, 
                label=f'Qo = {Qo_pmax:.0f}')
        
        # Área de escasez
        if escasez > 0:
            ax.axvspan(Qo_pmax, Qd_pmax, alpha=0.25, color=COLOR_ESCASEZ, 
                       label=f'Escasez = {escasez:.0f} unidades')
        
        # ========== EXCEDENTE DEL CONSUMIDOR ==========
        # Polígono sobre P_max, entre la curva de demanda y la cantidad transada (Qo_pmax)
        # El excedente del consumidor con precio máximo es el área BAJO la demanda
        # y SOBRE el precio máximo, desde Q=0 hasta Q=Qo_pmax
        
        if Q_transada > 0 and b > 0:
            # Puntos para el polígono:
            # 1. (0, P_max) - origen en precio máximo
            # 2. (0, P_demanda_en_0) - pero la demanda en Q=0 es P_max_demanda
            # Mejor: construir polígono desde (0, P_max) siguiendo la demanda hasta (Q_transada, P_demanda_en_Qtrans)
            # y luego volver a (Q_transada, P_max)
            
            # Precio en la demanda para Q_transada
            P_demanda_Qtrans = (a - Q_transada) / b if b > 0 else P_max
            
            if P_demanda_Qtrans > P_max:
                # Crear puntos a lo largo de la curva de demanda desde Q=0 hasta Q_transada
                Q_curve = np.linspace(0, Q_transada, 100)
                P_curve = (a - Q_curve) / b
                
                # Rellenar el área entre P_max y la curva de demanda
                ax.fill_between(Q_curve, P_max, P_curve, 
                                where=(P_curve >= P_max),
                                alpha=0.35, color=COLOR_CS,
                                label=f'Excedente Consumidor = ${CS_new:,.0f}')
        
        # ========== EXCEDENTE DEL PRODUCTOR ==========
        # Área bajo P_max y sobre la oferta, desde Q=0 hasta Q_transada
        if Q_transada > 0 and d > 0:
            P_min_of = precio_minimo_oferta(c, d)
            if P_min_of is None:
                P_min_of = 0
            
            # Construir curva de oferta desde Q=0 hasta Q_transada
            Q_ps_curve = np.linspace(0, Q_transada, 100)
            P_ps_curve = (Q_ps_curve - c) / d if d > 0 else np.zeros_like(Q_ps_curve)
            P_ps_curve = np.maximum(P_ps_curve, P_min_of)
            
            # Rellenar área sobre la oferta y bajo P_max
            ax.fill_between(Q_ps_curve, P_ps_curve, P_max,
                            where=(P_ps_curve <= P_max),
                            alpha=0.35, color=COLOR_PS,
                            label=f'Excedente Productor = ${PS_new:,.0f}')
        
        # ========== PÉRDIDA SOCIAL (DWL) ==========
        # Triángulo entre oferta y demanda, desde Q_transada hasta Q_eq
        if Q_transada < Q_eq and Q_transada > 0:
            Pd_Qtrans = (a - Q_transada) / b if b > 0 else P_max
            Po_Qtrans = (Q_transada - c) / d if d > 0 else P_max
            
            vertices = np.array([[Q_transada, Po_Qtrans], 
                                 [Q_transada, Pd_Qtrans], 
                                 [Q_eq, P_eq]])
            polygon = mpatches.Polygon(vertices, closed=True, 
                                        facecolor='none', 
                                        edgecolor='red',
                                        hatch='///',
                                        linewidth=2.0,
                                        alpha=0.9)
            ax.add_patch(polygon)
        
        titulo = f"Precio Máximo EFECTIVO - Escasez de {escasez:.0f} unidades"
    else:
        # Precio máximo no efectivo
        ax.axhline(P_max, color=COLOR_GRIS, lw=2, linestyle='--', 
                   label=f'Precio Máximo = ${P_max:.2f} (no efectivo)')
        titulo = "Precio Máximo NO EFECTIVO (por encima del equilibrio)"
    
    # ========== LEYENDA (CONSTRUCCIÓN MANUAL) ==========
    from matplotlib.patches import Patch, Rectangle
    from matplotlib.lines import Line2D
    
    handles = []
    labels = []
    
    # Elementos base
    handles.append(Patch(facecolor=COLOR_DEMANDA, edgecolor=COLOR_DEMANDA, lw=2.5))
    labels.append('Demanda')
    
    handles.append(Patch(facecolor=COLOR_OFERTA, edgecolor=COLOR_OFERTA, lw=2.5))
    labels.append('Oferta')
    
    handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor=COLOR_EQ, markersize=8))
    labels.append(f'Equilibrio original (P*={P_eq:.2f})')
    
    if efectivo:
        handles.append(Line2D([0], [0], color=COLOR_PERDIDA, lw=2.5))
        labels.append(f'Precio Máximo = ${P_max:.2f}')
        
        handles.append(Line2D([0], [0], marker='s', color='w', markerfacecolor=COLOR_DEMANDA, markersize=8))
        labels.append(f'Qd = {Qd_pmax:.0f}')
        
        handles.append(Line2D([0], [0], marker='s', color='w', markerfacecolor=COLOR_OFERTA, markersize=8))
        labels.append(f'Qo = {Qo_pmax:.0f}')
        
        if escasez > 0:
            handles.append(Patch(facecolor=COLOR_ESCASEZ, alpha=0.25, edgecolor='none'))
            labels.append(f'Escasez = {escasez:.0f} unidades')
        
        # Excedentes
        handles.append(Patch(facecolor=COLOR_CS, alpha=0.35, edgecolor='none'))
        labels.append(f'Excedente Consumidor = ${CS_new:,.0f}')
        
        handles.append(Patch(facecolor=COLOR_PS, alpha=0.35, edgecolor='none'))
        labels.append(f'Excedente Productor = ${PS_new:,.0f}')
        
        # Pérdida Social (DWL) - solo en leyenda, sin texto flotante
        if perdida_social > 0 and Qo_pmax < Q_eq:
            handles.append(Rectangle((0,0), 1, 1, facecolor='none', edgecolor='red', hatch='///', lw=2))
            labels.append(f'Pérdida Social (DWL) = ${perdida_social:,.0f}')
    
    # Leyenda
    ncol_legend = 2 if len(handles) <= 8 else 1
    ax.legend(handles, labels, loc='upper right', fontsize=8, 
              framealpha=0.92, ncol=ncol_legend, handlelength=2.0)
    
    _estilo_base(ax, titulo)
    fig.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════════════
# SIDEBAR: INGRESO DE DATOS DEL MERCADO
# ══════════════════════════════════════════════════════════════════

st.sidebar.header("📊 Parámetros del Mercado")

# Demanda
st.sidebar.subheader("📉 Demanda: Qd = a − b·P")
a = st.sidebar.number_input("a (intercepto demanda)", value=1500.0, step=50.0, format="%.2f", key="a_dem")
b = st.sidebar.number_input("b (pendiente, b > 0)", value=25.0, step=5.0, min_value=0.1, format="%.2f", key="b_dem")

# Oferta
st.sidebar.subheader("📈 Oferta: Qo = c + d·P")
c = st.sidebar.number_input("c (intercepto oferta)", value=0.0, step=10.0, format="%.2f", key="c_of")
d = st.sidebar.number_input("d (pendiente, d > 0)", value=15.0, step=5.0, min_value=0.1, format="%.2f", key="d_of")

# Validaciones
errores = []
errores.extend(validar_demanda(a, b))
errores.extend(validar_oferta(c, d))

if errores:
    for err in errores:
        st.sidebar.error(err)
    st.stop()

# Mostrar ecuaciones
st.sidebar.divider()
st.sidebar.success(f"✅ Qd = {a:.2f} − {b:.2f}·P")
if c >= 0:
    st.sidebar.success(f"✅ Qo = {c:.2f} + {d:.2f}·P")
else:
    st.sidebar.success(f"✅ Qo = {c:.2f} + {d:.2f}·P (comienza en P = {-c/d:.2f})")

# Calcular equilibrio
P_eq, Q_eq = equilibrio(a, b, c, d)

if P_eq is None or Q_eq is None or Q_eq <= 0 or P_eq <= 0:
    st.error("⚠️ Las curvas no se intersectan en el primer cuadrante (P>0, Q>0).")
    st.info("💡 Sugerencia: Asegurate que a > c y que los parámetros sean positivos.")
    st.stop()

# Excedentes iniciales
CS_inicial = excedente_consumidor(a, b, P_eq, Q_eq)
PS_inicial = excedente_productor(c, d, P_eq, Q_eq)
WT_inicial = bienestar_total(CS_inicial, PS_inicial)

# Mostrar P_min y P_max informativos
P_max_dem = precio_maximo_demanda(a, b)
P_min_of = precio_minimo_oferta(c, d)
if P_max_dem:
    st.sidebar.caption(f"Precio máximo demanda: ${P_max_dem:.2f}")
if P_min_of:
    st.sidebar.caption(f"Precio mínimo oferta: ${P_min_of:.2f}")

# ══════════════════════════════════════════════════════════════════
# MÓDULO 1: MERCADO COMPETITIVO
# ══════════════════════════════════════════════════════════════════

st.markdown('<div class="mod-header">📊 Módulo 1 — Mercado Competitivo (Situación Inicial)</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("⚖️ Precio de Equilibrio (P*)", f"${P_eq:.2f}")
    st.metric("📦 Cantidad de Equilibrio (Q*)", f"{Q_eq:.0f} unidades")
with col2:
    st.metric("👥 Excedente del Consumidor", f"${CS_inicial:,.0f}")
    st.metric("🏭 Excedente del Productor", f"${PS_inicial:,.0f}")
with col3:
    st.metric("📈 Bienestar Total", f"${WT_inicial:,.0f}")
    st.caption("Bienestar = CS + PS")

# Gráfico del mercado inicial
fig_inicial = graficar_mercado_inicial(a, b, c, d, P_eq, Q_eq, CS_inicial, PS_inicial)
st.pyplot(fig_inicial)

with st.expander("📖 Fórmulas utilizadas - Excedentes"):
    P_max_dem_str = f"{P_max_dem:.2f}" if P_max_dem else "N/A"
    P_min_of_str = f"{P_min_of:.2f}" if P_min_of else "0"
    st.markdown(rf"""
    **Excedente del Consumidor (CS):** Área bajo la curva de demanda y sobre el precio de equilibrio.
    
    $$CS = \frac{{(P_{{max}} - P^*) \times Q^*}}{{2}} = \frac{{({P_max_dem_str} - {P_eq:.2f}) \times {Q_eq:.0f}}}{{2}} = {CS_inicial:,.0f}$$
    
    Donde $P_{{max}} = a/b = {P_max_dem_str}$ es el precio al que la cantidad demandada es cero.
    
    **Excedente del Productor (PS):** Área sobre la curva de oferta y bajo el precio de equilibrio.
    
    $$PS = \frac{{(P^* - P_{{min}}) \times Q^*}}{{2}} = \frac{{({P_eq:.2f} - {P_min_of_str}) \times {Q_eq:.0f}}}{{2}} = {PS_inicial:,.0f}$$
    
    Donde $P_{{min}} = \max(0, -c/d) = {P_min_of_str}$ es el precio al que la oferta comienza.
    
    **Bienestar Total:** $WT = CS + PS = {WT_inicial:,.0f}$
    """)

st.divider()

# ══════════════════════════════════════════════════════════════════
# MÓDULO 2: INTERVENCIONES
# ══════════════════════════════════════════════════════════════════

st.markdown('<div class="mod-header">🏛️ Módulo 2 — Políticas Públicas</div>', unsafe_allow_html=True)

tab_subsidio, tab_preciomax = st.tabs(["💰 SUBSIDIO (Ejercicio 1)", "💎 PRECIO MÁXIMO (Ejercicio 2)"])

# ================================================================
# TAB 1: SUBSIDIO (Ejercicio 1 del TP)
# ================================================================
with tab_subsidio:
    st.subheader("Ejercicio 1: Subsidio al Transporte Público")
    st.markdown("""
    El gobierno otorga un subsidio por cada unidad (viaje) para reducir el precio pagado por los usuarios.
    
    **Funciones del mercado:**  
    $Q_d = a - b \\cdot P$  
    $Q_o = c + d \\cdot P$
    """)
    
    s = st.number_input("Monto del subsidio por unidad ($)", 
                    min_value=0.0,
                    max_value=float(P_eq * 2),
                    value=round(float(P_eq * 0.4), 1),
                    step=1.0,
                    key="subsidio_input",
                    format="%.2f",
                    help="Cantidad de pesos que el Estado entrega al productor por cada unidad vendida")
    
    if s > 0:
        Pc_test = (a - c - d * s) / (b + d)
        if Pc_test < 0:
            st.warning(f"⚠️ Con un subsidio de ${s:.2f}, el precio pagado por consumidores sería negativo. El subsidio máximo efectivo es ${(a-c)/d:.2f}.")
        else:
            # Cálculo con subsidio
            Pc = (a - c - d * s) / (b + d)
            Pc = max(0, Pc)
            Pv = Pc + s
            Qs = a - b * Pc
            Qs = max(0, Qs)
            
            # Excedentes con subsidio
            CS_nuevo = excedente_consumidor(a, b, Pc, Qs)
            PS_nuevo = excedente_productor(c, d, Pv, Qs)
            
            # Gasto fiscal
            gasto_fiscal = s * Qs
            
            # Bienestar total después
            WT_nuevo = CS_nuevo + PS_nuevo - gasto_fiscal
            
            # Variación del bienestar social
            variacion_bienestar = WT_nuevo - WT_inicial
        
        # Mostrar resultados
        st.subheader("Resultados del subsidio")
        
        # Primera fila: Precios y cantidades
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 Precio pagado por usuarios", f"${Pc:.2f}", delta=f"-${P_eq - Pc:.2f}")
            st.metric("🏭 Precio recibido por empresas", f"${Pv:.2f}", delta=f"+${Pv - P_eq:.2f}")
        with col2:
            st.metric("📦 Nueva cantidad transada", f"{Qs:.0f} unidades", delta=f"+{Qs - Q_eq:.0f}")
            st.metric("💵 Gasto fiscal total", f"${gasto_fiscal:,.0f}")

        # Segunda fila: Excedentes
        col1, col2 = st.columns(2)
        with col1:
            delta_cs = CS_nuevo - CS_inicial
            st.metric("👥 Nuevo Excedente Consumidor", f"${CS_nuevo:,.0f}", delta=f"{delta_cs:+,.0f}")
        with col2:
            delta_ps = PS_nuevo - PS_inicial
            st.metric("🏭 Nuevo Excedente Productor", f"${PS_nuevo:,.0f}", delta=f"{delta_ps:+,.0f}")

        # Tercera fila: Bienestar
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Bienestar Total (neto)", f"${WT_nuevo:,.0f}")
        with col2:
            color_delta = "normal" if variacion_bienestar >= 0 else "inverse"
            st.metric("📉 Variación del Bienestar Social", 
                    f"${variacion_bienestar:+,.0f}",
                    delta_color=color_delta)
        
        if variacion_bienestar < 0:
            st.markdown(f'<div class="caja-warn">⚠️ El subsidio genera una pérdida de bienestar social de <b>${abs(variacion_bienestar):,.0f}</b>. El costo fiscal supera los beneficios para consumidores y productores.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="caja-success">✅ El subsidio genera una ganancia de bienestar social de <b>${variacion_bienestar:,.0f}</b>.</div>', unsafe_allow_html=True)
        
        # Tabla resumen comparativa
        st.markdown("#### Comparación pre/post subsidio")
        comparativa = {
            "Variable": ["Precio de mercado", "Cantidad transada", "Excedente Consumidor", "Excedente Productor", "Bienestar Total (neto)"],
            "Sin subsidio": [f"${P_eq:.2f}", f"{Q_eq:.0f}", f"${CS_inicial:,.0f}", f"${PS_inicial:,.0f}", f"${WT_inicial:,.0f}"],
            "Con subsidio": [f"${Pc:.2f}", f"{Qs:.0f}", f"${CS_nuevo:,.0f}", f"${PS_nuevo:,.0f}", f"${WT_nuevo:,.0f}"],
            "Cambio": [f"${Pc - P_eq:+.2f}", f"{Qs - Q_eq:+.0f}", f"${delta_cs:+,.0f}", f"${delta_ps:+,.0f}", f"${variacion_bienestar:+,.0f}"]
        }
        st.dataframe(comparativa, use_container_width=True, hide_index=True)
        
        # Gráfico del subsidio
        fig_sub = graficar_subsidio(a, b, c, d, P_eq, Q_eq, s, Pc, Pv, Qs, 
                                    CS_inicial, PS_inicial, CS_nuevo, PS_nuevo, 
                                    gasto_fiscal, variacion_bienestar)
        st.pyplot(fig_sub)
        
        # Simulación de múltiples subsidios (como pide el TP)
        st.markdown("#### Simulación de distintos montos de subsidio")
        st.markdown("Construya una tabla con diferentes valores de subsidio para analizar su impacto:")
        
        subsidios_a_simular = [0, 5, 10, 15, 20]
        # Ajustar para que no se pase del rango
        subsidios_a_simular = [s_val for s_val in subsidios_a_simular if s_val <= P_eq * 1.2]
        
        datos_simulacion = []
        for s_val in subsidios_a_simular:
            if s_val == 0:
                datos_simulacion.append({
                    "Subsidio (s)": f"${s_val}",
                    "Cantidad (Q)": f"{Q_eq:.0f}",
                    "Gasto Público": "$0",
                    "Bienestar Total": f"${WT_inicial:,.0f}"
                })
            else:
                Pc_sim = max(0, (a - c - d * s_val) / (b + d))
                Qs_sim = max(0, a - b * Pc_sim)
                gasto_sim = s_val * Qs_sim
                CS_sim = excedente_consumidor(a, b, Pc_sim, Qs_sim)
                PS_sim = excedente_productor(c, d, Pc_sim + s_val, Qs_sim)
                WT_sim = CS_sim + PS_sim - gasto_sim
                datos_simulacion.append({
                    "Subsidio (s)": f"${s_val}",
                    "Cantidad (Q)": f"{Qs_sim:.0f}",
                    "Gasto Público": f"${gasto_sim:,.0f}",
                    "Bienestar Total": f"${WT_sim:,.0f}"
                })
        
        st.dataframe(datos_simulacion, use_container_width=True, hide_index=True)
        
        # Interpretación económica
        with st.expander("📖 Interpretación económica del subsidio (Ejercicio 1)"):
            st.markdown(f"""
            ### ¿Qué ocurre con el subsidio de ${s:.2f} por unidad?
            
            **Efectos del subsidio:**
            
            1. **Desplazamiento de la oferta:** El subsidio desplaza la curva de oferta **hacia abajo** en exactamente ${s:.2f}.
            
            2. **Precios:**  
               - Los **consumidores** pagan ${Pc:.2f} en lugar de ${P_eq:.2f} → ahorro de ${P_eq - Pc:.2f} por unidad.  
               - Los **productores** reciben ${Pv:.2f} (precio de mercado + subsidio) en lugar de ${P_eq:.2f} → ganancia de ${Pv - P_eq:.2f} por unidad.
            
            3. **Cantidad:** Aumenta de {Q_eq:.0f} a {Qs:.0f} unidades.
            
            4. **Costo fiscal:** El Estado gasta ${gasto_fiscal:,.0f}.
            
            ### ¿Quiénes ganan?
            - **Usuarios del transporte (consumidores):** pagan menos por cada viaje.
            - **Empresas (productores):** reciben un precio efectivo más alto por unidad.
            
            ### ¿Quiénes pagan?
            - **Contribuyentes:** financian el subsidio a través de impuestos.
            
            ### ¿Aumenta o reduce el bienestar social?
            La variación del bienestar es **${'positiva' if variacion_bienestar >= 0 else 'negativa'}** (${'${:+,.0f}'.format(variacion_bienestar)}).
            
            **Conclusión:** El subsidio beneficia a consumidores y productores, pero genera un costo fiscal. En general, el subsidio produce una **pérdida social (DWL)** porque el costo fiscal supera los beneficios, excepto cuando existen externalidades positivas no consideradas en este modelo.
            """)
    
    else:
        st.info("📊 Ingresa un numero positivo para simular un subsidio.")


# ================================================================
# TAB 2: PRECIO MÁXIMO (Ejercicio 2 del TP)
# ================================================================
with tab_preciomax:
    st.subheader("Ejercicio 2: Precio Máximo a los Alquileres")
    st.markdown("""
    El gobierno fija un precio máximo para los alquileres urbanos con el objetivo de facilitar el acceso a la vivienda.
    
    **Funciones del mercado:**  
    $Q_d = a - b \\cdot P$  
    $Q_o = c + d \\cdot P$
    """)
    
    P_max_val = st.number_input("Precio máximo ($)", 
                            min_value=0.0,
                            max_value=float(max(P_eq * 2, P_max_dem if P_max_dem else P_eq * 2)),
                            value=float(P_eq * 0.7),
                            step=5.0,
                            key="pmax_input",
                            format="%.2f",
                            help="Precio máximo legal fijado por el Estado")
    
    # Validar que el precio máximo sea positivo
    if P_max_val <= 0:
        st.error("❌ El precio máximo debe ser mayor que cero.")
    else:
        Qd_pmax = max(0, a - b * P_max_val)
        Qo_pmax = max(0, c + d * P_max_val)
        escasez = max(0, Qd_pmax - Qo_pmax)
        efectivo = P_max_val < P_eq
    
        # Cálculo de excedentes con precio máximo
        if efectivo:
            Q_transada = Qo_pmax  # La cantidad transada es la ofrecida (la menor)
            
            # Excedente del Consumidor nuevo
            # CS nuevo = área bajo demanda hasta Q_transada - P_max * Q_transada
            if Q_transada > 0 and b > 0:
                # Integración numérica del área bajo la demanda
                Q_grid = np.linspace(0, Q_transada, 100)
                P_grid = (a - Q_grid) / b
                area_bajo_demanda = np.trapezoid(P_grid, Q_grid)
                CS_nuevo = max(0, area_bajo_demanda - P_max_val * Q_transada)
            else:
                CS_nuevo = 0
            
            # Excedente del Productor nuevo
            # PS nuevo = área bajo P_max hasta la oferta desde 0 hasta Q_transada
            if Q_transada > 0 and d > 0:
                # Encontrar el precio mínimo de oferta
                P_min_ps = precio_minimo_oferta(c, d)
                if P_min_ps is None:
                    P_min_ps = 0
                # Integración numérica
                P_grid_ps = np.linspace(P_min_ps, P_max_val, 100)
                Q_grid_ps = np.maximum(c + d * P_grid_ps, 0)
                # Solo hasta Q_transada
                mask = Q_grid_ps <= Q_transada
                if np.any(mask):
                    area_bajo_oferta = np.trapezoid(Q_grid_ps[mask], P_grid_ps[mask])
                    PS_nuevo = max(0, area_bajo_oferta)
                else:
                    PS_nuevo = 0
            else:
                PS_nuevo = 0
            
            # Pérdida social (DWL)
            # DWL = área del triángulo entre oferta y demanda entre Q_transada y Q_eq
            if Q_transada < Q_eq:
                Pd_Qtrans = (a - Q_transada) / b
                Po_Qtrans = (Q_transada - c) / d
                perdida_social = 0.5 * (Q_eq - Q_transada) * (Pd_Qtrans - Po_Qtrans)
            else:
                perdida_social = 0
                
            WT_nuevo = CS_nuevo + PS_nuevo
            variacion_bienestar = WT_nuevo - WT_inicial
        else:
            Q_transada = Q_eq
            CS_nuevo = CS_inicial
            PS_nuevo = PS_inicial
            perdida_social = 0
            variacion_bienestar = 0
            WT_nuevo = WT_inicial
    
        # Mostrar resultados
        st.subheader("Resultados del precio máximo")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 Precio máximo fijado", f"${P_max_val:.2f}")
            st.metric("⚠️ Escasez generada", f"{escasez:.0f} unidades", 
                    delta="Efectivo" if efectivo else "Sin efecto", delta_color="off")
        with col2:
            st.metric("📈 Cantidad demandada (Qd)", f"{Qd_pmax:.0f}")
            st.metric("📉 Cantidad ofrecida (Qo)", f"{Qo_pmax:.0f}")
        
        if efectivo:
            # Primera fila: Excedentes (2 columnas)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("👥 Excedente Consumidor (nuevo)", f"${CS_nuevo:,.0f}", 
                        delta=f"${CS_nuevo - CS_inicial:+,.0f}")
            with col2:
                st.metric("🏭 Excedente Productor (nuevo)", f"${PS_nuevo:,.0f}",
                        delta=f"${PS_nuevo - PS_inicial:+,.0f}")
            
            # Segunda fila: Bienestar y Variación (2 columnas)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 Bienestar Total (nuevo)", f"${WT_nuevo:,.0f}")
            with col2:
                st.metric("📉 Variación del Bienestar Social", 
                        f"${variacion_bienestar:+,.0f}",
                        delta_color="inverse")
            

        # Gráfico
        fig_pmax = graficar_precio_maximo(a, b, c, d, P_eq, Q_eq, P_max_val, Qd_pmax, Qo_pmax, 
                                        escasez, efectivo, CS_inicial, PS_inicial, 
                                        CS_nuevo if efectivo else CS_inicial,
                                        PS_nuevo if efectivo else PS_inicial,
                                        perdida_social if efectivo else 0)
        st.pyplot(fig_pmax)
        
        # Simulación de múltiples precios máximos 
        st.markdown("#### Simulación de distintos precios máximos")
        st.markdown("Construya una tabla mostrando: cantidad demandada, cantidad ofrecida y escasez.")
        
        precios_a_simular = [70, 60, 50, 40, 30]
        datos_simulacion = []
        for p_val in precios_a_simular:
            Qd_sim = max(0, a - b * p_val)
            Qo_sim = max(0, c + d * p_val)
            esc_sim = max(0, Qd_sim - Qo_sim)
            efectivo_sim = p_val < P_eq
            datos_simulacion.append({
                "Precio Máximo": f"${p_val}",
                "¿Efectivo?": "✅ Sí" if efectivo_sim else "❌ No",
                "Qd": f"{Qd_sim:.0f}",
                "Qo": f"{Qo_sim:.0f}",
                "Escasez": f"{esc_sim:.0f}"
            })
        
        st.dataframe(datos_simulacion, use_container_width=True, hide_index=True)
        
        # Interpretación económica
        with st.expander("📖 Interpretación económica del precio máximo (Ejercicio 2)"):
            if efectivo:
                st.markdown(f"""
                ### ¿Qué ocurre con el precio máximo de ${P_max_val:.2f}?
                
                **Efectos del precio máximo:**
                
                1. **Precio máximo por debajo del equilibrio:** El techo de precio se fija **por debajo** de P* = ${P_eq:.2f}.
                
                2. **Consecuencias:**  
                - **Cantidad demandada:** {Qd_pmax:.0f} unidades (aumenta porque el precio es más bajo).  
                - **Cantidad ofrecida:** {Qo_pmax:.0f} unidades (disminuye porque el precio es más bajo).  
                - **Escasez:** {escasez:.0f} unidades ({Qd_pmax:.0f} - {Qo_pmax:.0f}).
                
                3. **Cantidad realmente transada:** {Qo_pmax:.0f} unidades (la menor entre oferta y demanda).
                
                4. **Excedentes:**  
                - El **excedente del consumidor** cambia de ${CS_inicial:,.0f} a ${CS_nuevo:,.0f}.  
                - El **excedente del productor** cambia de ${PS_inicial:,.0f} a ${PS_nuevo:,.0f}.
                
                5. **Pérdida social (DWL):** ${perdida_social:,.0f}
                
                ### ¿Quiénes ganan?
                - **Algunos consumidores** que logran alquilar a un precio más bajo.
                
                ### ¿Quiénes pierden?
                - **Propietarios** reciben menos por sus propiedades.
                - **Consumidores excluidos** que no encuentran vivienda disponible.
                - La **sociedad en su conjunto** pierde bienestar (DWL).
                
                ### ¿La política resuelve el problema habitacional?
                No necesariamente. Si bien algunos inquilinos pagan menos, muchos no encuentran vivienda debido a la escasez. Pueden aparecer **mercados negros** y **deterioro de la calidad** de las viviendas ofrecidas.
                """)
            else:
                st.markdown(f"""
                ### El precio máximo de ${P_max_val:.2f} NO es efectivo
                
                **¿Por qué no tiene efecto?**
                
                El equilibrio de mercado se encuentra en P* = ${P_eq:.2f}.  
                El gobierno fija un techo de ${P_max_val:.2f}, pero este valor está **por encima** del precio de equilibrio.
                
                **Consecuencia:** El mercado sigue operando en su equilibrio natural. La ley no prohíbe nada porque nadie quiere cobrar por encima del techo.
                
                **Un precio máximo solo es relevante cuando se ubica POR DEBAJO del equilibrio.**
                """)


# ══════════════════════════════════════════════════════════════════
# GENERADOR DE PDF
# ══════════════════════════════════════════════════════════════════

AZUL     = rl_colors.HexColor('#1e3a8a')
AZUL_MED = rl_colors.HexColor('#2563eb')
GRIS_OSC = rl_colors.HexColor('#374151')
GRIS_CLR = rl_colors.HexColor('#f3f4f6')
BLANCO   = rl_colors.white
ROJO_RL  = rl_colors.HexColor('#dc2626')
VERDE_RL = rl_colors.HexColor('#059669')
NARANJA_RL = rl_colors.HexColor('#f59e0b')

def _pdf_styles():
    base = getSampleStyleSheet()
    estilos = {
        'titulo': ParagraphStyle('titulo', parent=base['Title'],
                                 fontSize=20, textColor=BLANCO, alignment=TA_CENTER,
                                 spaceAfter=4, fontName='Helvetica-Bold'),
        'subtitulo': ParagraphStyle('subtitulo', parent=base['Normal'],
                                    fontSize=11, textColor=BLANCO, alignment=TA_CENTER,
                                    spaceAfter=2),
        'h1': ParagraphStyle('h1', parent=base['Heading1'],
                              fontSize=13, textColor=AZUL, fontName='Helvetica-Bold',
                              spaceBefore=14, spaceAfter=4,
                              borderPad=4, leading=16),
        'h2': ParagraphStyle('h2', parent=base['Heading2'],
                              fontSize=11, textColor=AZUL_MED, fontName='Helvetica-Bold',
                              spaceBefore=8, spaceAfter=3),
        'body': ParagraphStyle('body', parent=base['Normal'],
                               fontSize=9.5, textColor=GRIS_OSC,
                               spaceAfter=4, leading=14),
        'caption': ParagraphStyle('caption', parent=base['Normal'],
                                  fontSize=8, textColor=rl_colors.HexColor('#6b7280'),
                                  alignment=TA_CENTER, spaceAfter=6),
        'formula': ParagraphStyle('formula', parent=base['Normal'],
                                  fontSize=10, fontName='Courier',
                                  textColor=AZUL, leftIndent=18,
                                  spaceAfter=3, leading=14),
        'footer': ParagraphStyle('footer', parent=base['Normal'],
                                 fontSize=7.5, textColor=rl_colors.HexColor('#9ca3af'),
                                 alignment=TA_CENTER),
    }
    return estilos

def _tabla_datos(filas, col_widths=None, header_bg=AZUL):
    """Crea una tabla estilizada para el PDF."""
    t = Table(filas, colWidths=col_widths)
    style = [
        ('BACKGROUND', (0,0), (-1,0), header_bg),
        ('TEXTCOLOR',  (0,0), (-1,0), BLANCO),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,0), 9),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [BLANCO, GRIS_CLR]),
        ('FONTSIZE',   (0,1), (-1,-1), 8.5),
        ('TEXTCOLOR',  (0,1), (-1,-1), GRIS_OSC),
        ('GRID',       (0,0), (-1,-1), 0.4, rl_colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('RIGHTPADDING',  (0,0), (-1,-1), 8),
        ('ROUNDEDCORNERS', [4]),
    ]
    t.setStyle(TableStyle(style))
    return t

def fig_to_png_bytes(fig, dpi=120):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    return buf

def generar_pdf(params):
    """
    params: dict con todos los datos del simulador para incluir en el PDF.
    Devuelve bytes del PDF.
    """
    es = _pdf_styles()
    buf_pdf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf_pdf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    story = []
    W = A4[0] - 4*cm

    # ── PORTADA ──────────────────────────────────────────────────
    header_data = [[
        Paragraph("SIMULADOR DE POLÍTICAS PÚBLICAS", es['titulo']),
    ],[
        Paragraph("Economía para Ingenieros · UNSTA 2026", es['subtitulo']),
    ],[
        Paragraph(f"Alumnas: {params['alumnas']}", es['subtitulo']),
    ],[
        Paragraph(f"Profesor: {params['profesor']}  |  Fecha: {params['fecha']}", es['subtitulo']),
    ],[
        Paragraph("Subsidio y Precio Máximo", es['subtitulo']),
    ]]
    tbl_header = Table(header_data, colWidths=[W])
    tbl_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), AZUL),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 16),
        ('RIGHTPADDING',  (0,0),(-1,-1), 16),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(tbl_header)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width='100%', thickness=1.5, color=AZUL_MED))
    story.append(Spacer(1, 0.3*cm))

    # ── SECCIÓN 1: PARÁMETROS DEL MERCADO ────────────────────────
    story.append(Paragraph("1. Parámetros del Mercado", es['h1']))

    filas_ec = [
        ['Ecuación', 'Función', 'Parámetros'],
        ['Demanda', f"Qd = {params['a']:.2f} − {params['b']:.2f}·P",
         f"a = {params['a']:.2f}  |  b = {params['b']:.2f}"],
        ['Oferta',  f"Qo = {params['c']:.2f} + {params['d']:.2f}·P",
         f"c = {params['c']:.2f}  |  d = {params['d']:.2f}"],
    ]
    story.append(_tabla_datos(filas_ec, col_widths=[W*0.2, W*0.45, W*0.35]))
    story.append(Spacer(1, 0.3*cm))

    # ── SECCIÓN 2: EQUILIBRIO ────────────────────────────────────
    story.append(Paragraph("2. Equilibrio de Mercado", es['h1']))
    story.append(Paragraph(
        f"Igualando Qd = Qo → P* = (a − c) / (b + d) = "
        f"({params['a']:.2f} − {params['c']:.2f}) / ({params['b']:.2f} + {params['d']:.2f})", es['formula']))

    filas_eq = [
        ['Variable', 'Valor', 'Interpretación'],
        ['Precio de equilibrio P*', f"${params['P_eq']:.2f}", 'Precio al que Qd = Qo'],
        ['Cantidad de equilibrio Q*', f"{params['Q_eq']:.0f} unidades", 'Cantidad intercambiada'],
        ['Excedente del Consumidor', f"${params['CS_inicial']:,.0f}", 'Área bajo la demanda sobre P*'],
        ['Excedente del Productor', f"${params['PS_inicial']:,.0f}", 'Área sobre la oferta bajo P*'],
        ['Bienestar Total', f"${params['WT_inicial']:,.0f}", 'CS + PS'],
    ]
    story.append(_tabla_datos(filas_eq, col_widths=[W*0.35, W*0.25, W*0.40]))

    # Gráfico mercado
    if params.get('fig_mercado'):
        story.append(Spacer(1, 0.25*cm))
        png = fig_to_png_bytes(params['fig_mercado'])
        story.append(RLImage(png, width=W*0.85, height=W*0.52))
        story.append(Paragraph("Gráfico 1 — Equilibrio de mercado competitivo", es['caption']))

    # ── SECCIÓN 3: SUBSIDIO ──────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("3. Subsidio por Unidad", es['h1']))
    story.append(Paragraph(
        "Ejercicio 1: Subsidio al transporte público", es['h2']))
    
    sub = params['subsidio']
    filas_sub = [
        ['Concepto', 'Sin subsidio', 'Con subsidio', 'Cambio'],
        ['Precio de mercado', f"${params['P_eq']:.2f}", f"${sub['Pc']:.2f}", f"${sub['Pc'] - params['P_eq']:+.2f}"],
        ['Precio que recibe el vendedor', f"${params['P_eq']:.2f}", f"${sub['Pv']:.2f}", f"+${sub['Pv'] - params['P_eq']:.2f}"],
        ['Cantidad transada', f"{params['Q_eq']:.0f}", f"{sub['Q']:.0f}", f"+{sub['Q'] - params['Q_eq']:.0f}"],
        ['Excedente Consumidor', f"${params['CS_inicial']:,.0f}", f"${sub['CS_nuevo']:,.0f}", f"${sub['CS_nuevo'] - params['CS_inicial']:+,.0f}"],
        ['Excedente Productor', f"${params['PS_inicial']:,.0f}", f"${sub['PS_nuevo']:,.0f}", f"${sub['PS_nuevo'] - params['PS_inicial']:+,.0f}"],
        ['Bienestar Total', f"${params['WT_inicial']:,.0f}", f"${sub['WT_nuevo']:,.0f}", f"${sub['WT_nuevo'] - params['WT_inicial']:+,.0f}"],
        ['Gasto Fiscal', '—', f"${sub['gasto_fiscal']:,.0f}", '—'],
        ['Variación del Bienestar', '—', '—', f"${sub['variacion']:+,.0f}"],
    ]
    story.append(_tabla_datos(filas_sub, col_widths=[W*0.25, W*0.2, W*0.25, W*0.3]))

    if params.get('fig_subsidio'):
        story.append(Spacer(1, 0.25*cm))
        png = fig_to_png_bytes(params['fig_subsidio'])
        story.append(RLImage(png, width=W*0.85, height=W*0.52))
        story.append(Paragraph("Gráfico 2 — Subsidio por unidad", es['caption']))

    # Tabla de simulación de subsidios
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("3.1 Simulación de distintos montos de subsidio", es['h2']))
    filas_sim_sub = [['Subsidio (s)', 'Cantidad (Q)', 'Gasto Público', 'Bienestar Total']]
    for sim in params['simulacion_subsidios']:
        filas_sim_sub.append([sim['s'], sim['Q'], sim['gasto'], sim['bienestar']])
    story.append(_tabla_datos(filas_sim_sub, col_widths=[W*0.25, W*0.25, W*0.25, W*0.25]))

    # ── SECCIÓN 4: PRECIO MÁXIMO ─────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4. Precio Máximo", es['h1']))
    story.append(Paragraph(
        "Ejercicio 2: Precio máximo a los alquileres urbanos", es['h2']))
    
    pm = params['precio_maximo']
    filas_pm = [
        ['Concepto', 'Sin intervención', 'Con precio máximo', 'Cambio'],
        ['Precio máximo fijado', '—', f"${pm['P_max']:.2f}", '—'],
        ['¿Es efectivo?', '—', '✓ Sí' if pm['efectivo'] else '✗ No', '—'],
        ['Precio de mercado', f"${params['P_eq']:.2f}", f"${pm['P_max']:.2f}" if pm['efectivo'] else f"${params['P_eq']:.2f}", f"${pm['P_max'] - params['P_eq']:+.2f}" if pm['efectivo'] else '$0.00'],
        ['Cantidad demandada (Qd)', f"{params['Q_eq']:.0f}", f"{pm['Qd']:.0f}", f"{pm['Qd'] - params['Q_eq']:+.0f}"],
        ['Cantidad ofrecida (Qo)', f"{params['Q_eq']:.0f}", f"{pm['Qo']:.0f}", f"{pm['Qo'] - params['Q_eq']:+.0f}"],
        ['Cantidad transada', f"{params['Q_eq']:.0f}", f"{pm['Q_transada']:.0f}", f"{pm['Q_transada'] - params['Q_eq']:+.0f}"],
        ['Escasez', '0', f"{pm['escasez']:.0f}", f"+{pm['escasez']:.0f}"] if pm['efectivo'] else ['Escasez', '0', '0', '0'],
        ['Excedente Consumidor', f"${params['CS_inicial']:,.0f}", f"${pm['CS_nuevo']:,.0f}", f"${pm['CS_nuevo'] - params['CS_inicial']:+,.0f}"],
        ['Excedente Productor', f"${params['PS_inicial']:,.0f}", f"${pm['PS_nuevo']:,.0f}", f"${pm['PS_nuevo'] - params['PS_inicial']:+,.0f}"],
        ['Bienestar Total', f"${params['WT_inicial']:,.0f}", f"${pm['WT_nuevo']:,.0f}", f"${pm['WT_nuevo'] - params['WT_inicial']:+,.0f}"],
        ['Pérdida Social (DWL)', '0', f"${pm['perdida_social']:,.0f}", f"-${pm['perdida_social']:,.0f}"],
    ]
    story.append(_tabla_datos(filas_pm, col_widths=[W*0.25, W*0.2, W*0.25, W*0.3]))

    if params.get('fig_preciomax'):
        story.append(Spacer(1, 0.25*cm))
        png = fig_to_png_bytes(params['fig_preciomax'])
        story.append(RLImage(png, width=W*0.85, height=W*0.52))
        story.append(Paragraph("Gráfico 3 — Precio máximo", es['caption']))

    # Tabla de simulación de precios máximos
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("4.1 Simulación de distintos precios máximos", es['h2']))
    filas_sim_pm = [['Precio Máximo', '¿Efectivo?', 'Qd', 'Qo', 'Escasez']]
    for sim in params['simulacion_precios']:
        filas_sim_pm.append([sim['P_max'], sim['efectivo'], sim['Qd'], sim['Qo'], sim['escasez']])
    story.append(_tabla_datos(filas_sim_pm, col_widths=[W*0.2, W*0.2, W*0.2, W*0.2, W*0.2]))

    # ── SECCIÓN 5: CONCLUSIONES ───────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5. Conclusiones", es['h1']))

    conclusiones = [
        f"• El mercado alcanza equilibrio en <b>P* = ${params['P_eq']:.2f}</b> y "
        f"<b>Q* = {params['Q_eq']:.0f} unidades</b>. El bienestar total inicial es de <b>${params['WT_inicial']:,.0f}</b>.",

        f"• <b>Subsidio de ${params['subsidio']['s']:.2f} por unidad:</b> "
        f"Reduce el precio pagado por consumidores a ${params['subsidio']['Pc']:.2f} "
        f"y aumenta la cantidad a {params['subsidio']['Q']:.0f} unidades. "
        f"El Estado gasta <b>${params['subsidio']['gasto_fiscal']:,.0f}</b> y el bienestar social "
        f"{'aumenta' if params['subsidio']['variacion'] >= 0 else 'disminuye'} en "
        f"<b>${abs(params['subsidio']['variacion']):,.0f}</b>.",

        f"• <b>Precio máximo de ${params['precio_maximo']['P_max']:.2f}:</b> "
        f"{'Es efectivo' if params['precio_maximo']['efectivo'] else 'No es efectivo (está por encima del equilibrio)'}. "
        f"{'Genera una escasez de ' + str(int(params['precio_maximo']['escasez'])) + ' unidades y una pérdida social de $' + f'{params['precio_maximo']['perdida_social']:,.0f}' if params['precio_maximo']['efectivo'] else 'No altera el mercado.'}",

        "• <b>Regla general:</b> Un subsidio beneficia a consumidores y productores pero genera un costo fiscal. "
        "Un precio máximo efectivo (por debajo del equilibrio) beneficia a algunos consumidores pero genera escasez y pérdida de bienestar.",

        "• <b>Conclusión final:</b> Las intervenciones del Estado pueden lograr objetivos sociales específicos, "
        "pero siempre generan efectos secundarios. Es fundamental analizar cada caso considerando "
        "las elasticidades de oferta y demanda para minimizar la pérdida de eficiencia."
    ]
    for c_txt in conclusiones:
        story.append(Paragraph(c_txt, es['body']))
        story.append(Spacer(1, 0.15*cm))

    # ── PIE ──────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width='100%', thickness=0.8, color=rl_colors.HexColor('#e5e7eb')))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"UNSTA 2026 · Economía para Ingenieros · "
        f"Alumnas: {params['alumnas']} · Prof. {params['profesor']} · "
        f"Generado: {params['fecha']}",
        es['footer']))

    doc.build(story)
    buf_pdf.seek(0)
    return buf_pdf.read()

# ══════════════════════════════════════════════════════════════════
# EXPORTAR PDF
# ══════════════════════════════════════════════════════════════════

st.markdown('<div class="mod-header">📄 Exportar Informe PDF</div>', unsafe_allow_html=True)
st.markdown("Generá un informe académico completo con todos los resultados y gráficos.")

col_pdf1, col_pdf2 = st.columns([3, 1])
with col_pdf1:
    st.markdown(
        "El PDF incluye: parámetros del mercado, equilibrio, excedentes, "
        "resultados del subsidio (con simulación), resultados del precio máximo (con simulación) y conclusiones."
    )
with col_pdf2:
    generar_btn = st.button("⚙️ Preparar PDF", type="primary", use_container_width=True)

if generar_btn:
    with st.spinner("Generando informe PDF..."):
        # Re-generar gráficos para el PDF
        _fig_mercado = graficar_mercado_inicial(a, b, c, d, P_eq, Q_eq, CS_inicial, PS_inicial)
        
        # Subsidio (usar el valor actual del slider)
        s_actual = s if 's' in locals() else 0
        if s_actual > 0:
            Pc_pdf = max(0, (a - c - d * s_actual) / (b + d))
            Qs_pdf = max(0, a - b * Pc_pdf)
            Pv_pdf = Pc_pdf + s_actual
            CS_sub_pdf = excedente_consumidor(a, b, Pc_pdf, Qs_pdf)
            PS_sub_pdf = excedente_productor(c, d, Pv_pdf, Qs_pdf)
            gasto_pdf = s_actual * Qs_pdf
            WT_sub_pdf = CS_sub_pdf + PS_sub_pdf - gasto_pdf
            var_sub_pdf = WT_sub_pdf - WT_inicial
            _fig_sub = graficar_subsidio(a, b, c, d, P_eq, Q_eq, s_actual, Pc_pdf, Pv_pdf, Qs_pdf,
                                        CS_inicial, PS_inicial, CS_sub_pdf, PS_sub_pdf,
                                        gasto_pdf, var_sub_pdf)
        else:
            _fig_sub = None
            Pc_pdf = P_eq
            Pv_pdf = P_eq
            Qs_pdf = Q_eq
            CS_sub_pdf = CS_inicial
            PS_sub_pdf = PS_inicial
            gasto_pdf = 0
            WT_sub_pdf = WT_inicial
            var_sub_pdf = 0
        
        # Simulación de subsidios para PDF
        simulacion_subsidios = []
        for s_val in [0, 5, 10, 15, 20]:
            if s_val <= P_eq * 1.2:
                if s_val == 0:
                    simulacion_subsidios.append({
                        's': f"${s_val}",
                        'Q': f"{Q_eq:.0f}",
                        'gasto': "$0",
                        'bienestar': f"${WT_inicial:,.0f}"
                    })
                else:
                    Pc_sim = max(0, (a - c - d * s_val) / (b + d))
                    Qs_sim = max(0, a - b * Pc_sim)
                    gasto_sim = s_val * Qs_sim
                    CS_sim = excedente_consumidor(a, b, Pc_sim, Qs_sim)
                    PS_sim = excedente_productor(c, d, Pc_sim + s_val, Qs_sim)
                    WT_sim = CS_sim + PS_sim - gasto_sim
                    simulacion_subsidios.append({
                        's': f"${s_val}",
                        'Q': f"{Qs_sim:.0f}",
                        'gasto': f"${gasto_sim:,.0f}",
                        'bienestar': f"${WT_sim:,.0f}"
                    })
        
        # Precio máximo (usar el valor actual del slider)
        Pmax_actual = P_max_val if 'P_max_val' in locals() else P_eq
        efectivo_actual = Pmax_actual < P_eq
        
        if efectivo_actual:
            Qo_pmax_actual = max(0, c + d * Pmax_actual)
            Qd_pmax_actual = max(0, a - b * Pmax_actual)
            escasez_actual = max(0, Qd_pmax_actual - Qo_pmax_actual)
            Q_trans_actual = Qo_pmax_actual
            
            # Calcular CS y PS para precio máximo
            if Q_trans_actual > 0 and b > 0:
                Q_grid = np.linspace(0, Q_trans_actual, 100)
                P_grid = (a - Q_grid) / b
                area_bajo_demanda = np.trapezoid(P_grid, Q_grid)
                CS_pmax_actual = max(0, area_bajo_demanda - Pmax_actual * Q_trans_actual)
            else:
                CS_pmax_actual = 0
            
            if Q_trans_actual > 0 and d > 0:
                P_min_ps = precio_minimo_oferta(c, d) or 0
                P_grid_ps = np.linspace(P_min_ps, Pmax_actual, 100)
                Q_grid_ps = np.maximum(c + d * P_grid_ps, 0)
                mask = Q_grid_ps <= Q_trans_actual
                if np.any(mask):
                    area_bajo_oferta = np.trapezoid(Q_grid_ps[mask], P_grid_ps[mask])
                    PS_pmax_actual = max(0, area_bajo_oferta)
                else:
                    PS_pmax_actual = 0
            else:
                PS_pmax_actual = 0
            
            if Q_trans_actual < Q_eq:
                Pd_Qtrans = (a - Q_trans_actual) / b
                Po_Qtrans = (Q_trans_actual - c) / d
                perdida_actual = 0.5 * (Q_eq - Q_trans_actual) * (Pd_Qtrans - Po_Qtrans)
            else:
                perdida_actual = 0
        else:
            Qo_pmax_actual = Q_eq
            Qd_pmax_actual = Q_eq
            escasez_actual = 0
            Q_trans_actual = Q_eq
            CS_pmax_actual = CS_inicial
            PS_pmax_actual = PS_inicial
            perdida_actual = 0
        
        WT_pmax_actual = CS_pmax_actual + PS_pmax_actual
        variacion_pmax = WT_pmax_actual - WT_inicial
        
        _fig_pmax = graficar_precio_maximo(a, b, c, d, P_eq, Q_eq, Pmax_actual, 
                                          Qd_pmax_actual, Qo_pmax_actual, 
                                          escasez_actual, efectivo_actual,
                                          CS_inicial, PS_inicial,
                                          CS_pmax_actual, PS_pmax_actual, perdida_actual)
        
        # Simulación de precios máximos para PDF
        simulacion_precios = []
        for p_val in [70, 60, 50, 40, 30]:
            Qd_sim = max(0, a - b * p_val)
            Qo_sim = max(0, c + d * p_val)
            esc_sim = max(0, Qd_sim - Qo_sim)
            efectivo_sim = p_val < P_eq
            simulacion_precios.append({
                'P_max': f"${p_val}",
                'efectivo': "✅ Sí" if efectivo_sim else "❌ No",
                'Qd': f"{Qd_sim:.0f}",
                'Qo': f"{Qo_sim:.0f}",
                'escasez': f"{esc_sim:.0f}"
            })
        
        # Construir diccionario de parámetros para el PDF
        params_pdf = {
            'alumnas': 'Abregú Candela · Amin Guadalupe · Pasteris Luciana',
            'profesor': 'Raúl García',
            'fecha': datetime.date.today().strftime('%d/%m/%Y'),
            'a': a, 'b': b, 'c': c, 'd': d,
            'P_eq': P_eq, 'Q_eq': Q_eq,
            'CS_inicial': CS_inicial, 'PS_inicial': PS_inicial, 'WT_inicial': WT_inicial,
            'subsidio': {
                's': s_actual,
                'Pc': Pc_pdf, 'Pv': Pv_pdf, 'Q': Qs_pdf,
                'CS_nuevo': CS_sub_pdf, 'PS_nuevo': PS_sub_pdf,
                'WT_nuevo': WT_sub_pdf,
                'gasto_fiscal': gasto_pdf,
                'variacion': var_sub_pdf
            },
            'precio_maximo': {
                'P_max': Pmax_actual,
                'efectivo': efectivo_actual,
                'Qd': Qd_pmax_actual, 'Qo': Qo_pmax_actual,
                'Q_transada': Q_trans_actual,
                'escasez': escasez_actual,
                'CS_nuevo': CS_pmax_actual, 'PS_nuevo': PS_pmax_actual,
                'WT_nuevo': WT_pmax_actual,
                'perdida_social': perdida_actual,
                'variacion': variacion_pmax
            },
            'simulacion_subsidios': simulacion_subsidios,
            'simulacion_precios': simulacion_precios,
            'fig_mercado': _fig_mercado,
            'fig_subsidio': _fig_sub,
            'fig_preciomax': _fig_pmax,
        }
        
        pdf_bytes = generar_pdf(params_pdf)
        
        # Cerrar todas las figuras
        plt.close(_fig_mercado)
        if _fig_sub:
            plt.close(_fig_sub)
        plt.close(_fig_pmax)
    
    st.success("✅ PDF listo para descargar.")
    nombre_archivo = f"Informe_Politicas_Publicas_{datetime.date.today().strftime('%Y%m%d')}.pdf"
    st.download_button(
        label="📄 Descargar Informe PDF",
        data=pdf_bytes,
        file_name=nombre_archivo,
        mime="application/pdf",
        use_container_width=True,
    )