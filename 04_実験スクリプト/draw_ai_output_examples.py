"""
AI出力の成功例・失敗例 比較図生成
対象: C4（3相VSIインバータ）Task T1（トポロジ認識）
  成功例: Form-C（構造体JSON）→ TE=1.0
  失敗例: Form-A（アスキーアート）→ TE=0.0（VDC欠落、CR=0.909）
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path

plt.rcParams["font.family"] = ["Hiragino Sans", "AppleGothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

FIGURES_DIR = Path(__file__).parent.parent / "06_図表"

# ─── 色定義 ─────────────────────────────────────────
C_OK     = "#27AE60"   # 正解コンポーネント
C_MISS   = "#E74C3C"   # 欠落コンポーネント
C_NODE   = "#5DADE2"   # 接続ノード
C_BG_OK  = "#F0FFF4"   # 成功側背景
C_BG_NG  = "#FFF5F5"   # 失敗側背景
C_JSON   = "#1A252F"   # JSONテキスト色
C_ASCII  = "#2C3E50"   # ASCIIテキスト色

FORM_A_TEXT = """\
3相VSIインバータのアスキーアート表現:

DC+──┬──────────────────────────────────┐
     │        │            │            │
   [CDC]    [Q1]upper-A [Q3]upper-B  [Q5]upper-C
     │        │            │            │
DC-──┤       PhA          PhB          PhC
     │        │            │            │
     │       [Q2]lower-A [Q4]lower-B [Q6]lower-C
     │        │            │            │
     └─────────────────────────────────┘
              │            │            │
           [Rload_A]   [Rload_B]   [Rload_C]
              │            │            │
           NeutralLoad─────────────────

