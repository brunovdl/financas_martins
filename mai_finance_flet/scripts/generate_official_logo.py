"""
generate_official_logo.py — Gera a logo oficial do MAI Finance baseada fielmente no design do usuário.
Gera SVG vetorial, PNGs em múltiplos tamanhos e atualiza os arquivos do flet_web para erradicar o logo do Flet.
"""
import os
from PIL import Image, ImageDraw

def generate():
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#182036"/>
      <stop offset="100%" stop-color="#0E1424"/>
    </linearGradient>

    <linearGradient id="tealGrad" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#2DD4BF"/>
      <stop offset="100%" stop-color="#4FF1DF"/>
    </linearGradient>

    <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Fundo Squircle Arredondado com cantos suaves -->
  <rect x="28" y="28" width="456" height="456" rx="115" ry="115" fill="url(#bgGrad)"/>
  <rect x="28" y="28" width="456" height="456" rx="115" ry="115" fill="none" stroke="url(#tealGrad)" stroke-width="16" opacity="0.95"/>

  <!-- Gráfico de Tendência Ascendente com Seta (MAI Finance) -->
  <g filter="url(#neonGlow)">
    <polyline
      points="155,340 230,265 285,315 375,220"
      fill="none"
      stroke="url(#tealGrad)"
      stroke-width="32"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <polygon
      points="410,170 315,190 348,232 390,265"
      fill="url(#tealGrad)"
    />
  </g>
</svg>'''

    # Renderização de Alta Resolução via Pillow (1024x1024 supersampled)
    S = 1024
    scale = S / 512.0

    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Cores Oficiais
    BG_COLOR = (18, 24, 40, 255)       # #121828 escuro
    BORDER_COLOR = (63, 214, 196, 255) # #3FD6C4 Teal
    LINE_COLOR = (63, 214, 196, 255)   # #3FD6C4 Teal

    # Squircle
    m = int(28 * scale)
    r = int(115 * scale)
    bw = int(16 * scale)
    box = [m, m, S - m, S - m]

    draw.rounded_rectangle(box, radius=r, fill=BG_COLOR)
    draw.rounded_rectangle(box, radius=r, outline=BORDER_COLOR, width=bw)

    # Linha Ascendente
    lw = int(34 * scale)
    p1 = (int(155 * scale), int(340 * scale))
    p2 = (int(230 * scale), int(265 * scale))
    p3 = (int(285 * scale), int(315 * scale))
    p4 = (int(375 * scale), int(220 * scale))

    draw.line([p1, p2], fill=LINE_COLOR, width=lw, joint='round')
    draw.line([p2, p3], fill=LINE_COLOR, width=lw, joint='round')
    draw.line([p3, p4], fill=LINE_COLOR, width=lw, joint='round')

    for pt in (p1, p2, p3):
        draw.ellipse([pt[0] - lw//2, pt[1] - lw//2, pt[0] + lw//2, pt[1] + lw//2], fill=LINE_COLOR)

    # Seta
    tip = (int(410 * scale), int(170 * scale))
    wing_left = (int(315 * scale), int(190 * scale))
    wing_bottom = (int(390 * scale), int(265 * scale))
    inner_corner = (int(348 * scale), int(232 * scale))

    draw.polygon([tip, wing_left, inner_corner, wing_bottom], fill=LINE_COLOR)

    # Redimensionamentos com filtro Lanczos para máxima nitidez
    img_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    img_192 = img.resize((192, 192), Image.Resampling.LANCZOS)
    img_64  = img.resize((64, 64), Image.Resampling.LANCZOS)
    img_32  = img.resize((32, 32), Image.Resampling.LANCZOS)
    img_16  = img.resize((16, 16), Image.Resampling.LANCZOS)

    # Diretório de assets da aplicação
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(base_dir, 'assets')
    icons_dir = os.path.join(assets_dir, 'icons')
    os.makedirs(icons_dir, exist_ok=True)

    with open(os.path.join(assets_dir, 'logo.svg'), 'w', encoding='utf-8') as f:
        f.write(svg_content)

    img_512.save(os.path.join(assets_dir, 'logo.png'), 'PNG')
    img_64.save(os.path.join(assets_dir, 'favicon.png'), 'PNG')
    img_32.save(os.path.join(assets_dir, 'favicon.ico'), format='ICO', sizes=[(32, 32), (16, 16)])
    img_192.save(os.path.join(icons_dir, 'icon-192.png'), 'PNG')
    img_512.save(os.path.join(icons_dir, 'icon-512.png'), 'PNG')
    img_192.save(os.path.join(icons_dir, 'loading-animation.png'), 'PNG')

    # Ícones de empacotamento Mobile / Android (Flet build launcher icons)
    img.save(os.path.join(assets_dir, 'icon.png'), 'PNG')
    img.save(os.path.join(assets_dir, 'icon_android.png'), 'PNG')
    img.save(os.path.join(base_dir, 'icon.png'), 'PNG')

    print('[generate] Assets atualizados com sucesso em mai_finance_flet/assets/ e icones Android gerados (1024x1024)')

    # Substituição no flet_web da venv para erradicação total do logo flet padrão
    venv_dir = os.path.join(base_dir, '..', '.venv', 'Lib', 'site-packages', 'flet_web', 'web')
    venv_dir = os.path.abspath(venv_dir)
    if os.path.exists(venv_dir):
        img_64.save(os.path.join(venv_dir, 'favicon.png'), 'PNG')
        fw_icons = os.path.join(venv_dir, 'icons')
        if os.path.exists(fw_icons):
            img_192.save(os.path.join(fw_icons, 'icon-192.png'), 'PNG')
            img_512.save(os.path.join(fw_icons, 'icon-512.png'), 'PNG')
            img_192.save(os.path.join(fw_icons, 'apple-touch-icon-192.png'), 'PNG')
            img_192.save(os.path.join(fw_icons, 'icon-maskable-192.png'), 'PNG')
            img_512.save(os.path.join(fw_icons, 'icon-maskable-512.png'), 'PNG')
            img_192.save(os.path.join(fw_icons, 'loading-animation.png'), 'PNG')

        index_path = os.path.join(venv_dir, 'index.html')
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                html = f.read()
            html = html.replace('<title>Flet</title>', '<title>MAI Finance</title>')
            html = html.replace('content="Flet"', 'content="MAI Finance"')
            html = html.replace('content="Flet application."', 'content="MAI Finance — Gestão Financeira Pessoal"')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(html)

        manifest_path = os.path.join(venv_dir, 'manifest.json')
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = f.read()
            manifest = manifest.replace('"Flet"', '"MAI Finance"')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(manifest)

        print('[generate] Arquivos flet_web sobrescritos com sucesso! Logo e nomes do Flet erradicados.')

if __name__ == '__main__':
    generate()
