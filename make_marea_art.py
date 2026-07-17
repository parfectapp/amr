#!/usr/bin/env python3
"""Dibujos MAREA — mismo lenguaje que GUERRERO (tinta + acento + glow), violeta bruma."""
import os

A = '#6E5BAE'    # violeta bruma
AL = '#9D8BD6'   # violeta claro
INK = '#141210'

def wrap(gid, inner, gy=150):
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

ART['orilla'] = wrap('gor', f'''
  <path d="M120 96 A34 34 0 0 1 154 130 L86 130 A34 34 0 0 1 120 96 Z" fill="{A}"/>
  <rect x="46" y="128" width="148" height="5" rx="2.5" fill="{INK}"/>
  <path d="M62 160 C74 152 86 168 98 160 C110 152 122 168 134 160" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <path d="M96 184 C108 176 120 192 132 184 C144 176 156 192 168 184" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="70" cy="84" r="2.2" fill="{INK}"/><circle cx="176" cy="102" r="2.4" fill="{INK}"/>
''', gy=130)

ART['brisa'] = wrap('gbr', f'''
  <path d="M52 110 C92 96 138 124 186 106" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
  <path d="M60 142 C100 128 140 156 182 140" fill="none" stroke="{A}" stroke-width="5" stroke-linecap="round"/>
  <path d="M72 172 C106 160 138 182 170 170" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="186" cy="106" r="5" fill="{A}"/>
  <circle cx="64" cy="76" r="2.2" fill="{INK}"/><circle cx="172" cy="206" r="2.2" fill="{INK}"/>
''')

ART['sal'] = wrap('gsa', f'''
  <path d="M120 78 L146 122 L120 166 L94 122 Z" fill="{INK}"/>
  <path d="M120 96 L134 122 L120 148 L106 122 Z" fill="{A}"/>
  <path d="M74 150 L88 172 L74 194 L60 172 Z" fill="{A}"/>
  <path d="M166 146 L182 170 L166 194 L150 170 Z" fill="{INK}"/>
  <circle cx="120" cy="122" r="4" fill="#EAE6DF"/>
  <circle cx="78" cy="86" r="2.2" fill="{INK}"/><circle cx="184" cy="110" r="2.2" fill="{INK}"/>
''')

ART['coral'] = wrap('gco', f'''
  <ellipse cx="120" cy="206" rx="44" ry="7" fill="{INK}" opacity="0.05"/>
  <path d="M120 204 L120 96 M120 150 C102 144 92 128 90 110 M120 162 C140 156 150 140 152 120 M120 118 C110 110 106 100 106 88 M152 120 C158 110 158 100 154 92" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>
  <circle cx="120" cy="92" r="7" fill="{A}"/>
  <circle cx="90" cy="106" r="6" fill="{A}"/>
  <circle cx="106" cy="84" r="5" fill="{AL}"/>
  <circle cx="154" cy="88" r="6" fill="{AL}"/>
  <circle cx="66" cy="150" r="2.2" fill="{INK}"/><circle cx="178" cy="168" r="2.4" fill="{INK}"/>
''', gy=140)

ART['laguna'] = wrap('gla', f'''
  <ellipse cx="120" cy="146" rx="74" ry="30" fill="none" stroke="{INK}" stroke-width="4"/>
  <ellipse cx="120" cy="146" rx="50" ry="19" fill="none" stroke="{A}" stroke-width="4"/>
  <ellipse cx="120" cy="146" rx="26" ry="9" fill="none" stroke="{AL}" stroke-width="3.5"/>
  <circle cx="120" cy="146" r="5" fill="{INK}"/>
  <circle cx="72" cy="82" r="2.2" fill="{INK}"/><circle cx="170" cy="88" r="2.4" fill="{INK}"/>
''', gy=146)

ART['luciernaga'] = wrap('glu', f'''
  <path d="M96 208 C96 168 106 138 124 112" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>
  <path d="M96 176 C86 168 80 158 78 146" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
  <circle cx="140" cy="86" r="10" fill="{A}"/><circle cx="140" cy="86" r="17" fill="{A}" opacity="0.25"/>
  <circle cx="86" cy="112" r="6" fill="{AL}"/><circle cx="86" cy="112" r="11" fill="{AL}" opacity="0.25"/>
  <circle cx="168" cy="140" r="5" fill="{A}"/><circle cx="168" cy="140" r="9" fill="{A}" opacity="0.25"/>
  <circle cx="64" cy="196" r="2.2" fill="{INK}"/>
''', gy=120)

ART['cenote'] = wrap('gce', f'''
  <circle cx="120" cy="140" r="58" fill="{INK}"/>
  <circle cx="120" cy="140" r="42" fill="{A}"/>
  <circle cx="120" cy="140" r="26" fill="{INK}"/>
  <path d="M120 46 L120 128" stroke="#EAE6DF" stroke-width="4" stroke-linecap="round" opacity="0.85"/>
  <circle cx="120" cy="140" r="7" fill="#EAE6DF"/>
  <circle cx="60" cy="88" r="2.2" fill="{INK}"/><circle cx="184" cy="102" r="2.4" fill="{INK}"/>
''', gy=140)

ART['marejada'] = wrap('gma', f'''
  <path d="M60 176 A66 66 0 0 1 126 110 A30 30 0 0 1 156 140 A16 16 0 0 1 140 156 A8 8 0 0 1 132 148" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round"/>
  <path d="M84 176 A44 44 0 0 1 118 134" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <rect x="46" y="176" width="148" height="5" rx="2.5" fill="{INK}"/>
  <circle cx="76" cy="92" r="2.2" fill="{INK}"/><circle cx="182" cy="108" r="2.4" fill="{INK}"/>
''', gy=134)

ART['estela'] = wrap('ges', f'''
  <path d="M120 82 L134 108 L106 108 Z" fill="{INK}"/>
  <path d="M112 124 L74 196 M128 124 L166 196" fill="none" stroke="{A}" stroke-width="5" stroke-linecap="round"/>
  <path d="M120 128 L120 178" fill="none" stroke="{AL}" stroke-width="4" stroke-linecap="round" stroke-dasharray="2 12"/>
  <circle cx="66" cy="96" r="2.2" fill="{INK}"/><circle cx="176" cy="86" r="2.4" fill="{INK}"/>
''', gy=140)

ART['horizonte'] = wrap('gho', f'''
  <path d="M86 132 A34 34 0 0 1 154 132 Z" fill="{A}"/>
  <rect x="46" y="130" width="148" height="5" rx="2.5" fill="{INK}"/>
  <path d="M78 158 L102 158 M116 158 L142 158 M156 158 L166 158" stroke="{AL}" stroke-width="4" stroke-linecap="round"/>
  <path d="M92 180 L112 180 M126 180 L148 180" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="70" cy="86" r="2.2" fill="{INK}"/><circle cx="174" cy="98" r="2.4" fill="{INK}"/>
''', gy=132)

os.makedirs('art', exist_ok=True)
for name, svg in ART.items():
    with open(f'art/marea-{name}.svg', 'w') as f:
        f.write(svg)
    print(f'art/marea-{name}.svg')
print('done')
