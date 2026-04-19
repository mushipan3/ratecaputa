"""
ラテカピュータ ジョイントアダプタ v1
パーツ1: ラテカセ底部ジョイントアダプタ（台錐なし・断面埋めなし・外形のみ）
"""
import cadquery as cq
from cadquery.occ_impl.exporters.svg import getSVG
from PIL import Image
import io
import re
import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np

# ========== パラメータ ==========
W = 440.0    # アダプタ幅（左右、X方向）
D = 263.0    # アダプタ奥行（前後、Y方向）。前方向 = +Y
T = 2.0      # 基本板厚

CW = 416.0   # 凸部幅（抜き幅）
CD = 216.0   # 凸部奥行（抜き奥行）

FRONT_SOLID = 40.0  # 前端から抜かない長さ
REAR_SOLID = 7.0    # 後端から抜かない長さ
CS = 30.0           # 4隅の台錐エリアサイズ（正方形一辺）

WALL_H = 5.0  # 外周壁高さ（プレート下面から下向き）
WALL_T = 2.0  # 外周壁厚

OUTPUT_DIR = '/home/mushipan3/esp_projects/ratecaputa/cad/'

# ========== 派生値 ==========
LR = (W - CW) / 2      # 左右マージン = 12mm

cut_y_front = D/2 - FRONT_SOLID    # 抜き前端 = 91.5
cut_y_rear  = -D/2 + REAR_SOLID    # 抜き後端 = -124.5
cut_y_ctr   = (cut_y_front + cut_y_rear) / 2  # = -16.5

# ========== モデリング ==========
# 1. ベースプレート
plate = cq.Workplane("XY").box(W, D, T)

# 2. 中央抜き（十字形）
cut_h = T + 2  # 板を貫通するカット高さ

# 縦帯（左右の隅を除く）
c1 = (cq.Workplane("XY")
      .box(CW - 2*CS, CD, cut_h)
      .translate((0, cut_y_ctr, 0)))

# 横帯（前後の隅を除く）
c2 = (cq.Workplane("XY")
      .box(CW, CD - 2*CS, cut_h)
      .translate((0, cut_y_ctr, 0)))

plate = plate.cut(c1.union(c2))

# 3. 外周壁（プレート下面から下に WALL_H mm）
wall_z = -T/2 - WALL_H/2   # 壁中心Z = -1 - 2.5 = -3.5

front_wall = (cq.Workplane("XY")
              .box(W, WALL_T, WALL_H)
              .translate((0,  D/2 - WALL_T/2, wall_z)))

rear_wall  = (cq.Workplane("XY")
              .box(W, WALL_T, WALL_H)
              .translate((0, -D/2 + WALL_T/2, wall_z)))

left_wall  = (cq.Workplane("XY")
              .box(WALL_T, D, WALL_H)
              .translate((-W/2 + WALL_T/2, 0, wall_z)))

right_wall = (cq.Workplane("XY")
              .box(WALL_T, D, WALL_H)
              .translate(( W/2 - WALL_T/2, 0, wall_z)))

result = (plate
          .union(front_wall)
          .union(rear_wall)
          .union(left_wall)
          .union(right_wall))

# ========== STEP出力 ==========
step_path = OUTPUT_DIR + 'joint_adapter_v1.step'
cq.exporters.export(result, step_path)
print(f"STEP exported: {step_path}")


# ========== 三面図 JPEG出力 ==========
def svg_to_pil(svg_bytes):
    """SVGバイト列をPIL Imageに変換（cairo不使用、matplotlib経由）"""
    # SVGをファイルに書いてmatplotlibで読む代わりに
    # PIL SVGはサポート外なのでrsvg-convertを試みる
    import subprocess, tempfile, os
    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as f:
        f.write(svg_bytes if isinstance(svg_bytes, bytes) else svg_bytes.encode())
        tmp_svg = f.name
    tmp_png = tmp_svg.replace('.svg', '.png')
    try:
        subprocess.run(['rsvg-convert', '-f', 'png', '-o', tmp_png, tmp_svg],
                       check=True, capture_output=True)
        img = Image.open(tmp_png)
        return img.copy()
    except Exception:
        return None
    finally:
        for p in [tmp_svg, tmp_png]:
            try: os.unlink(p)
            except: pass


