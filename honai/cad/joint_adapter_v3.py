"""
ラテカピュータ ジョイントアダプタ v3
v2からの変更点:
  - 台錐穴位置 X: ±193mm → ±190mm（前後、重心調整）
  - 外周壁厚: 2.0mm → 2.5mm（U字パーツとの干渉回避）
"""
import cadquery as cq

W = 440.0; D = 263.0; T = 2.0
CW = 416.0; CD = 216.0
FRONT_SOLID = 40.0; REAR_SOLID = 7.0; CS = 30.0
WALL_H = 5.0; WALL_T = 2.5
CONVEX_H = 2.0
FRUST_R1 = 7.0; FRUST_R2 = 6.8; FRUST_H = 5.0
M3_D = 3.2

CORNER_CENTERS = [
    ( 190.0,  76.5),
    (-190.0,  76.5),
    ( 190.0, -109.5),
    (-190.0, -109.5),
]

LR = (W - CW) / 2
cut_y_front = D/2 - FRONT_SOLID
cut_y_rear  = -D/2 + REAR_SOLID

base = cq.Workplane("XY").box(W, D, T)

base = (base
    .faces("<Z").workplane()
    .rect(W, D).rect(W - 2*WALL_T, D - 2*WALL_T).extrude(WALL_H))

cut_h = T + 2
cut_w = CW - 2*CS
cut_d = CD - 2*CS
base = (base
    .faces(">Z").workplane()
    .rect(cut_w, CD).cutBlind(-cut_h)
    .faces(">Z").workplane()
    .rect(CW, cut_d).cutBlind(-cut_h))

for cx, cy in CORNER_CENTERS:
    base = (base
        .faces(">Z").workplane()
        .center(cx, cy)
        .rect(CS, CS).extrude(CONVEX_H))

for cx, cy in CORNER_CENTERS:
    cone = (cq.Workplane("XY")
        .workplane(offset=T + CONVEX_H)
        .center(cx, cy)
        .circle(FRUST_R1)
        .workplane(offset=FRUST_H)
        .circle(FRUST_R2)
        .loft())
    base = base.union(cone)
    base = (base
        .faces(">Z").workplane()
        .center(cx, cy)
        .circle(M3_D / 2).cutThruAll())

result = base

cq.exporters.export(result, "/home/mushipan3/esp_projects/ratecaputa/cad/joint_adapter_v3.step")
print("STEP exported: joint_adapter_v3.step")
