"""
mapa_cusco.py - Generación de mapa base para Cusco
"""

from PIL import Image, ImageDraw

def generar_mapa(ancho, alto):
    """Genera una imagen de mapa de fondo para Cusco."""
    img = Image.new('RGB', (ancho, alto), color=(13, 17, 23))
    draw = ImageDraw.Draw(img)
    
    # Cuadrícula
    for x in range(0, ancho, 50):
        draw.line([(x, 0), (x, alto)], fill=(30, 35, 45), width=1)
    for y in range(0, alto, 50):
        draw.line([(0, y), (ancho, y)], fill=(30, 35, 45), width=1)
    
    # Centro histórico
    centro_x, centro_y = ancho // 2, alto // 2
    draw.ellipse([centro_x-120, centro_y-80, centro_x+120, centro_y+80], 
                 outline=(88, 166, 255), width=2, fill=(13, 17, 23))
    
    # Río
    draw.line([(0, alto//2 + 40), (ancho, alto//2 + 40)], fill=(52, 152, 219), width=3)
    
    return img
