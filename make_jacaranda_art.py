#!/usr/bin/env python3
"""Dibujos JACARANDA — el árbol morado de México: trazo violeta grueso + tinta + glow."""
import os

A = '#6E5BAE'    # violeta jacaranda
AL = '#9D8BD6'   # violeta claro
INK = '#141210'

def wrap(gid, inner, gy=140):
    return f'''<svg viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">
  <defs><radialGradient id="{gid}" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{A}" stop-opacity="0.42"/>
    <stop offset="55%" stop-color="{A}" stop-opacity="0.14"/>
    <stop offset="100%" stop-color="{A}" stop-opacity="0"/>
  </radialGradient></defs>
  <circle cx="120" cy="{gy}" r="52" fill="url(#{gid})"/>
{inner}
</svg>'''

ART = {}

# RAIZ — el tronco baja y las raíces agarran la tierra
ART['raiz'] = wrap('gra', f'''
  <path d="M120 92 L120 138 M120 138 L94 168 M120 138 L146 168 M120 138 L120 172" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M108 118 L86 132 M132 118 L154 132" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="120" cy="86" r="7" fill="{A}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="64" cy="96" r="2.2" fill="{INK}"/><circle cx="180" cy="112" r="2.4" fill="{INK}"/>
''', gy=132)

# FLOR — la trompeta de jacaranda: cinco pétalos alrededor del centro
ART['flor'] = wrap('gfl', f'''
  <ellipse cx="120" cy="92" rx="10" ry="20" fill="{A}"/>
  <ellipse cx="120" cy="92" rx="10" ry="20" fill="{A}" transform="rotate(72 120 120)"/>
  <ellipse cx="120" cy="92" rx="10" ry="20" fill="{A}" transform="rotate(144 120 120)"/>
  <ellipse cx="120" cy="92" rx="10" ry="20" fill="{AL}" transform="rotate(216 120 120)"/>
  <ellipse cx="120" cy="92" rx="10" ry="20" fill="{AL}" transform="rotate(288 120 120)"/>
  <circle cx="120" cy="120" r="9" fill="{INK}"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="62" cy="94" r="2.2" fill="{INK}"/><circle cx="180" cy="150" r="2.4" fill="{INK}"/>
''', gy=120)

# ABRIL — el árbol entero en flor: tronco de tinta, copa violeta
ART['abril'] = wrap('gab', f'''
  <path d="M120 176 L120 118 M120 138 L102 122 M120 132 L138 118" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>
  <circle cx="120" cy="96" r="34" fill="{A}"/>
  <circle cx="100" cy="86" r="7" fill="{AL}"/>
  <circle cx="132" cy="78" r="5.5" fill="{AL}"/>
  <circle cx="138" cy="104" r="6" fill="{AL}"/>
  <ellipse cx="86" cy="158" rx="4" ry="7" fill="{AL}" transform="rotate(-30 86 158)"/>
  <ellipse cx="158" cy="150" rx="4" ry="7" fill="{A}" transform="rotate(24 158 150)"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="60" cy="102" r="2.2" fill="{INK}"/><circle cx="184" cy="120" r="2.4" fill="{INK}"/>
''', gy=110)

# CALMA — la sombra violeta del árbol, alguien descansa debajo
ART['calma'] = wrap('gca', f'''
  <path d="M78 176 A42 42 0 0 1 162 176" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M96 176 A24 24 0 0 1 144 176" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="120" cy="166" r="6" fill="{INK}"/>
  <ellipse cx="150" cy="132" rx="4" ry="7" fill="{AL}" transform="rotate(30 150 132)"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="62" cy="104" r="2.2" fill="{INK}"/><circle cx="180" cy="118" r="2.4" fill="{INK}"/>
''', gy=146)

# LLUVIA — el pico: la lluvia de pétalos cayendo en diagonal
ART['lluvia'] = wrap('gll', f'''
  <path d="M70 64 L54 108 M104 56 L88 100 M138 60 L122 104 M170 68 L154 112" fill="none" stroke="{AL}" stroke-width="3" stroke-linecap="round" opacity="0.55"/>
  <ellipse cx="76" cy="124" rx="6" ry="11" fill="{A}" transform="rotate(-24 76 124)"/>
  <ellipse cx="112" cy="108" rx="7" ry="12" fill="{A}" transform="rotate(-30 112 108)"/>
  <ellipse cx="146" cy="126" rx="6" ry="11" fill="{AL}" transform="rotate(-18 146 126)"/>
  <ellipse cx="94" cy="152" rx="6" ry="10" fill="{AL}" transform="rotate(-34 94 152)"/>
  <ellipse cx="130" cy="158" rx="6" ry="10" fill="{A}" transform="rotate(-14 130 158)"/>
  <ellipse cx="164" cy="160" rx="5" ry="9" fill="{A}" transform="rotate(-28 164 160)"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="58" cy="150" r="2.2" fill="{INK}"/><circle cx="184" cy="96" r="2.4" fill="{INK}"/>
''', gy=130)

# PETALOS — la alfombra: los pétalos ya en el suelo, uno todavía cayendo
ART['petalos'] = wrap('gpe', f'''
  <ellipse cx="80" cy="170" rx="8" ry="5" fill="{A}"/>
  <ellipse cx="104" cy="172" rx="9" ry="5" fill="{AL}"/>
  <ellipse cx="130" cy="170" rx="8" ry="5" fill="{A}"/>
  <ellipse cx="154" cy="172" rx="7" ry="4.5" fill="{AL}"/>
  <ellipse cx="118" cy="163" rx="7" ry="4.5" fill="{A}"/>
  <ellipse cx="132" cy="104" rx="6" ry="11" fill="{A}" transform="rotate(-26 132 104)"/>
  <path d="M138 78 C134 86 136 94 134 100" fill="none" stroke="{AL}" stroke-width="3" stroke-linecap="round" opacity="0.6"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="62" cy="112" r="2.2" fill="{INK}"/><circle cx="180" cy="130" r="2.4" fill="{INK}"/>
''', gy=150)

os.makedirs('art', exist_ok=True)
for name, svg in ART.items():
    with open(f'art/jaca-{name}.svg', 'w') as f:
        f.write(svg)
    print(f'art/jaca-{name}.svg')
print('done')
