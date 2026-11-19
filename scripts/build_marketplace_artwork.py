"""Build bilingual 1600x900 SVG banners using actual Box Studio geometry.

Artwork template adapted from Orca Gear Studio (MIT; see LICENSE).
Copyright (c) 2026 Orca Gear Studio (shared artwork template).
Copyright (c) 2026 Orca Vase Studio (shared artwork template).
Copyright (c) 2026 Orca Box Studio (Box artwork).
This is a development tool; it does not install or modify the plugin.
"""
from __future__ import annotations

import base64
import hashlib
import json
from html import escape
from pathlib import Path
import subprocess
import sys
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from box_studio.mesh_generator import generate_box_mesh, latch_open_transform
from box_studio.schema import normalize_params
import numpy as np

OUT = ROOT / "assets" / "marketplace"
ACCENT = "#15dfae"
LANG = "en"
MODEL_RENDERS = {}


def tr(en, pt):
    return pt if LANG == "pt-BR" else en


def text(x, y, value, size=26, color="#eaf4f0", weight=400, spacing=0):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" letter-spacing="{spacing}">{escape(value)}</text>'


def right_text(x, y, value, size=18, color="#9cb8af", weight=400, spacing=1.5):
    return text(x,y,value,size,color,weight,spacing).replace('<text ', '<text text-anchor="end" ', 1)


def frame(section):
    return ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">',
            '<style>text{font-family:Segoe UI,Arial,sans-serif}</style>',
            '<defs><radialGradient id="glow"><stop stop-color="#17483e"/><stop offset="1" stop-color="#11191b"/></radialGradient></defs>',
            '<rect width="1600" height="900" fill="#11191b"/>',
            '<ellipse cx="1200" cy="450" rx="660" ry="500" fill="url(#glow)"/>',
            '<path d="M64 112H1536M64 830H1536" stroke="#30443f"/>',
            text(64,71,"ORCA BOX STUDIO",25,ACCENT,700,3),
            right_text(1536,71,section),
            text(64,871,tr("PARAMETRIC BOXES  /  NATIVE ORCASLICER PLUGIN","CAIXAS PARAMÉTRICAS  /  PLUGIN NATIVO DO ORCASLICER"),16,"#9cb8af",400,1.5),
            right_text(1536,854,tr("FREE + OPEN SOURCE","GRATUITO + CÓDIGO ABERTO"),14,ACCENT,600),
            right_text(1536,885,"By @VictorFernande",20,"#eaf4f0",600,0)]


def scene_svg(items, x, y, width, height, azimuth=-55, altitude=28):
    """Embed a true depth-buffer render of the actual connected mesh surfaces."""
    vertices, triangles, colors, centres, offset = [], [], [], [], 0
    for mesh, color, translation in items:
        verts = mesh.vertices.astype(float) + np.asarray(translation)
        vertices.append(verts)
        triangles.append(mesh.triangles + offset)
        colors.extend([color] * len(mesh.triangles))
        centre = ((verts.min(axis=0)+verts.max(axis=0))/2).tolist()
        centres.extend([centre] * len(mesh.triangles))
        offset += len(verts)
    scene = {'vertices':np.concatenate(vertices).tolist(),
             'triangles':np.concatenate(triangles).tolist(), 'colours':colors, 'centres':centres,
             'width':round(width*2), 'height':round(height*2),
             'azimuth':azimuth, 'altitude':altitude}
    encoded = json.dumps(scene, separators=(',', ':'))
    key = hashlib.sha256(encoded.encode()).hexdigest()
    if key not in MODEL_RENDERS:
        target = OUT/'sources'/f'model-{len(MODEL_RENDERS)+1:02d}.png'
        result = subprocess.run(['node',str(ROOT/'scripts/render_marketplace_models.cjs'),str(target)],
                                input=encoded,text=True,capture_output=True,check=True)
        print('Depth-buffer model render: '+result.stdout.strip())
        MODEL_RENDERS[key] = base64.b64encode(target.read_bytes()).decode('ascii')
    return f'<image href="data:image/png;base64,{MODEL_RENDERS[key]}" x="{x}" y="{y}" width="{width}" height="{height}"/>'