def make_views_matplotlib():
    """matplotlibでパラメータベースの三面図を描画してPIL Imageを返す"""

    # 描画用補助値
    total_h = T + WALL_H   # = 7mm（プレート上面からWALL下端まで）

    # 抜き領域（プレート上面から見た上面図用）
    # 十字形の外形ボックス用
    cutout_lx = -CW/2
    cutout_rx =  CW/2
    cutout_fy = cut_y_front   # = 91.5
    cutout_ry = cut_y_rear    # = -124.5

    fig, axes = plt.subplots(1, 3, figsize=(20, 8))
    fig.patch.set_facecolor('white')

    # ---- 上面図 (XY, Z方向から見下ろす) ----
    ax = axes[0]
    ax.set_title('Top View (from +Z)', fontsize=11)
    ax.set_aspect('equal')
    ax.set_facecolor('#f8f8f8')

    # 外形矩形
    rect_outer = plt.Polygon([
        [-W/2, -D/2], [W/2, -D/2], [W/2, D/2], [-W/2, D/2]
    ], closed=True, fill=True, facecolor='#d0d8e8', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect_outer)

    # 外周壁（上から見ると外縁から内側2mmの帯）
    wall_inner_x = W/2 - WALL_T
    wall_inner_y = D/2 - WALL_T
    rect_wall_hole = plt.Polygon([
        [-wall_inner_x, -wall_inner_y],
        [ wall_inner_x, -wall_inner_y],
        [ wall_inner_x,  wall_inner_y],
        [-wall_inner_x,  wall_inner_y],
    ], closed=True, fill=True, facecolor='#d0d8e8', edgecolor='black', linewidth=0.8, linestyle='--')
    # 壁は外縁部分なので上から見た壁の内縁を点線で示す
    ax.add_patch(rect_wall_hole)

    # 中央の抜き（十字形）→ 白く塗る
    # 縦帯
    rect_c1 = plt.Polygon([
        [-(CW-2*CS)/2, cutout_ry],
        [ (CW-2*CS)/2, cutout_ry],
        [ (CW-2*CS)/2, cutout_fy],
        [-(CW-2*CS)/2, cutout_fy],
    ], closed=True, fill=True, facecolor='white', edgecolor='black', linewidth=1.0)
    ax.add_patch(rect_c1)

    # 横帯
    rect_c2 = plt.Polygon([
        [-CW/2, cutout_ry + CS],
        [ CW/2, cutout_ry + CS],
        [ CW/2, cutout_fy - CS],
        [-CW/2, cutout_fy - CS],
    ], closed=True, fill=True, facecolor='white', edgecolor='black', linewidth=1.0)
    ax.add_patch(rect_c2)

    # 4隅の台錐エリア（グレー）
    corners = [
        (-CW/2, cutout_fy - CS),  # 前左
        ( CW/2 - CS, cutout_fy - CS),  # 前右
        (-CW/2, cutout_ry),  # 後左
        ( CW/2 - CS, cutout_ry),  # 後右
    ]
    for cx, cy in corners:
        rect_corner = plt.Polygon([
            [cx, cy], [cx+CS, cy], [cx+CS, cy+CS], [cx, cy+CS]
        ], closed=True, fill=True, facecolor='#b0b8c8', edgecolor='black', linewidth=1.0)
        ax.add_patch(rect_corner)

    # 寸法線
    ax.annotate('', xy=(W/2, D/2+15), xytext=(-W/2, D/2+15),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(0, D/2+20, f'{W:.0f}', ha='center', va='bottom', fontsize=9)

    ax.annotate('', xy=(W/2+15, D/2), xytext=(W/2+15, -D/2),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(W/2+20, 0, f'{D:.0f}', ha='left', va='center', fontsize=9)

    ax.text(0, D/2+35, '← REAR', ha='center', va='bottom', fontsize=8, color='gray')
    ax.text(0, -D/2-15, 'FRONT →', ha='center', va='top', fontsize=8, color='gray')

    ax.set_xlim(-W/2-40, W/2+40)
    ax.set_ylim(-D/2-30, D/2+50)
    ax.set_xlabel('X [mm]')
    ax.set_ylabel('Y [mm]')
    ax.grid(True, alpha=0.3)

    # ---- 正面図 (XZ, 前 +Y方向から見る) ----
    ax = axes[1]
    ax.set_title('Front View (from +Y / FRONT side)', fontsize=11)
    ax.set_aspect('equal')
    ax.set_facecolor('#f8f8f8')

    # プレート本体（全幅440mm × 板厚2mm）
    # Z: プレート下面=0, 上面=T=2
    plate_rect = plt.Polygon([
        [-W/2, 0], [W/2, 0], [W/2, T], [-W/2, T]
    ], closed=True, fill=True, facecolor='#d0d8e8', edgecolor='black', linewidth=1.5)
    ax.add_patch(plate_rect)

    # 外周壁（下向き、プレート下面から-WALL_H）
    left_wall_rect = plt.Polygon([
        [-W/2, -WALL_H], [-W/2+WALL_T, -WALL_H],
        [-W/2+WALL_T, 0], [-W/2, 0]
    ], closed=True, fill=True, facecolor='#d0d8e8', edgecolor='black', linewidth=1.5)
    ax.add_patch(left_wall_rect)

    right_wall_rect = plt.Polygon([
        [W/2-WALL_T, -WALL_H], [W/2, -WALL_H],
        [W/2, 0], [W/2-WALL_T, 0]
    ], closed=True, fill=True, facecolor='#d0d8e8', edgecolor='black', linewidth=1.5)
    ax.add_patch(right_wall_rect)

    # 前面壁断面（前端=全幅×壁厚）は正面図では全幅に見える
    front_wall_rect = plt.Polygon([
        [-W/2, -WALL_H], [W/2, -WALL_H],
        [W/2, 0], [-W/2, 0]
    ], closed=True, fill=True, facecolor='#c0c8d8', edgecolor='black', linewidth=0.8, linestyle='--')
    ax.add_patch(front_wall_rect)

    # 寸法線
    ax.annotate('', xy=(W/2, T+8), xytext=(-W/2, T+8),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(0, T+12, f'{W:.0f}', ha='center', va='bottom', fontsize=9)

    ax.annotate('', xy=(W/2+15, T), xytext=(W/2+15, -WALL_H),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(W/2+20, (T-WALL_H)/2, f'{T+WALL_H:.0f}', ha='left', va='center', fontsize=9)

    ax.annotate('', xy=(W/2+30, T), xytext=(W/2+30, 0),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(W/2+35, T/2, f'{T:.0f}', ha='left', va='center', fontsize=9)

    ax.set_xlim(-W/2-50, W/2+60)
    ax.set_ylim(-WALL_H-15, T+25)
    ax.set_xlabel('X [mm]')
    ax.set_ylabel('Z [mm]')
    ax.grid(True, alpha=0.3)

    # ---- 側面図 (YZ, 右 +X方向から見る) ----
    ax = axes[2]
    ax.set_title('Side View (from +X / RIGHT side)', fontsize=11)
    ax.set_aspect('equal')
    ax.set_facecolor('#f8f8f8')

    # プレート本体（奥行263mm × 板厚2mm）
    plate_side = plt.Polygon([
        [-D/2, 0], [D/2, 0], [D/2, T], [-D/2, T]
    ], closed=True, fill=True, facecolor='#d0d8e8', edgecolor='black', linewidth=1.5)
    ax.add_patch(plate_side)

    # 前壁断面（+Y側）
    fw = plt.Polygon([
        [D/2-WALL_T, -WALL_H], [D/2, -WALL_H],
        [D/2, 0], [D/2-WALL_T, 0]
    ], closed=True, fill=True, facecolor='#d0d8e8', edgecolor='black', linewidth=1.5)
    ax.add_patch(fw)

    # 後壁断面（-Y側）
    rw = plt.Polygon([
        [-D/2, -WALL_H], [-D/2+WALL_T, -WALL_H],
        [-D/2+WALL_T, 0], [-D/2, 0]
    ], closed=True, fill=True, facecolor='#d0d8e8', edgecolor='black', linewidth=1.5)
    ax.add_patch(rw)

    # 右壁（側面全幅）
    side_wall_rect = plt.Polygon([
        [-D/2, -WALL_H], [D/2, -WALL_H],
        [D/2, 0], [-D/2, 0]
    ], closed=True, fill=True, facecolor='#c0c8d8', edgecolor='black', linewidth=0.8, linestyle='--')
    ax.add_patch(side_wall_rect)

    # 中央抜き部分（上面から見えない部分）
    # 前端から40mmは実体あり（抜きなし）
    # 後端から7mmも実体あり
    # 中央は抜き
    front_solid_y = D/2 - FRONT_SOLID   # = 91.5 (抜き始まり)
    rear_solid_y  = -D/2 + REAR_SOLID   # = -124.5 (抜き終わり)

    # 抜き部分（プレート厚さ内で白く表示）
    cutout_side = plt.Polygon([
        [rear_solid_y, 0], [front_solid_y, 0],
        [front_solid_y, T], [rear_solid_y, T]
    ], closed=True, fill=True, facecolor='white', edgecolor='gray', linewidth=0.8, linestyle=':')
    ax.add_patch(cutout_side)

    # 寸法線
    ax.annotate('', xy=(D/2, T+8), xytext=(-D/2, T+8),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(0, T+12, f'{D:.0f}', ha='center', va='bottom', fontsize=9)

    ax.annotate('', xy=(D/2+15, T), xytext=(D/2+15, -WALL_H),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(D/2+20, (T-WALL_H)/2, f'{T+WALL_H:.0f}', ha='left', va='center', fontsize=9)

    # 前後端の注記
    ax.text(D/2, -WALL_H-8, 'FRONT', ha='center', fontsize=8, color='gray')
    ax.text(-D/2, -WALL_H-8, 'REAR', ha='center', fontsize=8, color='gray')

    ax.set_xlim(-D/2-40, D/2+50)
    ax.set_ylim(-WALL_H-20, T+25)
    ax.set_xlabel('Y [mm]')
    ax.set_ylabel('Z [mm]')
    ax.grid(True, alpha=0.3)

    plt.tight_layout(pad=2.0)

    # PILに変換
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig)
    return img


# 三面図を生成
print("Generating 3-view drawing...")
img = make_views_matplotlib()
jpeg_path = OUTPUT_DIR + 'joint_adapter_v1_3views.jpg'
img.convert('RGB').save(jpeg_path, 'JPEG', quality=92)
print(f"3-view JPEG exported: {jpeg_path}")

print("\n=== 完了 ===")
print(f"STEP: {OUTPUT_DIR}joint_adapter_v1.step")
print(f"三面図: {jpeg_path}")
print(f"\n主要寸法:")
print(f"  外形: {W:.0f} x {D:.0f} mm")
print(f"  板厚: {T:.0f} mm")
print(f"  外周壁: 高さ{WALL_H:.0f}mm x 厚さ{WALL_T:.0f}mm")
print(f"  中央抜き: {CW:.0f} x {CD:.0f} mm（十字形、4隅{CS:.0f}mm角残し）")
print(f"  前端実体: {FRONT_SOLID:.0f}mm, 後端実体: {REAR_SOLID:.0f}mm")
