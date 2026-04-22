"""
ラテカピュータ ジョイントアダプタ v2
パーツ1: ラテカセ底部ジョイントアダプタ
v2変更点:
  - 4隅コーナーエリアを凸部に合わせ2mm嵩上げ
  - 台錐（フットプリントR7/上部R6.8、高さ5mm）を各コーナー中心に追加
  - M3クリアランス穴（φ3.2mm）を台錐中心に貫通
"""
import cadquery as cq
from PIL import Image
import io
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import numpy as np

# ========== パラメータ ==========
W = 440.0    # アダプタ幅（左右、X方向）
D = 263.0    # アダプタ奥行（前後、Y方向）、前方向 = +Y
T = 2.0      # 基本板厚

CW = 416.0   # 凸部幅（抜き幅）
CD = 216.0   # 凸部奥行（抜き奥行）

FRONT_SOLID = 40.0  # 前端から抜かない長さ
REAR_SOLID  = 7.0   # 後端から抜かない長さ
CS = 30.0           # 4隅コーナーエリアのサイズ（正方形一辺）

WALL_H = 5.0   # 外周壁高さ（プレート下面から下向き）
WALL_T = 2.0   # 外周壁厚

CONVEX_H = 2.0   # ラテカセ底面凸部の高さ（コーナー嵩上げ量）

FRUST_R1 = 7.0   # 台錐底面半径
FRUST_R2 = 6.8   # 台錐上面半径
FRUST_H  = 5.0   # 台錐高さ
M3_D     = 3.2   # M3クリアランス穴径

OUTPUT_DIR = '/home/mushipan3/esp_projects/ratecaputa/cad/'

# ========== 派生値 ==========
LR = (W - CW) / 2      # 左右マージン = 12.0mm

cut_y_front = D/2 - FRONT_SOLID    # 抜き前端 = 91.5
cut_y_rear  = -D/2 + REAR_SOLID    # 抜き後端 = -124.5
cut_y_ctr   = (cut_y_front + cut_y_rear) / 2   # = -16.5
cut_h_box   = T + 2  # カット用ボックス高さ（板貫通）

# コーナー中心座標（4隅）
CX_R = CW/2 - CS/2              # = 193.0
CY_F = cut_y_front - CS/2       # = 76.5  (前側)
CY_R = cut_y_rear  + CS/2       # = -109.5 (後側)

CORNER_CENTERS = [
    (-CX_R,  CY_F),   # 前・左
    ( CX_R,  CY_F),   # 前・右
    (-CX_R,  CY_R),   # 後・左
    ( CX_R,  CY_R),   # 後・右
]

# 各Z高さ（プレート中心Z=0、プレート上面=+T/2、下面=-T/2）
pad_z_ctr    = T/2 + CONVEX_H/2          # 嵩上げパッド中心Z = 2.0
frust_base_z = T/2 + CONVEX_H            # 台錐底面Z = 3.0
hole_depth   = T/2 + frust_base_z + FRUST_H   # M3穴の長さ = 1+3+5 = 9.0mm

# ========== モデリング ==========

# 1. ベースプレート
plate = cq.Workplane("XY").box(W, D, T)

# 2. 中央抜き（十字形）
c1 = (cq.Workplane("XY")
      .box(CW - 2*CS, CD, cut_h_box)
      .translate((0, cut_y_ctr, 0)))
c2 = (cq.Workplane("XY")
      .box(CW, CD - 2*CS, cut_h_box)
      .translate((0, cut_y_ctr, 0)))
plate = plate.cut(c1.union(c2))

# 3. 外周壁（プレート下面から下に WALL_H mm）
wall_z = -T/2 - WALL_H/2

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

# 4. 4隅コーナー嵩上げパッド（CONVEX_H=2mm）
for cx, cy in CORNER_CENTERS:
    pad = (cq.Workplane("XY")
           .box(CS, CS, CONVEX_H)
           .translate((cx, cy, pad_z_ctr)))
    result = result.union(pad)

# 5. 台錐（フラスタム）＋ M3穴
for cx, cy in CORNER_CENTERS:
    # 台錐: 底面R7 → 上面R6.8、高さ5mm
    frustum = (cq.Workplane("XY")
               .circle(FRUST_R1)
               .workplane(offset=FRUST_H)
               .circle(FRUST_R2)
               .loft()
               .translate((cx, cy, frust_base_z)))
    result = result.union(frustum)

    # M3クリアランス穴（板底から台錐頂部まで貫通）
    hole = (cq.Workplane("XY")
            .circle(M3_D / 2)
            .extrude(hole_depth)
            .translate((cx, cy, -T/2)))
    result = result.cut(hole)

