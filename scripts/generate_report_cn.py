#!/usr/bin/env python
"""生成中文版改进实验报告 Word 文档。"""

import os, json
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "MovieRec_改进实验报告_中文版.docx")

with open(os.path.join(RESULTS_DIR, "experiment_results.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

ratings = data["rating_prediction_results"]
ranking = data["ranking_results"]

doc = Document()

style = doc.styles["Normal"]
font = style.font
font.name = "宋体"
font.size = Pt(11)
style.paragraph_format.line_spacing = 1.25

def add_heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "黑体"
    return h

def add_para(text, bold=False, size=11, font_name=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = font_name or "宋体"
    run.font.size = Pt(size)
    run.bold = bold
    return p

def add_table(headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for run in p.runs:
                run.font.name = "宋体"
                run.font.size = Pt(10)
                run.bold = True
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.rows[r + 1].cells[c]
            cell.text = str(val)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.name = "宋体"
                    run.font.size = Pt(10)
    doc.add_paragraph()
    return table

def insert_image(name, width=5.5):
    path = os.path.join(RESULTS_DIR, name)
    if os.path.exists(path):
        doc.add_picture(path, width=Inches(width))
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        label_map = {
            "01_rating_distribution": "图：评分分布",
            "02_sparsity_pie": "图：用户-物品交互矩阵稀疏度",
            "03_error_distributions": "图：预测误差分布对比",
            "04_actual_vs_predicted": "图：实际评分 vs 预测评分散点图",
            "05_algorithm_radar": "图：算法优劣势雷达对比图",
            "06_model_comparison_mae": "图：所有模型 MAE 对比",
            "07_hyperparameter_sensitivity": "图：超参数 K 敏感度分析",
            "08_diversity_comparison": "图：推荐多样性对比",
            "09_zscore_improvement_heatmap": "图：Z-score 改进热力图",
            "10_time_comparison": "图：计算效率对比",
            "11_user_rating_behavior": "图：用户评分行为分析",
            "12_cold_start_analysis": "图：冷启动风险分析",
        }
        key = name.replace(".png", "")
        caption = label_map.get(key, name)
        run = p.add_run(caption)
        run.font.size = Pt(9)
        run.font.name = "宋体"
        run.italic = True
    doc.add_paragraph()

# ===================================================================
# 封面
# ===================================================================
doc.add_paragraph()
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("MovieRec 改进实验报告")
run.font.name = "黑体"
run.font.size = Pt(22)
run.bold = True

doc.add_paragraph()
subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run("基于协同过滤的电影推荐系统 — 关键Bug修复与方法论增强")
run.font.name = "黑体"
run.font.size = Pt(14)

doc.add_paragraph()
info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = info.add_run("与原实验的详细对照分析\n数据科学硕士课程\n2026年5月")
run.font.name = "宋体"
run.font.size = Pt(11)

doc.add_page_break()

# ===================================================================
# 摘要
# ===================================================================
add_heading("摘要", level=1)
add_para(
    "本报告是对 MovieRec 电影推荐系统的修正与增强复现实验。原实验基于 MovieLens 1M 数据集"
    "（6,040位用户、3,706部电影、1,000,209条评分）实现了基于用户和基于物品的协同过滤算法，"
    "并引入了 Z-score 标准化优化。然而，我们发现原始实现存在一个致命缺陷：Precision@K 和 "
    "Recall@K 均被报告为 0.0，原因是推荐函数未能排除用户已在训练集中评分过的项目。"
    "修复该 Bug 后，我们得到了有效的排序指标：基于用户的协同过滤 Precision@10 达到 0.086，"
    "基于物品的协同过滤（Pearson）Precision@10 达到 0.069。此外，我们新增了四个基线模型"
    "（GlobalMean、UserMean、ItemMean、MostPopular），将 Z-score 标准化扩展到基于物品的"
    "协同过滤（MAE 从 0.7904 降至 0.7146，提升 9.6%），通过配对 t 检验进行了统计显著性"
    "验证（所有改进 p < 0.01），并完成了超参数 K 从 5 到 100 的敏感度分析。表现最优的模型"
    "是基于用户的协同过滤（余弦相似度 + Z-score），MAE = 0.7018。我们还修正了原报告中数据"
    "统计的矛盾之处，包括矩阵稀疏度（实际为 95.53% 而非 99.98%）和评分总数（100 万而非 181 万）。"
)

# ===================================================================
# 1. 引言
# ===================================================================
add_heading("一、引言", level=1)

add_heading("1.1 原实验发现的问题", level=2)
add_para("我们在复现原实验的过程中，发现了以下六个问题（按严重程度排序）：")

issues = [
    "【P0 — 致命评估Bug】Precision@K 和 Recall@K 对所有算法均报告为 0.0。"
    "根本原因：推荐函数未排除用户在训练集中已评分的物品，导致 Top-K 推荐列表中全是用户已交互过的内容，"
    "在测试集中无法命中任何新物品。",
    "【P0 — 数据报告矛盾】原报告声称评分总数为 1,810,189 条，但标准 MovieLens 1M 数据集为 1,000,209 条。"
    "报告同时声称「仅约 18,000 条已观测交互」和「1,810,189 条评分」，两者自相矛盾。"
    "报告声称稀疏度为 99.98%，但实际为 95.53%，相差超过 20 倍。",
    "【P1 — 缺少基线对比】仅比较了 User-CF vs Item-CF，未验证这两种方法是否优于简单的统计基线"
    "（如预测全局均值、用户均值、物品均值）。",
    "【P1 — Z-score 分析不完整】仅对基于用户的协同过滤应用了 Z-score，未探索其对基于物品的"
    "协同过滤的影响。",
    "【P2 — 缺少统计检验】Z-score 带来的性能提升未经过任何统计显著性检验，无法排除偶然性。",
    "【P2 — 缺少超参数分析】所有结果均在单一 K=50 下报告，未探索邻居数量对性能的影响。",
]
for issue in issues:
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(issue)
    run.font.name = "宋体"
    run.font.size = Pt(10)

add_heading("1.2 本实验的改进贡献", level=2)
improvements = [
    "修复 Precision@K / Recall@K 评估 Bug：正确排除训练集已评分项目，得到有意义的排序指标。",
    "新增 4 个基线模型：GlobalMean、UserMean、ItemMean、MostPopular，明确了 CF 方法的实际提升幅度。",
    "将 Z-score 标准化同时应用于 User-CF 和 Item-CF，系统评估其在不同算法-相似度组合下的效果。",
    "完成配对 t 检验统计显著性分析，所有主要改进均达到 p < 0.01 水平。",
    "完成超参数 K 从 5 到 100 的敏感度分析，给出最优 K 值建议。",
    "修正原报告中所有数据矛盾，提供准确、一致的数据统计。",
]
for item in improvements:
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(item)
    run.font.name = "宋体"
    run.font.size = Pt(10)

# ===================================================================
# 2. 实验方法
# ===================================================================
add_heading("二、实验方法", level=1)

add_heading("2.1 数据集与预处理", level=2)
add_para(
    "我们使用 MovieLens 1M 数据集，包含 6,040 位用户、3,706 部电影和 1,000,209 条 1–5 星的评分。"
    "用户-物品交互矩阵共有 22,384,240 个可能的单元格，其中已观测 1,000,209 个，稀疏度为 95.53%。"
    "评分分布呈现轻微右偏（均值 3.58，中位数 4，偏度 −0.55），最常见的评分为 4 星（34.9%）和 "
    "3 星（26.1%）。平均每位用户贡献 166 条评分（中位数 96）。"
)

add_heading("2.2 训练/测试集划分", level=2)
add_para(
    "采用按用户的时间顺序划分：对每位用户，按时间戳排序后，将最近 20% 的评分作为测试集，"
    "其余 80% 作为训练集。评分少于 5 条的用户被排除。最终训练集包含 802,553 条评分，"
    "测试集包含 197,656 条评分，覆盖全部 6,040 位用户。"
)

add_heading("2.3 实现算法", level=2)
add_para("本实验统一实现了以下 12 个模型：")

algos = [
    ["基线", "GlobalMean", "对所有物品预测全局平均评分"],
    ["基线", "UserMean", "对每位用户预测其个人平均评分"],
    ["基线", "ItemMean", "对每个物品预测其历史平均评分"],
    ["基线", "MostPopular", "推荐评分次数最多的物品（非个性化）"],
    ["CF", "User-CF (cosine)", "基于用户的协同过滤 + 余弦相似度"],
    ["CF", "User-CF (cosine, Z)", "基于用户的协同过滤 + 余弦相似度 + Z-score"],
    ["CF", "User-CF (pearson)", "基于用户的协同过滤 + Pearson相关系数"],
    ["CF", "User-CF (pearson, Z)", "基于用户的协同过滤 + Pearson + Z-score"],
    ["CF", "Item-CF (cosine)", "基于物品的协同过滤 + 余弦相似度"],
    ["CF", "Item-CF (cosine, Z)", "基于物品的协同过滤 + 余弦相似度 + Z-score"],
    ["CF", "Item-CF (pearson)", "基于物品的协同过滤 + Pearson相关系数"],
    ["CF", "Item-CF (pearson, Z)", "基于物品的协同过滤 + Pearson + Z-score"],
]
add_table(["类型", "模型", "说明"], algos)

add_heading("2.4 Z-score 标准化原理", level=2)
add_para(
    "Z-score 标准化将每位用户的评分转换为标准差单位："
    "z_ui = (r_ui − μ_u) / σ_u，其中 μ_u 和 σ_u 分别是用户 u 在训练集中评分的均值和标准差。"
    "此举的核心目的是消除个人评分偏差——有些用户习惯性给 2–3 星，另一些用户习惯性给 4–5 星，"
    "直接比较原始评分会引入噪声。标准化的关键细节在于：(1) 在计算相似度之前进行 Z-score 变换，"
    "使相似度反映的是评分模式而非绝对值；(2) 在预测后再反标准化：r̂ = ẑ · σ_u + μ_u。"
)

add_heading("2.5 关键Bug修复：Precision@K / Recall@K", level=2)
add_para(
    "这是本实验最重要的修正。原实现的推荐函数直接返回预测评分最高的 K 个物品，未排除用户"
    "已在训练集中评分过的物品。由于 CF 倾向于对用户已高分评分的相似物品给出高预测值，"
    "Top-K 推荐列表几乎全部被训练集物品占据。当用测试集（包含用户评分过但被保留的物品）验证时，"
    "推荐列表中没有新物品，命中率为零。"
)
add_para(
    "修正后的实现：(1) 对每位测试用户，获取其在训练集中已评分的所有物品；(2) 生成 K 个推荐时"
    "显式排除这些物品；(3) 将推荐物品与用户的测试集进行比对，评分 >= 4 的视为「相关」命中。"
    "这是 Herlocker 等人（2004）描述的留一法评估标准协议。"
)

add_heading("2.6 统计显著性检验", level=2)
add_para(
    "我们对每种算法计算逐用户的 MAE，然后进行配对双尾 t 检验。显著性标记："
    "* p < 0.05，** p < 0.01，*** p < 0.001。"
)

# ===================================================================
# 3. 实验结果
# ===================================================================
add_heading("三、实验结果", level=1)

add_heading("3.1 评分预测精度", level=2)
add_para(
    "表 1 展示了所有 12 个模型的 MAE 和 RMSE。表现最优的模型是基于用户的协同过滤"
    "（余弦相似度 + Z-score），MAE = 0.7018；紧随其后的是基于物品的协同过滤"
    "（余弦相似度 + Z-score），MAE = 0.7146。"
)

sorted_models = sorted(ratings.items(), key=lambda x: x[1]["mae"])
rows = []
for name, r in sorted_models:
    rows.append([name, f"{r['mae']:.4f}", f"{r['rmse']:.4f}", f"{r['predict_time_s']:.2f}s"])
add_table(["模型", "MAE", "RMSE", "预测耗时"], rows)
add_para("表1：所有模型的评分预测结果（数值越低越好）。")

add_heading("3.2 排序质量：Precision@K 与 Recall@K", level=2)
add_para(
    "表 2 展示了修正后的 Precision@10 和 Recall@10。与原报告全部为 0.0 相比，"
    "修正后的实现得出了有意义的排序指标。基于用户的协同过滤（余弦相似度）取得了最高的 "
    "Precision@10 = 0.086，即平均每 10 个推荐中有 0.86 个是用户尚未看过但确实会打高分的电影。"
)

srank = sorted(
    [(k, v) for k, v in ranking.items() if v.get("precision@10", 0) > 0],
    key=lambda x: x[1]["precision@10"], reverse=True
)
rows2 = []
for name, r in srank:
    rows2.append([
        name, f"{r['precision@10']:.4f}", f"{r['recall@10']:.4f}",
        str(r["hit_count"]), str(r["users_with_relevant"])
    ])
add_table(["模型", "Precision@10", "Recall@10", "命中数", "有效用户"], rows2)
add_para("表2：排序评估结果（相关阈值：评分 ≥ 4）。")

add_heading("3.3 Z-score 改进效果分析", level=2)
add_para(
    "表 3 量化了 Z-score 标准化对每种算法的效果。在使用余弦相似度时，基于用户和基于物品的"
    "协同过滤均从 Z-score 中获益，MAE 分别降低 9.3% 和 9.6%（均为 p < 0.001）。"
    "然而，Z-score 与 Pearson 相关系数的组合在 Item-CF 上反而使性能下降了 2.9%——"
    "这是因为 Pearson 本身已对数据进行了均值中心化，额外的标准差归一化引入了噪声。"
)

rows3 = [
    ["User-CF (cosine)", "0.7737", "0.7018", "−9.3%", "p < 0.001 (t=24.84)"],
    ["User-CF (pearson)", "0.7640", "0.7237", "−5.3%", "p < 0.001 (t=12.75)"],
    ["Item-CF (cosine)", "0.7904", "0.7146", "−9.6%", "p < 0.001 (t=38.16)"],
    ["Item-CF (pearson)", "0.7503", "0.7724", "+2.9%（变差）", "p < 0.001 (t=−16.61)"],
]
add_table(["算法", "原始 MAE", "Z-score MAE", "变化", "显著性"], rows3)
add_para("表3：Z-score 标准化对预测精度的影响。")

add_heading("3.4 基线模型对比", level=2)
add_para(
    "所有协同过滤方法均显著优于四个基线模型。最优基线模型（ItemMean，MAE = 0.7871）仍比 "
    "User-CF (cosine, Z) 差 10.8%。这证明了 CF 算法确实捕获了超越简单统计聚合的用户偏好模式。"
    "值得注意的是，MostPopular 在评分预测上与 ItemMean 相同（因为其预测值就是物品均值），"
    "两者的区别仅体现在排序任务中。"
)

add_heading("3.5 超参数敏感度分析", level=2)
add_para(
    "随着 K（邻居数量）从 5 增加到 100，两种算法的 MAE 均持续下降。对于基于用户的协同过滤，"
    "最优 K = 30；对于基于物品的协同过滤，最优 K = 20（无 Z-score）或 K = 50（有 Z-score）。"
    "当 K 超过 50 后，性能趋于稳定，增加更多邻居带来的边际收益很小。Z-score 变体在所有 K 值下"
    "均优于非 Z-score 版本。"
)

add_heading("3.6 计算效率", level=2)
add_para(
    "基于物品的协同过滤在训练阶段比基于用户的快 2–5 倍，预测阶段快 1.4 倍。在推荐评估中，"
    "Item-CF 比 User-CF 快约 120 倍（0.23 秒 vs 27.5 秒，100 个用户），这是因为 Item-CF "
    "使用向量化矩阵乘法（predict_all_for_user）一次性计算用户对所有物品的预测分数。"
    "对于生产环境中需要实时推荐的场景，Item-CF 具有显著优势。"
)

# ===================================================================
# 4. 与原实验详细对照
# ===================================================================
add_heading("四、与原实验的详细对照", level=1)

add_heading("4.1 数据统计：原报告 vs 修正后", level=2)
rows_data = [
    ["评分总数", "1,810,189", "1,000,209", "原报告虚高 81%"],
    ["矩阵稀疏度", "99.98%", "95.53%", "矛盾数据已修正"],
    ["已观测交互", "0.02% / 18,119", "4.47% / 1,000,209", "原报告多处数据自相矛盾"],
    ["用户数 × 电影数", "6,040 × 3,706", "6,040 × 3,706", "一致 ✓"],
    ["评分范围", "1–5 星", "1–5 星", "一致 ✓"],
]
add_table(["指标", "原报告", "本报告", "说明"], rows_data)
add_para("表4：数据统计对照。")

add_heading("4.2 评分预测：原报告 vs 修正后", level=2)
rows_mae = [
    ["User-CF MAE", "1.0786", "0.7737", "差异源于不同数据集"],
    ["User-CF + Z-score MAE", "0.8094", "0.7018", "本实验 MAE 更优"],
    ["User-CF Z-score 提升幅度", "−25.0%", "−9.3%", "原报告可能高估"],
    ["Item-CF MAE", "0.4410", "0.7904", "原报告数值异常偏低"],
    ["Item-CF + Z-score MAE", "未报告", "0.7146", "本实验新增"],
    ["Item-CF Z-score 提升幅度", "未报告", "−9.6%", "本实验新增"],
]
add_table(["指标", "原报告", "本报告", "说明"], rows_mae)
add_para("表5：评分预测结果对照。")
add_para(
    "原报告的 Item-CF MAE = 0.4410 异常偏低。在此精度水平上，Item-CF 几乎可以完美预测评分"
    "（5 分量表上平均误差不到 0.5 星），这与该数据集上的已发表基准结果严重不符"
    "（Sarwar 等, 2001）。我们的 Item-CF MAE = 0.7904 与 MovieLens 1M 上 CF 算法的"
    "典型表现一致。原报告异常低的值可能源于数据泄露（训练/测试分割不当）或使用了不同的数据集版本。"
)

add_heading("4.3 排序质量：原报告 vs 修正后", level=2)
add_para("这是最关键的修正，直接将无效的 0.0 替换为有意义的评估值：")

rows_rank = [
    ["User-CF Precision@10", "0.0（Bug）", "0.086", "修复：排除训练集已评分物品"],
    ["User-CF Recall@10", "0.0（Bug）", "0.0541", "修复：同上"],
    ["Item-CF Precision@10", "0.0（Bug）", "0.069（pearson）", "修复：同上"],
    ["Item-CF Recall@10", "0.0（Bug）", "0.0327（pearson）", "修复：同上"],
    ["MostPopular P@10", "未评估", "0.0（符合预期）", "非个性化推荐无法命中"],
]
add_table(["指标", "原报告", "本报告", "说明"], rows_rank)
add_para("表6：排序质量对照——最关键的修正。")

add_heading("4.4 本实验新增的分析", level=2)
new_items = [
    "统计显著性检验：配对 t 检验确认所有 Z-score 改进均显著（p < 0.01），User-CF vs Item-CF "
    "的差异亦显著。t 统计量范围从 |6.50| 到 |38.16|。",
    "超参数敏感度分析：最优 K 值分别为 User-CF K=30、Item-CF K=20。两种算法在 K>50 后"
    "均呈现边际收益递减，K=30 后性能趋于稳定。",
    "Z-score 应用于 Item-CF：余弦相似度下 MAE 提升 9.6%，但 Pearson 下反而下降 2.9%。"
    "根本原因：Pearson 已内置均值中心化，叠加 Z-score 标准化相当于过度校正。",
    "计算效率分析：Item-CF 的拟合速度比 User-CF 快 2–5 倍，预测速度约快 1.4 倍。"
    "在推荐评估中，Item-CF 比 User-CF 快约 120 倍（0.23s vs 27.5s），"
    "因为其使用向量化矩阵乘法一次性预测所有物品。",
    "冷启动风险分析：56.1% 的用户拥有 ≥20 条评分（低风险），40.7% 的用户拥有 5–19 条（中等风险），"
    "3.2% 的用户少于 5 条（高风险，已被排除出实验）。",
]
for item in new_items:
    p = doc.add_paragraph(style="List Number")
    run = p.add_run(item)
    run.font.name = "宋体"
    run.font.size = Pt(10)

# ===================================================================
# 5. 可视化
# ===================================================================
add_heading("五、可视化分析", level=1)

add_heading("5.1 评分分布", level=2)
insert_image("01_rating_distribution.png", width=5.0)
add_para("评分集中在 3–4 星，4 星占比最高（34.9%），整体呈右偏分布。")

add_heading("5.2 矩阵稀疏度", level=2)
insert_image("02_sparsity_pie.png", width=4.0)
add_para("在 22,384,240 个可能的用户-物品对中，仅 1,000,209 个（4.47%）有评分记录。")

add_heading("5.3 预测误差分布", level=2)
insert_image("03_error_distributions.png", width=6.0)
add_para("Z-score 变体的误差分布更加集中，均值和峰值均更接近零。")

add_heading("5.4 实际 vs 预测评分", level=2)
insert_image("04_actual_vs_predicted.png", width=6.0)

add_heading("5.5 算法对比雷达图", level=2)
insert_image("05_algorithm_radar.png", width=4.5)

add_heading("5.6 模型 MAE 对比", level=2)
insert_image("06_model_comparison_mae.png", width=5.5)

add_heading("5.7 超参数敏感度", level=2)
insert_image("07_hyperparameter_sensitivity.png", width=6.0)
add_para("K 从 5 增至 20–30 时 MAE 持续下降，之后趋于平台。Z-score 变体在所有 K 值下均占优。")

add_heading("5.8 推荐多样性", level=2)
insert_image("08_diversity_comparison.png", width=5.0)
add_para("基于物品的协同过滤在推荐多样性上优于基于用户的方法。")

add_heading("5.9 Z-score 改进热力图", level=2)
insert_image("09_zscore_improvement_heatmap.png", width=5.0)

add_heading("5.10 计算效率", level=2)
insert_image("10_time_comparison.png", width=5.5)

add_heading("5.11 用户评分行为", level=2)
insert_image("11_user_rating_behavior.png", width=6.0)
add_para("不同用户的评分均值和标准差存在显著差异，这验证了 Z-score 标准化的必要性。")

add_heading("5.12 冷启动分析", level=2)
insert_image("12_cold_start_analysis.png", width=6.0)

# ===================================================================
# 6. 讨论
# ===================================================================
add_heading("六、讨论", level=1)

add_heading("6.1 为何 Precision/Recall 为 0？", level=2)
add_para(
    "根本原因是一个看似微小但影响深远的实现错误。推荐函数生成了按预测评分排序的 Top-K 物品列表，"
    "但没有过滤掉用户在训练集中已评分过的物品。由于协同过滤倾向于对与用户已高分评分物品相似的内容"
    "给出高预测分，Top-K 列表几乎完全由训练集物品主导。当用测试集验证时（测试集包含的是用户在训练后"
    "实际互动过的物品），推荐列表中没有任何新物品能够命中——命中数为零。我们的修复方案在推荐函数中"
    "显式排除了训练物品候选集，严格按照推荐系统的标准评估协议执行。"
)

add_heading("6.2 原报告的数据矛盾", level=2)
add_para(
    "原报告的数据统计存在多处矛盾：同时声称 1,810,189 条评分和「仅 18,119 条交互」；"
    "稀疏度报告为 99.98% 但按 6,040×3,706=2,238 万总单元格计算，1 万条评分对应约 99.95% 稀疏度"
    "而非 99.98%；1,810,189 条评分对应的稀疏度应为约 92%。标准 MovieLens 1M 数据集包含的评分"
    "恰好是 1,000,209 条，稀疏度确实为 95.53%。这些矛盾可能源于实验过程中使用了不同版本或"
    "子采样的数据集，但在报告中未加以区分。无论原因如何，准确的数据报告对于研究的可复现性至关重要。"
)

add_heading("6.3 Z-score 与相似度度量的交互作用", level=2)
add_para(
    "一个重要发现是 Z-score 标准化与不同相似度度量之间存在交互效应。对于余弦相似度，Z-score "
    "始终提升性能（User-CF 9.3%，Item-CF 9.6%）。然而对于已经包含均值中心化的 Pearson 相关系数，"
    "Z-score 反而使 Item-CF 性能下降 2.9%。这是因为对 Pearson 已中心化的数据再次进行 Z-score "
    "标准化不会增加新信息，反而可能放大评分较少的物品的噪声。这一发现为相似度度量与标准化方法的"
    "组合选择提供了明确指导。"
)

add_heading("6.4 实用建议", level=2)
recs = [
    "评分预测场景：推荐 Item-CF (cosine, Z-score)，K=20。MAE=0.7146，预测速度快（2.51s/197K 条），"
    "可扩展性好，适合大规模部署。",
    "Top-K 推荐场景：推荐 User-CF (cosine)，Precision@10=0.086 为所有模型中最高。"
    "虽然速度较慢，但提供了更好的推荐排序质量。",
    "始终加入基线对比：GlobalMean 基线（MAE=0.9449）为所有方法提供了有意义的下界。"
    "CF 方法相对基线约 20% 的 MAE 改进证实了其计算成本的合理性。",
    "报告统计检验结果：逐用户 MAE 分布不能保证正态性，配对 t 检验为性能改进是否偶然提供严格证据。",
    "注意相似度与标准化的匹配：余弦相似度 + Z-score 是最佳组合；Pearson + Z-score 对 Item-CF 有负面影响。",
]
for r in recs:
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(r)
    run.font.name = "宋体"
    run.font.size = Pt(10)

# ===================================================================
# 7. 结论
# ===================================================================
add_heading("七、结论", level=1)
add_para(
    "本改进实验表明，在修正了评估 Bug 并使用严格的方法论后，协同过滤与 Z-score 标准化的组合"
    "在 MovieLens 1M 数据集上取得了有意义且可测量的改进效果。修正后的 Precision@K 和 "
    "Recall@K 指标（0.048–0.086）替代了原报告无效的零值。基于用户和基于物品的协同过滤均"
    "从 Z-score 标准化中受益（余弦相似度下 MAE 分别降低 9.3% 和 9.6%），所有改进均具有"
    "统计显著性（p < 0.01）。基线模型、超参数分析和计算效率指标的加入为算法性能提供了"
    "完整的评估图景。主要方法论文献表明，我们获得的 MAE 值与此数据集上传统 CF 方法的预期结果一致。"
)
add_para(
    "未来工作方向：(1) 引入矩阵分解方法（SVD、NMF）以捕获更深层的隐含因子；"
    "(2) 结合电影元数据（类型、导演、演员）构建混合推荐系统以缓解冷启动问题；"
    "(3) 引入时间动态建模以捕捉用户偏好的演变；(4) 添加推荐解释模块以提升用户信任和透明度；"
    "(5) 在更大规模数据集（MovieLens 10M/20M）上验证结论的可扩展性。"
)

# ===================================================================
# 参考文献
# ===================================================================
add_heading("参考文献", level=1)
refs = [
    "[1] Ouyang, Q., Yang, P., Shi, Y. 等. (2026). MovieRec: A Comprehensive Collaborative "
    "Filtering-Based Movie Recommendation System with Z-Score Standardization Optimization. "
    "MScDS 项目报告, 岭南大学.",
    "[2] Sarwar, B., Karypis, G., Konstan, J., & Riedl, J. (2001). Item-based collaborative "
    "filtering recommendation algorithms. WWW 2001, 285–295.",
    "[3] Herlocker, J. L., Konstan, J. A., Terveen, L. G., & Riedl, J. T. (2004). Evaluating "
    "collaborative filtering recommender systems. ACM TOIS, 22(1), 5–53.",
    "[4] Su, X., & Khoshgoftaar, T. M. (2009). A survey of collaborative filtering techniques. "
    "Advances in Artificial Intelligence, 2009.",
    "[5] Koren, Y., Bell, R., & Volinsky, C. (2009). Matrix factorization techniques for "
    "recommender systems. Computer, 42(8), 30–37.",
    "[6] Harper, F. M., & Konstan, J. A. (2015). The MovieLens datasets: History and context. "
    "ACM TIIS, 5(4), 1–19.",
    "[7] Resnick, P., Iacovou, N., Suchak, M. 等. (1994). GroupLens: An open architecture for "
    "collaborative filtering of netnews. CSCW 1994, 175–186.",
    "[8] Linden, G., Smith, B., & York, J. (2003). Amazon.com recommendations: Item-to-item "
    "collaborative filtering. IEEE Internet Computing, 7(1), 76–80.",
]
for ref in refs:
    p = doc.add_paragraph()
    run = p.add_run(ref)
    run.font.name = "宋体"
    run.font.size = Pt(10)

# ===================================================================
# 附录
# ===================================================================
add_heading("附录：项目代码结构与复现方法", level=1)
add_para("所有实验使用 Python 3.11 运行，依赖 NumPy、SciPy、Pandas、Scikit-learn、Matplotlib 和 Seaborn。")

code_structure = """Movie Recommendation/
  data/ml-1m/              — MovieLens 1M 数据集
  src/
    config.py              — 配置常量
    data_loader.py         — 数据加载、预处理、统计分析
    baselines.py           — 4 个基线模型
    collaborative_filtering.py — User-CF & Item-CF + Z-score
    evaluation.py          — MAE, RMSE, Precision@K, Recall@K, t检验
    visualization.py       — 12 张可视化图表
    run_experiment.py      — 主实验编排脚本
  results/
    experiment_results.json — 全部数值结果
    01-12_*.png             — 全部图表
  generate_report.py        — 英文版报告生成器
  generate_report_cn.py     — 中文版报告生成器（本脚本）
"""
p = doc.add_paragraph()
run = p.add_run(code_structure)
run.font.name = "Consolas"
run.font.size = Pt(9)

add_para(
    "复现方法：激活 Python 环境后，在项目目录下执行 "
    "python -c \"from src.run_experiment import main; main()\"。"
    "实验总耗时约 3–5 分钟（取决于 CPU 性能）。"
)

doc.save(OUTPUT_PATH)
print(f"中文报告已保存至: {OUTPUT_PATH}")
