import cadquery as cq

# ラテカピュータ 筐体用 ジョイントアダプタ v3

# 基本寸法定義
W_OUTER = 440.0  # 全幅
D_OUTER = 263.0  # 全深
T_THICK = 2.0     # 板厚

# 中央開口寸法
W_OPEN = 416.0
D_OPEN = 216.0

# 台錐寸法
R_CONE = 6.8
H_CONE = 5.0
M3_DIA = 3.2

# コーナー嵩上げ
R_CORNER = 2.0

# 固定ネジ位置（v3変更：重心移動のため前方にずらす）
X_FRONT_CENTER = 193.0
Y_FRONT_CENTER = 76.5
X_REAR_CENTER = -193.0
Y_REAR_CENTER = -109.5

# 壁厚
WALL_THICK = 2.0

# 台錐穴位置（v3：前方にずらす）
X_FRONT_TAP = 190.0
Y_FRONT_TAP = 76.5
X_REAR_TAP = -190.0
Y_REAR_TAP = -109.5

# 台錐穴中心位置（v3：前方にずらす）
X_FRONT_TAP_CENTER = 190.0
Y_FRONT_TAP_CENTER = 76.5
X_REAR_TAP_CENTER = -190.0
Y_REAR_TAP_CENTER = -109.5

# U字パーツとの干渉回避（v3：壁厚増）
WALL_THICK_V3 = 2.5

# 台錐穴位置（v3：前方にずらす）
X_FRONT_TAP = 190.0
Y_FRONT_TAP = 76.5
X_REAR_TAP = -190.0
Y_REAR_TAP = -109.5

# 台錐穴中心位置（v3：前方にずらす）
X_FRONT_TAP_CENTER = 190.0
Y_FRONT_TAP_CENTER = 76.5
X_REAR_TAP_CENTER = -190.0
Y_REAR_TAP_CENTER = -109.5

# U字パーツとの干渉回避（v3：壁厚増）
WALL_THICK_V3 = 2.5

# 台錐穴位置（v3：前方にずらす）
X_FRONT_TAP = 190.0
Y_FRONT_TAP = 76.5
X_REAR_TAP = -190.0
Y_REAR_TAP = -109.5

# 台錐穴中心位置（v3：前方にずらす）
X_FRONT_TAP_CENTER = 190.0
Y_FRONT_TAP_CENTER = 76.5
X_REAR_TAP_CENTER = -190.0
Y_REAR_TAP_CENTER = -109.5

# U字パーツとの干渉回避（v3：壁厚増）
WALL_THICK_V3 = 2.5

# 台錐穴位置（v3：前方にずらす）
X_FRONT_TAP = 190.0
Y_FRONT_TAP = 76.5
X_REAR_TAP = -190.0
Y_REAR_TAP = -109.5

# 台錐穴中心位置（v3：前方にずらす）
X_FRONT_TAP_CENTER = 190.0
Y_FRONT_TAP_CENTER = 76.5
X_REAR_TAP_CENTER = -190.0
Y_REAR_TAP_CENTER = -109.5

# U字パーツとの干渉回避（v3：壁厚増）
WALL_THICK_V3 = 2.5

# 台錐穴位置（v3：前方にずらす）
X_FRONT_TAP = 190.0
Y_FRONT_TAP = 76.5
X_REAR_TAP = -190.0
Y_REAR_TAP = -109.5

# 台錐穴中心位置（v3：前方にずらす）
X_FRONT_TAP_CENTER = 190.0
Y_FRONT_TAP_CENTER = 76.5
X_REAR_TAP_CENTER = -190.0
Y_REAR_TAP_CENTER = -109.5

# U字パーツとの干渉回避（v3：壁厚増）
WALL_THICK_V3 = 2.5

# 台錐穴位置（v3：前方にずらす）
X_FRONT_TAP = 190.0
Y_FRONT_TAP = 76.5
X_REAR_TAP = -190.0
Y_REAR_TAP = -109.5

# 台錐穴中心位置（v3：前方にずらす）
X_FRONT_TAP_CENTER = 190.0
Y_FRONT_TAP_CENTER = 76.5
X_REAR_TAP_CENTER = -190.0
Y_REAR_TAP_CENTER = -109.5

# U字パーツとの干渉回避（v3：壁厚増）
WALL_THICK_V3 = 2.5

# 台錐穴位置（v3：前方にずらす）
X_FRONT_TAP = 190.0
Y_FRONT_TAP = 76.5
X_REAR_TAP = -190.0
Y_REAR_TAP = -109.5

# 台錐穴中心位置（v3：前方にずらす）
X_FRONT_TAP_CENTER = 190.0
Y_FRONT_TAP_CENTER = 76.5
X_REAR_TAP_CENTER = -190.0
Y_REAR_TAP_CENTER = -109.5

# U字パーツとの干渉回避（v3：壁厚増）
WALL_THICK_V3 = 2.5

# 台錐穴位置（v3：前方にずらす）
X_FRONT_TAP = 190.0
Y_FRONT_TAP = 76.5
X_REAR_TAP = -190.0
Y_REAR_TAP = -109.5

# 台錐穴中心位置（v3：前方にずらす）
X_FRONT_TAP_CENTER = 190.0
Y_FRONT_TAP_CENTER = 76.5
X_REAR_TAP_CENTER = -190.0
Y_REAR_TAP_CENTER = -109.5

# U字パーツとの干渉回避（v3：壁厚増）
WALL_THICK_V3 = 2.5

# 台錐穴位置（v3：前方にずらす）
X_FRONT_TAP = 190.0
Y_FRONT_TAP = 76.5
X_REAR_TAP = -190.0
Y_REAR_TAP = -109.5

# 台錐穴中心位置（v3：前方にずらす）
X_FRONT_TAP_CENTER = 190.0
Y_FRONT_TAP_CENTER = 76.5
X_REAR_TAP_CENTER = -190.0
Y_REAR_TAP_CENTER = -109.5

# U字パーツとの干渉回避（v3：壁厚増）
WALL_THICK_V3 = 2.5

# 台錐穴位置（v3：前方にずらす）
X_FRONT_TAP = 190.0
Y_FRONT_TAP = 76.5
X_REAR_TAP = -190.0
Y_REAR_TAP = -109.5

# 台錐穴中心位置（v3：前方にずらす）
X_FRONT_TAP_CENTER = 190.0
Y_FRONT_TAP_CENTER = 76.5
X_REAR_TAP_CENTER = -190.0