# ========== STEP出力 ==========
step_path = OUTPUT_DIR + 'joint_adapter_v2.step'
cq.exporters.export(result, step_path)
print(f"STEP exported: {step_path}")


# ========== 三面図 JPEG出力 ==========
def make_views_matplotlib():
    fig, axes = plt.subplots(1, 3, figsize=(22, 9))
    fig.patch.set_facecolor('white')
    fig.suptitle('Joint Adapter v2 - 3 View Drawing\n'
                 'Unit: mm  |  Plate: 440x263x2  |  Wall: H5/T2  |  Corner pads +2mm  |  Frustum R7->6.8/H5  |  M3 hole',
                 fontsize=10)

    # --- 上面図 (Top View, +Z から見下ろす) ---
    ax = axes[0]
    ax.set_title('Top View  (from +Z)', fontsize=11)
    ax.set_aspect('equal')
    ax.set_facecolor('#f8f8f8')

    # 外形
    ax.add_patch(plt.Polygon(
        [[-W/2,-D/2],[W/2,-D/2],[W/2,D/2],[-W/2,D/2]],
        closed=True, facecolor='#d0d8e8', edgecolor='black', lw=1.5))

    # 外周壁内縁（点線）
    wix, wiy = W/2-WALL_T, D/2-WALL_T
    ax.add_patch(plt.Polygon(
        [[-wix,-wiy],[wix,-wiy],[wix,wiy],[-wix,wiy]],
        closed=True, fill=False, edgecolor='black', lw=0.8, linestyle='--'))

    # 中央抜き（白）
    ax.add_patch(plt.Polygon(
        [[-(CW-2*CS)/2, cut_y_rear],[(CW-2*CS)/2, cut_y_rear],
         [(CW-2*CS)/2, cut_y_front],[-(CW-2*CS)/2, cut_y_front]],
        closed=True, facecolor='white', edgecolor='black', lw=1.0))
    ax.add_patch(plt.Polygon(
        [[-CW/2, cut_y_rear+CS],[CW/2, cut_y_rear+CS],
         [CW/2,  cut_y_front-CS],[-CW/2, cut_y_front-CS]],
        closed=True, facecolor='white', edgecolor='black', lw=1.0))

    # 4隅コーナー（濃青 = 嵩上げエリア）
    for cx, cy in CORNER_CENTERS:
        ax.add_patch(plt.Polygon(
            [[cx-CS/2, cy-CS/2],[cx+CS/2, cy-CS/2],
             [cx+CS/2, cy+CS/2],[cx-CS/2, cy+CS/2]],
            closed=True, facecolor='#8090b8', edgecolor='black', lw=1.0))
        # 台錐外周（点線円）
        ax.add_patch(plt.Circle((cx, cy), FRUST_R1,
                                fill=False, edgecolor='black', lw=1.0, linestyle='--'))
        # M3穴（白丸）
        ax.add_patch(plt.Circle((cx, cy), M3_D/2,
                                facecolor='white', edgecolor='black', lw=0.8))

    # 寸法線
    ax.annotate('', xy=(W/2, D/2+18), xytext=(-W/2, D/2+18),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(0, D/2+23, f'{W:.0f}', ha='center', va='bottom', fontsize=9)
    ax.annotate('', xy=(W/2+18, D/2), xytext=(W/2+18, -D/2),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(W/2+23, 0, f'{D:.0f}', ha='left', va='center', fontsize=9)

    ax.text(0, D/2+35, '<- REAR', ha='center', fontsize=8, color='gray')
    ax.text(0, -D/2-15, 'FRONT ->', ha='center', fontsize=8, color='gray')

    ax.set_xlim(-W/2-45, W/2+50)
    ax.set_ylim(-D/2-30, D/2+55)
    ax.set_xlabel('X [mm]')
    ax.set_ylabel('Y [mm]')
    ax.grid(True, alpha=0.3)

    # --- 正面図 (Front View, +Y から見る) ---
    ax = axes[1]
    ax.set_title('Front View  (from +Y / FRONT)', fontsize=11)
    ax.set_aspect('equal')
    ax.set_facecolor('#f8f8f8')

    # プレート本体（全幅 × T）
    ax.add_patch(plt.Polygon(
        [[-W/2, 0],[W/2, 0],[W/2, T],[-W/2, T]],
        closed=True, facecolor='#d0d8e8', edgecolor='black', lw=1.5))

    # 外周壁（左右）
    for sx in [-1, 1]:
        x0 = sx * W/2 - (WALL_T if sx > 0 else 0)
        x1 = sx * W/2 + (0 if sx > 0 else WALL_T)
        ax.add_patch(plt.Polygon(
            [[min(x0,x1),-WALL_H],[max(x0,x1),-WALL_H],
             [max(x0,x1),0],[min(x0,x1),0]],
            closed=True, facecolor='#d0d8e8', edgecolor='black', lw=1.5))

    # 前壁（点線、手前なので全幅）
    ax.add_patch(plt.Polygon(
        [[-W/2,-WALL_H],[W/2,-WALL_H],[W/2,0],[-W/2,0]],
        closed=True, facecolor='#c0c8d8', edgecolor='black', lw=0.8, linestyle='--'))

    # コーナー嵩上げ部（前側2コーナー）
    for cx, cy in [c for c in CORNER_CENTERS if c[1] == CY_F]:
        ax.add_patch(plt.Polygon(
            [[cx-CS/2, T],[cx+CS/2, T],[cx+CS/2, T+CONVEX_H],[cx-CS/2, T+CONVEX_H]],
            closed=True, facecolor='#8090b8', edgecolor='black', lw=1.0))
        # 台錐（台形で表現）
        fz_bot = T + CONVEX_H
        fz_top = fz_bot + FRUST_H
        ax.add_patch(plt.Polygon(
            [[cx-FRUST_R1, fz_bot],[cx+FRUST_R1, fz_bot],
             [cx+FRUST_R2, fz_top],[cx-FRUST_R2, fz_top]],
            closed=True, facecolor='#8090b8', edgecolor='black', lw=1.0))
        # M3穴（点線垂直線）
        ax.plot([cx, cx], [-T/2, fz_top], color='white', lw=1.5, linestyle=':')

    # 寸法
    total_h = T + CONVEX_H + FRUST_H  # = 9mm
    ax.annotate('', xy=(W/2, T+CONVEX_H+FRUST_H+5), xytext=(-W/2, T+CONVEX_H+FRUST_H+5),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(0, total_h+9, f'{W:.0f}', ha='center', va='bottom', fontsize=9)
    ax.annotate('', xy=(W/2+18, T), xytext=(W/2+18, -WALL_H),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(W/2+22, (T-WALL_H)/2, f'{T+WALL_H:.0f}', ha='left', fontsize=9)
    ax.annotate('', xy=(W/2+32, T), xytext=(W/2+32, total_h),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(W/2+36, (T+total_h)/2, f'{total_h:.0f}', ha='left', fontsize=9)
    ax.text(W/2+36, (T+total_h)/2 - 4, '(corner)', ha='left', fontsize=7, color='gray')

    ax.set_xlim(-W/2-55, W/2+70)
    ax.set_ylim(-WALL_H-12, total_h+18)
    ax.set_xlabel('X [mm]')
    ax.set_ylabel('Z [mm]')
    ax.grid(True, alpha=0.3)

    # --- 側面図 (Side View, +X から見る) ---
    ax = axes[2]
    ax.set_title('Side View  (from +X / RIGHT)', fontsize=11)
    ax.set_aspect('equal')
    ax.set_facecolor('#f8f8f8')

    # プレート本体
    ax.add_patch(plt.Polygon(
        [[-D/2, 0],[D/2, 0],[D/2, T],[-D/2, T]],
        closed=True, facecolor='#d0d8e8', edgecolor='black', lw=1.5))

    # 外周壁（前後）
    for sy, label in [(1, 'FRONT'), (-1, 'REAR')]:
        y0 = sy * D/2 - (WALL_T if sy > 0 else 0)
        y1 = sy * D/2 + (0 if sy > 0 else WALL_T)
        ax.add_patch(plt.Polygon(
            [[min(y0,y1),-WALL_H],[max(y0,y1),-WALL_H],
             [max(y0,y1),0],[min(y0,y1),0]],
            closed=True, facecolor='#d0d8e8', edgecolor='black', lw=1.5))
        ax.text(sy*D/2, -WALL_H-7, label, ha='center', fontsize=8, color='gray')

    # 右壁（点線全幅）
    ax.add_patch(plt.Polygon(
        [[-D/2,-WALL_H],[D/2,-WALL_H],[D/2,0],[-D/2,0]],
        closed=True, facecolor='#c0c8d8', edgecolor='black', lw=0.8, linestyle='--'))

    # 抜き部分（板厚内で白く）
    ax.add_patch(plt.Polygon(
        [[cut_y_rear, 0],[cut_y_front, 0],[cut_y_front, T],[cut_y_rear, T]],
        closed=True, facecolor='white', edgecolor='gray', lw=0.8, linestyle=':'))

    # コーナー嵩上げ・台錐（前後それぞれ）
    for cy_pos, label_y in [(CY_F, cut_y_front), (CY_R, cut_y_rear)]:
        # 嵩上げパッドのY範囲（コーナー中心±CS/2）
        pad_y0 = cy_pos - CS/2
        pad_y1 = cy_pos + CS/2
        ax.add_patch(plt.Polygon(
            [[pad_y0, T],[pad_y1, T],[pad_y1, T+CONVEX_H],[pad_y0, T+CONVEX_H]],
            closed=True, facecolor='#8090b8', edgecolor='black', lw=1.0))
        # 台錐（台形）
        fz_bot = T + CONVEX_H
        fz_top = fz_bot + FRUST_H
        ax.add_patch(plt.Polygon(
            [[cy_pos-FRUST_R1, fz_bot],[cy_pos+FRUST_R1, fz_bot],
             [cy_pos+FRUST_R2, fz_top],[cy_pos-FRUST_R2, fz_top]],
            closed=True, facecolor='#8090b8', edgecolor='black', lw=1.0))
        # M3穴
        ax.plot([cy_pos, cy_pos], [-T/2, fz_top], color='white', lw=1.5, linestyle=':')

    # 寸法
    ax.annotate('', xy=(D/2, T+15), xytext=(-D/2, T+15),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(0, T+18, f'{D:.0f}', ha='center', va='bottom', fontsize=9)
    ax.annotate('', xy=(D/2+18, T), xytext=(D/2+18, -WALL_H),
                arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(D/2+22, (T-WALL_H)/2, f'{T+WALL_H:.0f}', ha='left', fontsize=9)
    # FRONT_SOLID / REAR_SOLID 寸法
    ax.annotate('', xy=(D/2, -WALL_H-13), xytext=(cut_y_front, -WALL_H-13),
                arrowprops=dict(arrowstyle='<->', color='navy'))
    ax.text((D/2+cut_y_front)/2, -WALL_H-17, f'{FRONT_SOLID:.0f}', ha='center', fontsize=8, color='navy')
    ax.annotate('', xy=(cut_y_rear, -WALL_H-13), xytext=(-D/2, -WALL_H-13),
                arrowprops=dict(arrowstyle='<->', color='navy'))
    ax.text((cut_y_rear-D/2)/2, -WALL_H-17, f'{REAR_SOLID:.0f}', ha='center', fontsize=8, color='navy')

    ax.set_xlim(-D/2-40, D/2+45)
    ax.set_ylim(-WALL_H-28, T+CONVEX_H+FRUST_H+12)
    ax.set_xlabel('Y [mm]')
    ax.set_ylabel('Z [mm]')
    ax.grid(True, alpha=0.3)

    plt.tight_layout(pad=2.0)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    img = Image.open(buf).copy()
    plt.close(fig)
    return img


print("Generating 3-view drawing...")
img = make_views_matplotlib()
jpeg_path = OUTPUT_DIR + 'joint_adapter_v2_3views.jpg'
img.convert('RGB').save(jpeg_path, 'JPEG', quality=92)
print(f"3-view JPEG exported: {jpeg_path}")

print("\n=== 完了 ===")
print(f"STEP: {step_path}")
print(f"三面図: {jpeg_path}")
print(f"\n主要寸法:")
print(f"  外形: {W:.0f} x {D:.0f} mm")
print(f"  板厚: {T:.0f} mm / 外周壁: H{WALL_H:.0f} x T{WALL_T:.0f} mm")
print(f"  中央抜き: {CW:.0f} x {CD:.0f} mm（十字形、4隅{CS:.0f}mm角残し）")
print(f"  前端実体: {FRONT_SOLID:.0f}mm / 後端実体: {REAR_SOLID:.0f}mm")
print(f"  コーナー嵩上げ: {CONVEX_H:.0f}mm")
print(f"  台錐: R{FRUST_R1} -> R{FRUST_R2} / H{FRUST_H:.0f}mm / M3穴φ{M3_D}")
print(f"  コーナー中心位置: X=±{CX_R:.1f}mm, Y=+{CY_F:.1f}mm(前)/-{abs(CY_R):.1f}mm(後)")