def write(name, parts):
    target = OUT/(name+'.svg')
    target.write_text('\n'.join(parts)+'\n</svg>\n', encoding='utf-8', newline='\n')
    print(f'{target.name}: {target.stat().st_size:,} bytes')


def main():
    global LANG
    OUT.mkdir(parents=True, exist_ok=True)
    green, copper, slate = (21, 223, 174), (239, 176, 99), (107, 141, 136)
    bin_params = normalize_params({'style':'open_bin', 'width_x':160, 'depth_y':110, 'height_z':70})
    open_bin = generate_box_mesh(bin_params)
    snap_params = normalize_params({'style':'snap_latch','width_x':160,'depth_y':95,'height_z':35})
    snap = [(generate_box_mesh(snap_params,'base'),green,(0,0,0)),
            (generate_box_mesh(snap_params,'lid'),slate,(0,0,48))]
    for part in ('clip_left','clip_right'):
        mesh = generate_box_mesh(snap_params,part)
        opened = replace(mesh,vertices=latch_open_transform(mesh.vertices,snap_params,part,90))
        snap.append((opened,copper,(0,0,0)))
    # Derive the stacking offset from the validated geometry contract.
    from box_studio.mesh_generator import stacking_pose_z
    stack_params = normalize_params({'style':'stackable_bin','width_x':150,'depth_y':100,'height_z':65,
                                     'front_access_width':100,'front_access_drop':35})
    tall_params = normalize_params(stack_params | {'height_z':85})
    stack_mesh, tall_mesh = generate_box_mesh(stack_params), generate_box_mesh(tall_params)
    stack = [(stack_mesh,slate,(0,0,0)), (tall_mesh,green,(0,0,stacking_pose_z(stack_params,tall_params)))]
    for LANG in ('en','pt-BR'):
        capture = OUT/f'source-workspace-{LANG}.png'
        if not capture.is_file():
            raise FileNotFoundError('Supply the reviewed, generic-printer Box workspace captures first.')
        screenshot = base64.b64encode(capture.read_bytes()).decode('ascii')
        p = frame(tr('01 / ORGANIZE','01 / ORGANIZE'))
        p += [text(64,203,tr('FROM PROJECT TO STORAGE','DO PROJETO À ORGANIZAÇÃO'),21,ACCENT,600,2),
              text(58,308,tr('YOUR BOX.','CAIXAS.'),85,weight=750),
              text(58,412,tr('YOUR SIZE.','NA SUA MEDIDA.'),tr(85,69),ACCENT,750),
              text(64,498,tr('Set the dimensions. Keep the details.','Ajuste as medidas. Cuide dos detalhes.'),tr(30,27)),
              text(64,545,tr('Create without leaving OrcaSlicer.','Crie sem sair do OrcaSlicer.'),28,'#9cb8af'),
              '<rect x="64" y="608" width="602" height="56" rx="28" fill="#19362e" stroke="#2e6b57"/>',
              text(87,644,tr('OPEN BINS  /  CASES  /  ENCLOSURES','CAIXAS ABERTAS  /  ESTOJOS  /  PROJETOS'),tr(20,18),ACCENT,600),
              text(64,746,tr('REAL HAND-GRIP OPENINGS','ABERTURAS REAIS PARA AS MÃOS'),21,weight=700),
              text(64,786,tr('Width, height and choice of faces.','Largura, altura e escolha das faces.'),25,'#9cb8af'),
              scene_svg([(open_bin,green,(0,0,0))],760,186,780,568,altitude=35),
              right_text(1510,790,tr('ACTUAL PLUGIN GEOMETRY','GEOMETRIA REAL DO PLUGIN'),16)]
        write('01-box-studio-'+LANG,p)

        p = frame(tr('02 / REMOVABLE LID','02 / TAMPA REMOVÍVEL'))
        p += [text(64,239,tr('A LID.','UMA TAMPA.'),tr(74,68),weight=750),
              text(64,335,tr('TWO LEVERS.','DOIS FECHOS.'),tr(70,68),ACCENT,750),
              text(64,421,tr('Four separate printable pieces.','Quatro peças separadas para imprimir.'),tr(30,26)),
              text(64,468,tr('Levers pivot on the base to release the lid.','Fechos giram na base e liberam a tampa.'),tr(24,24),'#9cb8af'),
              text(64,586,tr('01   MOUNT LEVERS ON THE BASE','01   MONTE OS FECHOS NA BASE'),22,ACCENT,600),
              text(64,650,tr('02   RELEASE, THEN LIFT THE LID','02   SOLTE E LEVANTE A TAMPA'),22,ACCENT,600),
              text(64,713,tr('03   CLEARANCE IN MILLIMETERS','03   FOLGA EM MILÍMETROS'),22,ACCENT,600),
              text(64,785,tr('Calibrate the fit for your material and printer.','Calibre o encaixe para seu material e impressora.'),tr(23,21),'#9cb8af'),
              scene_svg(snap,770,155,760,592,altitude=28),
              right_text(1510,790,tr('EXPLODED VIEW · ACTUAL PARTS','VISTA EXPLODIDA · PEÇAS REAIS'),16)]
        write('02-removable-lid-'+LANG,p)

        p = frame(tr('03 / STACK','03 / EMPILHE'))
        p += [text(64,242,tr('ORGANIZE.','ORGANIZE.'),77,weight=750),
              text(64,342,tr('STACK.','EMPILHE.'),77,ACCENT,750),
              text(64,441,tr('One footprint. Different heights.','A mesma base. Alturas diferentes.'),tr(30,29)),
              text(64,488,tr('Front access with a lowered opening.','Acesso pela frente rebaixada.'),27,'#9cb8af'),
              text(64,605,tr('01   GUIDED STACKING FOOT','01   PÉ DE ENCAIXE GUIADO'),22,ACCENT,600),
              text(64,671,tr('02   CONFIGURABLE FRONT ACCESS','02   ABERTURA FRONTAL AJUSTÁVEL'),tr(22,21),ACCENT,600),
              text(64,783,tr('Match the mating dimensions before stacking.','Mantenha as medidas de encaixe compatíveis.'),tr(23,22),'#9cb8af'),
              scene_svg(stack,835,155,655,614,azimuth=-65,altitude=22),
              right_text(1510,795,tr('ACTUAL PLUGIN GEOMETRY','GEOMETRIA REAL DO PLUGIN'),16)]
        write('03-stackable-container-'+LANG,p)

        p = frame(tr('04 / PRINT-IN-PLACE','04 / PRINT-IN-PLACE'))
        p += [text(64,245,tr('PRINT OPEN.','IMPRIMA'),tr(65,74),weight=750),
              text(64,339,tr('FOLD','JÁ'),74,ACCENT,750),
              text(64,432,tr('CLOSED.','ARTICULADO.'),tr(74,63),ACCENT,750),
              text(64,529,tr('Equal base and lid heights.','Base e tampa da mesma altura.'),tr(29,27)),
              text(64,581,tr('180° open layout preserves both hinge halves.','Abertura de 180° preserva a articulação.'),tr(23,24),'#9cb8af'),
              text(64,680,tr('STL / 3MF AS ONE OPEN ASSEMBLY','STL / 3MF EM CONJUNTO ABERTO'),tr(22,21),ACCENT,600),
              text(64,784,tr('Calibrate hinge clearance before final use.','Calibre a folga antes do uso final.'),tr(23,25),'#9cb8af'),
              '<rect x="704" y="172" width="832" height="584" rx="14" fill="#1d2528" stroke="#496057"/>',
              f'<image href="data:image/png;base64,{screenshot}" x="716" y="184" width="808" height="560" preserveAspectRatio="xMidYMid meet"/>',
              right_text(1510,795,tr('ACTUAL PLUGIN SCREENSHOT','CAPTURA REAL DO PLUGIN'),16)]
        write('04-workspace-export-'+LANG,p)


if __name__ == '__main__':
    main()