凡例: VDC=600V DC母線, CDC=1000μF, Q1-Q6:IGBT"""

FORM_C_TEXT = """\
{
  "components": [
    {"id":"VDC","type":"DCVoltageSource",
     "value":600,"unit":"V"},
    {"id":"CDC","type":"Capacitor",
     "value":1000,"unit":"μF"},
    {"id":"Q1","type":"IGBT"},
    {"id":"Q2","type":"IGBT"},
    {"id":"Q3","type":"IGBT"},
    {"id":"Q4","type":"IGBT"},
    {"id":"Q5","type":"IGBT"},
    {"id":"Q6","type":"IGBT"},
    {"id":"Rload_A","type":"Resistor","value":10},
    {"id":"Rload_B","type":"Resistor","value":10},
    {"id":"Rload_C","type":"Resistor","value":10}
  ],
  "connections": [
    {"from":"VDC+","to":"DC+"},
    {"from":"VDC-","to":"DC-"},
    {"from":"DC+","to":"Q1_collector"},
    ...（計22接続）
  ]
}"""


def draw_vsi_graph(ax, missing_vdc=False):
    """C4 3相VSI のトポロジグラフを描画"""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.5)
    ax.set_aspect("equal")
    ax.axis("off")

    def box(x, y, label, color, w=1.3, h=0.6, fontsize=8.5, alpha=1.0,
            linestyle="-", textcolor="white"):
        rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                              boxstyle="round,pad=0.05",
                              fc=color, ec="white" if alpha == 1.0 else color,
                              lw=1.5, linestyle=linestyle, alpha=alpha)
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center",
                fontsize=fontsize, color=textcolor,
                fontweight="bold")

    def node(x, y, label, fontsize=7.5):
        ax.plot(x, y, "o", ms=7, color=C_NODE, zorder=5)
        ax.text(x, y + 0.35, label, ha="center", va="bottom",
                fontsize=fontsize, color="#1A5276")

    def line(x1, y1, x2, y2, color="gray", lw=1.4, ls="-", alpha=0.7):
        ax.plot([x1, x2], [y1, y2], color=color, lw=lw,
                linestyle=ls, alpha=alpha, zorder=1)

    # ─── DCバス ───────────────────────────────────────
    line(1.5, 7.5, 9, 7.5, color="#1A5276", lw=2.5)   # DC+ バス
    line(1.5, 0.8, 9, 0.8, color="#7F8C8D", lw=2.5)   # DC- バス
    ax.text(1.2, 7.5, "DC+", ha="right", va="center",
            fontsize=9, color="#1A5276", fontweight="bold")
    ax.text(1.2, 0.8, "DC−", ha="right", va="center",
            fontsize=9, color="#7F8C8D", fontweight="bold")

    # ─── VDC（電源）───────────────────────────────────
    vdc_color = C_MISS if missing_vdc else C_OK
    vdc_alpha = 1.0
    vdc_ls    = "--" if missing_vdc else "-"
    vdc_tc    = "white" if not missing_vdc else "white"
    box(1.0, 4.15, "VDC\n600V", vdc_color, w=1.1, h=1.0,
        fontsize=8, alpha=vdc_alpha, linestyle=vdc_ls, textcolor=vdc_tc)
    if missing_vdc:
        ax.text(1.0, 4.15, "×", ha="center", va="center",
                fontsize=22, color=C_MISS, alpha=0.35, fontweight="bold")
    # VDC → DC+, DC-
    lc = C_MISS if missing_vdc else "gray"
    line(1.0, 4.65, 1.0, 7.5, color=lc, lw=1.3, ls=vdc_ls)
    line(1.0, 3.65, 1.0, 0.8, color=lc, lw=1.3, ls=vdc_ls)

    # ─── CDC（DCリンクコンデンサ）─────────────────────
    box(2.5, 4.15, "CDC\n1000μF", C_OK, w=1.15, h=1.0, fontsize=8)
    line(2.5, 4.65, 2.5, 7.5)
    line(2.5, 3.65, 2.5, 0.8)

    # ─── 各相（A/B/C）─────────────────────────────────
    phase_x = [4.5, 6.5, 8.5]
    phase_labels = ["A相", "B相", "C相"]
    q_upper = ["Q1", "Q3", "Q5"]
    q_lower = ["Q2", "Q4", "Q6"]
    rload   = ["Rload_A\n10Ω", "Rload_B\n10Ω", "Rload_C\n10Ω"]

    for px, plbl, qu, ql, rl in zip(phase_x, phase_labels, q_upper, q_lower, rload):
        # 上アームIGBT
        box(px, 6.2, qu, C_OK, w=1.15, h=0.7)
        line(px, 7.5, px, 6.55)    # DC+ → 上SW
        line(px, 5.85, px, 4.8)    # 上SW → 中点

        # 中点ノード
        node(px, 4.8, f"Ph{plbl[0]}")

        # 下アームIGBT
        box(px, 3.4, ql, C_OK, w=1.15, h=0.7)
        line(px, 4.45, px, 3.75)   # 中点 → 下SW
        line(px, 3.05, px, 0.8)    # 下SW → DC-

        # 負荷抵抗
        box(px, 1.9, rl, C_OK, w=1.2, h=0.7, fontsize=7.5)
        line(px, 4.8, px, 2.25, color="gray", lw=1.2, ls=":")
        line(px, 1.55, px, 1.1, color="gray", lw=1.2)

    # Neutral Load
    ax.plot([4.5, 8.5], [1.1, 1.1], color="gray", lw=1.2)
    ax.text(6.5, 0.95, "NeutralLoad", ha="center", va="top",
            fontsize=7.5, color="#555")

    # ─── 欠落アノテーション ────────────────────────────
    if missing_vdc:
        ax.annotate("VDC が\n出力に\n欠落！",
                    xy=(1.0, 4.15), xytext=(2.2, 5.8),
                    fontsize=8.5, color=C_MISS, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=C_MISS, lw=1.5),
                    bbox=dict(boxstyle="round,pad=0.3", fc="#FFECEC", ec=C_MISS, lw=1.2))


def make_score_bar(ax, cr, ca, te, title, bg_color):
    """スコアバーを描画"""
    ax.set_facecolor(bg_color)
    ax.axis("off")
    metrics = [("CR", cr, "#5DADE2"), ("CA", ca, "#58D68D"), ("TE", te, "#F0B27A")]
    for i, (name, val, color) in enumerate(metrics):
        x = 0.15 + i * 0.32
        # バー背景
        ax.add_patch(mpatches.Rectangle((x, 0.25), 0.22, 0.5,
                                        fc="#E0E0E0", ec="none"))
        # バー本体
        bar_color = C_OK if val >= 1.0 else (C_MISS if val < 0.95 else "#F39C12")
        ax.add_patch(mpatches.Rectangle((x, 0.25), 0.22 * val, 0.5,
                                        fc=bar_color, ec="none", alpha=0.85))
        ax.text(x + 0.11, 0.5, f"{val:.2f}", ha="center", va="center",
                fontsize=11, fontweight="bold",
                color="white" if val > 0.3 else "#333")
        ax.text(x + 0.11, 0.18, name, ha="center", va="top",
                fontsize=10, color="#333")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    te_label = "完全一致！" if te == 1.0 else "完全不一致"
    te_color = C_OK if te == 1.0 else C_MISS
    ax.text(0.5, 0.88, te_label, ha="center", va="top",
            fontsize=11, fontweight="bold", color=te_color)


def main():
    fig = plt.figure(figsize=(16, 14))
    fig.patch.set_facecolor("#F8F9FA")

    # ─── タイトル ──────────────────────────────────────
    fig.text(0.5, 0.97, "AI出力例：C4（3相VSIインバータ）T1トポロジ認識タスク",
             ha="center", va="top", fontsize=16, fontweight="bold", color="#1A252F")
    fig.text(0.5, 0.945, "モデル: qwen3.5:9b  ／  入力形式の違いが認識精度を決定づける",
             ha="center", va="top", fontsize=12, color="#555")

    # ─── レイアウト定義 ─────────────────────────────────
    # [左列: 成功例]  [右列: 失敗例]
    # 行: ラベル / 入力テキスト / 回路グラフ / スコアバー

    gs = fig.add_gridspec(4, 2,
                          height_ratios=[0.06, 0.28, 0.52, 0.14],
                          hspace=0.04, wspace=0.06,
                          left=0.04, right=0.96,
                          top=0.92, bottom=0.03)

    # ─── 成功/失敗 ラベル行 ─────────────────────────────
    for col, (label, color, form, score) in enumerate([
        ("✓  成功例  Form-C（構造体JSON）", C_OK,   "Form-C入力：明示的コンポーネント配列＋接続配列",   "TE = 1.00"),
        ("✗  失敗例  Form-A（アスキーアート）", C_MISS, "Form-A入力：ASCII文字による回路図表現",          "TE = 0.00"),
    ]):
        ax = fig.add_subplot(gs[0, col])
        ax.set_facecolor(color)
        ax.text(0.5, 0.5, label, ha="center", va="center",
                fontsize=13, fontweight="bold", color="white",
                transform=ax.transAxes)
        ax.axis("off")

    # ─── 入力テキスト行 ─────────────────────────────────
    texts   = [FORM_C_TEXT, FORM_A_TEXT]
    bgs     = [C_BG_OK, C_BG_NG]
    fcolors = [C_JSON, C_ASCII]
    for col, (txt, bg, fc) in enumerate(zip(texts, bgs, fcolors)):
        ax = fig.add_subplot(gs[1, col])
        ax.set_facecolor(bg)
        ax.axis("off")
        # ヘッダ
        headers = ["【入力：構造体JSON（Form-C）】", "【入力：アスキーアート（Form-A）】"]
        ax.text(0.02, 0.96, headers[col], transform=ax.transAxes,
                fontsize=9.5, fontweight="bold", color=fc, va="top")
        ax.text(0.02, 0.86, txt, transform=ax.transAxes,
                fontsize=7.8, color=fc, va="top", fontfamily="monospace",
                linespacing=1.5)
        # 枠
        for spine in ax.spines.values():
            spine.set_edgecolor("#CCCCCC")
            spine.set_linewidth(0.8)

    # ─── 回路グラフ行 ────────────────────────────────────
    for col, missing in enumerate([False, True]):
        ax = fig.add_subplot(gs[2, col])
        bg = C_BG_OK if not missing else C_BG_NG
        ax.set_facecolor(bg)
        headers = ["【AIの出力した回路トポロジ】 — 全11素子・22接続を正確に再現",
                   "【AIの出力した回路トポロジ】 — VDC（電源）が欠落（10/11素子）"]
        hcolor  = C_OK if not missing else C_MISS
        ax.text(0.5, 1.02, headers[col], transform=ax.transAxes,
                ha="center", va="bottom", fontsize=9.5,
                fontweight="bold", color=hcolor)
        draw_vsi_graph(ax, missing_vdc=missing)

    # ─── スコアバー行 ────────────────────────────────────
    score_data = [
        (1.000, 1.000, 1.000, "成功例", C_BG_OK),
        (0.909, 1.000, 0.000, "失敗例", C_BG_NG),
    ]
    for col, (cr, ca, te, title, bg) in enumerate(score_data):
        ax = fig.add_subplot(gs[3, col])
        make_score_bar(ax, cr, ca, te, title, bg)

    # ─── 中央の矢印「→ LLM →」─────────────────────────
    for row_idx, y in [(1, 0.705), (1, 0.705)]:
        pass  # 不要なので省略

    # ─── 凡例 ────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(color=C_OK,   label="正しく認識（正解と一致）"),
        mpatches.Patch(color=C_MISS, label="認識失敗（欠落・誤り）"),
        mpatches.Patch(color=C_NODE, label="接続ノード（DC+/PhA 等）"),
    ]
    fig.legend(handles=legend_items, loc="lower center", ncol=3,
               fontsize=10, framealpha=0.9,
               bbox_to_anchor=(0.5, 0.0))

    out = FIGURES_DIR / "example_success_vs_failure.png"
    plt.savefig(out, bbox_inches="tight", dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"  → {out.name}")


if __name__ == "__main__":
    print("AI出力例 比較図生成...")
    main()
    print("完了")
