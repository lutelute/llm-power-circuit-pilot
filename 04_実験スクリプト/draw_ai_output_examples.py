"""
AI出力の成功例・失敗例 比較図（完全版）
対象: C4（3相VSIインバータ）Task T1（トポロジ認識）
  成功例: Form-C（構造体JSON）→ TE=1.0 → 正しい回路 → 正しい波形
  失敗例: Form-A（アスキーアート）→ TE=0.0（VDC欠落）→ 波形 = 0V
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.gridspec as gridspec
import numpy as np
from pathlib import Path

# 日本語フォント
plt.rcParams["font.family"] = ["Hiragino Sans", "AppleGothic",
                                "Apple SD Gothic Neo", "Arial Unicode MS",
                                "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

FIGURES_DIR = Path(__file__).parent.parent / "06_図表"

# ── 色定義 ────────────────────────────────────────────
COK   = "#1E8449"   # 正解
CMISS = "#C0392B"   # 欠落
CNODE = "#2471A3"   # ノード
CBG_S = "#F0FFF4"   # 成功側BG
CBG_F = "#FEF9F9"   # 失敗側BG
CHDR_S = "#1E8449"  # 成功ヘッダ
CHDR_F = "#C0392B"  # 失敗ヘッダ

FORM_A_TEXT = (
    "3相VSI アスキーアート（Form-A）\n\n"
    "DC+──┬──────────────────────┐\n"
    "     │   [Q1]A [Q3]B [Q5]C │\n"
    "   [CDC]    │     │     │   │\n"
    "DC-──┤   PhA  PhB  PhC   │\n"
    "     │   [Q2]A [Q4]B [Q6]C │\n"
    "     └────────────────────┘\n"
    "      [RA]  [RB]  [RC]\n"
    "凡例: VDC=600V, CDC=1000μF,\n"
    "      Q1-Q6:IGBT, Rload:10Ω"
)

FORM_C_TEXT = (
    '{\n'
    '  "components": [\n'
    '    {"id":"VDC","type":"DCVoltageSource",\n'
    '                "value":600,"unit":"V"},\n'
    '    {"id":"CDC","type":"Capacitor",\n'
    '                "value":1000,"unit":"μF"},\n'
    '    {"id":"Q1",...},{"id":"Q2",...},\n'
    '    {"id":"Q3",...},{"id":"Q4",...},\n'
    '    {"id":"Q5",...},{"id":"Q6",...},\n'
    '    {"id":"Rload_A","value":10},\n'
    '    {"id":"Rload_B","value":10},\n'
    '    {"id":"Rload_C","value":10}\n'
    '  ],\n'
    '  "connections": [\n'
    '    {"from":"VDC+","to":"DC+"},\n'
    '    {"from":"VDC-","to":"DC-"},\n'
    '    ... （計22接続）\n'
    '  ]\n'
    '}'
)


# ════════════════════════════════════════════════════
# (1) 回路トポロジグラフ
# ════════════════════════════════════════════════════
def draw_topology(ax, missing_vdc=False):
    bg = CBG_S if not missing_vdc else CBG_F
    ax.set_facecolor(bg)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")

    def box(x, y, lbl, color, w=1.3, h=0.65, fs=8.5, ls="-", alpha=1.0):
        r = FancyBboxPatch((x-w/2, y-h/2), w, h,
                           boxstyle="round,pad=0.06",
                           fc=color, ec="white", lw=1.4,
                           linestyle=ls, alpha=alpha)
        ax.add_patch(r)
        ax.text(x, y, lbl, ha="center", va="center",
                fontsize=fs, color="white", fontweight="bold")

    def nd(x, y, lbl):
        ax.plot(x, y, "o", ms=6, color=CNODE, zorder=5)
        ax.text(x, y+0.32, lbl, ha="center", va="bottom",
                fontsize=7.5, color="#1A5276", fontweight="bold")

    def ln(x1, y1, x2, y2, c="gray", lw=1.3, ls="-", a=0.65):
        ax.plot([x1,x2],[y1,y2], color=c, lw=lw, linestyle=ls, alpha=a, zorder=1)

    # DCバス
    ln(1.2, 7.2, 9.2, 7.2, c="#1A5276", lw=2.5)
    ln(1.2, 0.7, 9.2, 0.7, c="#7F8C8D", lw=2.5)
    ax.text(0.9, 7.2, "DC+", ha="right", va="center",
            fontsize=8.5, color="#1A5276", fontweight="bold")
    ax.text(0.9, 0.7, "DC−", ha="right", va="center",
            fontsize=8.5, color="#7F8C8D", fontweight="bold")

    # VDC
    vc = CMISS if missing_vdc else COK
    vls = "--" if missing_vdc else "-"
    box(1.0, 3.95, "VDC\n600V", vc, w=1.1, h=1.0, fs=8, ls=vls)
    lc = CMISS if missing_vdc else "gray"
    la = 0.9
    ln(1.0, 4.45, 1.0, 7.2, c=lc, ls=vls, lw=1.3, a=la)
    ln(1.0, 3.45, 1.0, 0.7, c=lc, ls=vls, lw=1.3, a=la)
    if missing_vdc:
        ax.text(1.0, 3.95, "✕", ha="center", va="center",
                fontsize=20, color=CMISS, alpha=0.45, fontweight="bold")

    # CDC
    box(2.5, 3.95, "CDC\n1000μF", COK, w=1.15, h=1.0, fs=8)
    ln(2.5, 4.45, 2.5, 7.2)
    ln(2.5, 3.45, 2.5, 0.7)

    # 3相
    for px, ph in [(4.3,"A"), (6.2,"B"), (8.1,"C")]:
        i = ["A","B","C"].index(ph)
        qu = ["Q1","Q3","Q5"][i]
        ql = ["Q2","Q4","Q6"][i]
        rl = f"Rload_{ph}\n10Ω"
        box(px, 6.1, qu, COK, w=1.15, h=0.65)
        ln(px, 7.2, px, 6.43)
        ln(px, 5.78, px, 4.7)
        nd(px, 4.7, f"Ph{ph}")
        box(px, 3.3, ql, COK, w=1.15, h=0.65)
        ln(px, 4.37, px, 3.63)
        ln(px, 2.98, px, 0.7)
        box(px, 1.85, rl, COK, w=1.2, h=0.65, fs=7.5)
        ln(px, 4.7, px, 2.18, c="gray", lw=1.1, ls=":")
        ln(px, 1.53, px, 1.05, c="gray")

    ax.plot([4.3, 8.1], [1.05, 1.05], color="gray", lw=1.1)
    ax.text(6.2, 0.88, "NeutralLoad", ha="center",
            fontsize=7.5, color="#555")

    # 欠落アノテーション
    if missing_vdc:
        ax.annotate("VDC が\n欠落！",
                    xy=(1.0, 3.95), xytext=(3.0, 5.8),
                    fontsize=9, color=CMISS, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=CMISS, lw=1.8),
                    bbox=dict(boxstyle="round,pad=0.35",
                              fc="#FFECEC", ec=CMISS, lw=1.3))


# ════════════════════════════════════════════════════
# (2) 波形シミュレーション
# ════════════════════════════════════════════════════
def draw_waveform(ax, missing_vdc=False):
    bg = CBG_S if not missing_vdc else CBG_F
    ax.set_facecolor(bg)

    t  = np.linspace(0, 0.04, 4000)
    f0 = 50.0
    VDC_OK   = 600.0
    VDC_FAIL = 0.0      # VDC欠落→電源なし→0V

    # フーリエ近似（5次まで）
    def phase_voltage(t, vdc, phase_offset):
        v = sum(
            (2*vdc/np.pi) * np.sin(n*(2*np.pi*f0*t - phase_offset)) / n
            for n in [1, 3, 5]
        )
        return v

    phases_ok   = [phase_voltage(t, VDC_OK,   k*2*np.pi/3) for k in range(3)]
    phases_fail = [phase_voltage(t, VDC_FAIL, k*2*np.pi/3) for k in range(3)]

    phase_colors = ["#E74C3C", "#2980B9", "#27AE60"]
    phase_names  = ["U相", "V相", "W相"]

    # 期待波形（点線）
    for v, c in zip(phases_ok, phase_colors):
        ax.plot(t*1e3, v, color=c, lw=1.2, linestyle="--",
                alpha=0.4, label="_nolegend_")

    # AI出力回路からの波形（実線）
    phases_actual = phases_ok if not missing_vdc else phases_fail
    lbl_actual = ["U相","V相","W相"] if not missing_vdc else ["U相（0V）","V相（0V）","W相（0V）"]
    for v, c, n in zip(phases_actual, phase_colors, lbl_actual):
        ax.plot(t*1e3, v, color=c, lw=2.0, label=n)

    ax.set_xlim(0, 40)
    ax.set_xlabel("時間 [ms]", fontsize=10)
    ax.set_ylabel("相電圧 [V]", fontsize=10)
    ax.axhline(0, color="gray", lw=0.6)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8.5, loc="upper right",
              ncol=3 if not missing_vdc else 1)

    if not missing_vdc:
        ax.set_title("シミュレーション出力  ✓ 期待波形と一致",
                     fontsize=10, color=COK, pad=5)
        ax.set_ylim(-420, 420)
        # 振幅注釈
        ax.annotate(f"V_peak ≈ {2*VDC_OK/np.pi:.0f}V\n（期待値通り）",
                    xy=(5, 360), fontsize=8.5, color=COK,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white",
                              ec=COK, alpha=0.85))
        # 点線の説明
        ax.plot([], [], color="gray", lw=1.2, ls="--", label="期待波形（正解）")
        ax.legend(fontsize=8, loc="upper right", ncol=2,
                  framealpha=0.85)
    else:
        ax.set_title("シミュレーション出力  ✗ 電源なし → 出力 = 0V",
                     fontsize=10, color=CMISS, pad=5)
        ax.set_ylim(-420, 420)
        # 期待波形の注釈
        ax.annotate(
            "期待波形\n（VDC=600V）",
            xy=(8, 300), fontsize=8.5, color="#AAA",
            bbox=dict(boxstyle="round,pad=0.3", fc="white",
                      ec="#CCC", alpha=0.85)
        )
        ax.annotate("✗ AI出力：\nVDC欠落→0V",
                    xy=(20, 30), fontsize=9, color=CMISS, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#FFECEC",
                              ec=CMISS, lw=1.3))
        # 点線の説明
        ax.plot([], [], color="gray", lw=1.2, ls="--", label="期待波形（正解）")
        ax.plot([], [], color="gray", lw=2.0, label="AI出力（0V）")
        ax.legend(fontsize=8, loc="upper right", framealpha=0.85)


# ════════════════════════════════════════════════════
# メイン
# ════════════════════════════════════════════════════
def main():
    fig = plt.figure(figsize=(18, 16))
    fig.patch.set_facecolor("#F4F6F7")

    # ── タイトル ──────────────────────────────────────
    fig.text(0.5, 0.975,
             "AI 出力例：C4（3相 VSI インバータ）  T1 トポロジ認識タスク",
             ha="center", fontsize=17, fontweight="bold", color="#1C2833")
    fig.text(0.5, 0.952,
             "モデル：qwen3.5:9b  ／  入力形式の違いが認識精度と回路動作を決定づける",
             ha="center", fontsize=12, color="#555")

    # ── グリッド ──────────────────────────────────────
    outer = gridspec.GridSpec(2, 2,
                              height_ratios=[1, 1],
                              hspace=0.10, wspace=0.06,
                              left=0.04, right=0.96,
                              top=0.93, bottom=0.04)

    # 各象限をさらに 3 行に分割
    # [ヘッダ, 入力+グラフ, 波形]
    sub_ratios = [0.06, 0.46, 0.48]

    panels = {}
    for col, (label, hdr_color, bg) in enumerate([
        ("✓  成功例：Form-C（構造体 JSON）", CHDR_S, CBG_S),
        ("✗  失敗例：Form-A（アスキーアート）", CHDR_F, CBG_F),
    ]):
        gs_inner = gridspec.GridSpecFromSubplotSpec(
            3, 1, subplot_spec=outer[:, col],
            height_ratios=sub_ratios, hspace=0.06
        )

        # ヘッダ
        ax_h = fig.add_subplot(gs_inner[0])
        ax_h.set_facecolor(hdr_color)
        ax_h.text(0.5, 0.5, label, ha="center", va="center",
                  fontsize=13, fontweight="bold", color="white",
                  transform=ax_h.transAxes)
        ax_h.axis("off")

        # 入力テキスト（上半分）＋回路グラフ（下半分）を横並び
        gs_mid = gridspec.GridSpecFromSubplotSpec(
            1, 2, subplot_spec=gs_inner[1],
            width_ratios=[0.38, 0.62], wspace=0.04
        )

        ax_txt = fig.add_subplot(gs_mid[0])
        ax_gr  = fig.add_subplot(gs_mid[1])
        ax_wav = fig.add_subplot(gs_inner[2])

        panels[col] = (ax_txt, ax_gr, ax_wav)

    # ── 左列：成功例 ──────────────────────────────────
    ax_txt, ax_gr, ax_wav = panels[0]

    ax_txt.set_facecolor(CBG_S)
    ax_txt.axis("off")
    ax_txt.text(0.04, 0.97, "入力：構造体 JSON（Form-C）",
                transform=ax_txt.transAxes, fontsize=9,
                fontweight="bold", color=COK, va="top")
    ax_txt.text(0.04, 0.88, FORM_C_TEXT,
                transform=ax_txt.transAxes, fontsize=7.8,
                color="#1A252F", va="top", fontfamily="monospace",
                linespacing=1.55)

    draw_topology(ax_gr, missing_vdc=False)
    ax_gr.set_title("AI 出力：11 素子・22 接続  →  完全再現",
                    fontsize=10, color=COK, pad=5)

    draw_waveform(ax_wav, missing_vdc=False)

    # ── 右列：失敗例 ──────────────────────────────────
    ax_txt, ax_gr, ax_wav = panels[1]

    ax_txt.set_facecolor(CBG_F)
    ax_txt.axis("off")
    ax_txt.text(0.04, 0.97, "入力：アスキーアート（Form-A）",
                transform=ax_txt.transAxes, fontsize=9,
                fontweight="bold", color=CMISS, va="top")
    ax_txt.text(0.04, 0.88, FORM_A_TEXT,
                transform=ax_txt.transAxes, fontsize=7.8,
                color="#1A252F", va="top", fontfamily="monospace",
                linespacing=1.55)

    draw_topology(ax_gr, missing_vdc=True)
    ax_gr.set_title("AI 出力：VDC（電源）欠落  →  10/11 素子  (CR=0.91)",
                    fontsize=10, color=CMISS, pad=5)

    draw_waveform(ax_wav, missing_vdc=True)

    # ── スコアサマリー（図の最下部）──────────────────
    fig.text(0.25, 0.025,
             "スコア：  CR = 1.00   CA = 1.00   TE = 1.00  ✓",
             ha="center", fontsize=11, fontweight="bold", color=COK)
    fig.text(0.75, 0.025,
             "スコア：  CR = 0.91   CA = 1.00   TE = 0.00  ✗",
             ha="center", fontsize=11, fontweight="bold", color=CMISS)

    # ── 凡例 ─────────────────────────────────────────
    legend_items = [
        mpatches.Patch(color=COK,   label="正しく認識（正解一致）"),
        mpatches.Patch(color=CMISS, label="認識失敗（欠落・誤り）"),
        mpatches.Patch(color=CNODE, label="接続ノード"),
        plt.Line2D([0],[0], color="gray", lw=1.5, ls="--",
                   label="期待波形（正解）"),
        plt.Line2D([0],[0], color="#E74C3C", lw=2,
                   label="AI 出力波形"),
    ]
    fig.legend(handles=legend_items, loc="lower center", ncol=5,
               fontsize=9.5, framealpha=0.92,
               bbox_to_anchor=(0.5, 0.0))

    out = FIGURES_DIR / "example_success_vs_failure.png"
    plt.savefig(out, bbox_inches="tight", dpi=150,
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  → {out.name}")


if __name__ == "__main__":
    print("AI出力例 比較図（完全版）生成...")
    main()
    print("完了")
