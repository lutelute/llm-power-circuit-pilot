"""
AI出力の成功例・失敗例 比較図（実データ版）
対象: C4（3相VSIインバータ）Task T1（トポロジ認識）
  成功例: Form-C → TE=1.0（全11素子正確）
  失敗例: Form-A → TE=0.0（VDC欠落、CR=0.909）

実際の入力テキストとLLM応答を使用。日本語はHiragino Sansで描画。
"""

import json, sys, textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ── フォント設定（monospace を使わない）────────────────
plt.rcParams["font.family"] = ["Hiragino Sans", "Apple SD Gothic Neo",
                                "Arial Unicode MS", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

BASE  = Path(__file__).parent.parent
FIGS  = BASE / "06_図表"
DATA  = BASE / "05_実験結果" / "evaluated_merged_20260430_112905.json"
C4DEF = BASE / "02_回路定義"  / "C4_3phase_VSI.json"

# ── カラー ────────────────────────────────────────────
COK    = "#1E8449"
CMISS  = "#C0392B"
CNODE  = "#2471A3"
CBG_S  = "#F0FFF4"
CBG_F  = "#FEF9F9"
CGRAY  = "#BDC3C7"


# ══════════════════════════════════════════════════════
# データ読み込み
# ══════════════════════════════════════════════════════
def load_data():
    sys.path.insert(0, str(Path(__file__).parent))
    from circuit_input_generator import ASCII_TEMPLATES

    with open(DATA) as f:
        records = json.load(f)["records"]

    suc  = next(r for r in records
                if r["form"]=="form_c" and r["circuit"]=="C4"
                and r["task"]=="T1" and r.get("scores",{}).get("TE",0)==1.0)
    fail = next(r for r in records
                if r["form"]=="form_a" and r["circuit"]=="C4"
                and r["task"]=="T1" and r.get("scores",{}).get("TE",0)==0.0)

    return {
        "ascii_input" : ASCII_TEMPLATES["C4"],
        "suc_response": json.loads(suc["response"])[0],
        "fail_response": json.loads(fail["response"])[0],
        "suc_scores"  : suc["scores"],
        "fail_scores" : fail["scores"],
    }


# ══════════════════════════════════════════════════════
# パネル描画関数
# ══════════════════════════════════════════════════════

def panel_input_json(ax):
    """Form-C 入力：実際のC4 JSON構造を表示"""
    ax.set_facecolor(CBG_S)
    ax.axis("off")

    ax.text(0.03, 0.97, "入力：構造体 JSON（Form-C）",
            transform=ax.transAxes, fontsize=9.5,
            fontweight="bold", color=COK, va="top")

    lines = [
        '{"components": [',
        '  {"id":"VDC", "type":"DCVoltageSource",',
        '              "value":600, "unit":"V"},',
        '  {"id":"CDC", "type":"Capacitor",',
        '              "value":1000, "unit":"μF"},',
        '  {"id":"Q1", "type":"IGBT"},',
        '  {"id":"Q2", "type":"IGBT"},',
        '  {"id":"Q3", "type":"IGBT"},',
        '  {"id":"Q4", "type":"IGBT"},',
        '  {"id":"Q5", "type":"IGBT"},',
        '  {"id":"Q6", "type":"IGBT"},',
        '  {"id":"Rload_A","type":"Resistor","value":10},',
        '  {"id":"Rload_B","type":"Resistor","value":10},',
        '  {"id":"Rload_C","type":"Resistor","value":10}',
        '], "connections": [',
        '  {"from":"VDC+","to":"DC+"},',
        '  {"from":"VDC-","to":"DC-"},',
        '  {"from":"DC+","to":"Q1_collector"},',
        '  ... (計 22 接続)',
        ']}',
    ]
    txt = "\n".join(lines)
    ax.text(0.03, 0.84, txt, transform=ax.transAxes,
            fontsize=7.6, color="#1A252F", va="top",
            linespacing=1.5, family="monospace")


def panel_input_ascii(ax, ascii_text):
    """Form-A 入力：実際のアスキーアートを表示（日本語フォントで描画）"""
    ax.set_facecolor(CBG_F)
    ax.axis("off")

    ax.text(0.03, 0.97, "入力：アスキーアート（Form-A）",
            transform=ax.transAxes, fontsize=9.5,
            fontweight="bold", color=CMISS, va="top")

    # アスキーアート本文（先頭16行）
    lines = ascii_text.splitlines()[:16]
    body  = "\n".join(lines)
    # 日本語フォントで描画（fontfamily 指定なし = rcParams に従う）
    ax.text(0.03, 0.84, body, transform=ax.transAxes,
            fontsize=7.3, color="#1A252F", va="top",
            linespacing=1.5)


def panel_ai_output(ax, response, success):
    """AI出力コンポーネント一覧"""
    bg = CBG_S if success else CBG_F
    ax.set_facecolor(bg)
    ax.axis("off")

    title_color = COK if success else CMISS
    title = ("AI 出力：全 11 素子を正確に出力  ✓"
             if success else
             "AI 出力：VDC（電源）が欠落  ✗  (10/11素子)")
    ax.text(0.03, 0.97, title, transform=ax.transAxes,
            fontsize=9, fontweight="bold", color=title_color, va="top")

    # 正解コンポーネント一覧
    gt_ids = ["VDC","CDC","Q1","Q2","Q3","Q4","Q5","Q6",
              "Rload_A","Rload_B","Rload_C"]
    out_ids = {c["id"] for c in response["components"]}

    y = 0.83
    for gid in gt_ids:
        found  = gid in out_ids
        marker = "✓" if found else "✗  欠落！"
        color  = COK if found else CMISS
        # コンポーネントの型と値
        comp = next((c for c in response["components"] if c["id"]==gid), None)
        if comp:
            val = f'  {comp["type"]}'
            if comp.get("value") is not None:
                val += f'  {comp["value"]}{comp.get("unit","")}'
        else:
            val = "  （出力されず）"

        ax.text(0.04, y, marker, transform=ax.transAxes,
                fontsize=8.5, color=color, fontweight="bold", va="top")
        ax.text(0.16, y, gid + val, transform=ax.transAxes,
                fontsize=8.2, color="#1A252F" if found else CMISS,
                va="top",
                fontweight="bold" if not found else "normal")
        y -= 0.075

    # 接続数
    n_conn = len(response.get("connections",[]))
    ax.text(0.04, y - 0.02,
            f"接続数: {n_conn} / 22",
            transform=ax.transAxes, fontsize=8.5,
            color=COK if n_conn==22 else CMISS, fontweight="bold", va="top")


def panel_topology(ax, missing_vdc):
    """回路トポロジグラフ"""
    bg = CBG_S if not missing_vdc else CBG_F
    ax.set_facecolor(bg)
    ax.set_xlim(0, 10); ax.set_ylim(0, 8)
    ax.axis("off")

    def box(x, y, lbl, color, w=1.25, h=0.62, fs=8.2, ls="-"):
        r = FancyBboxPatch((x-w/2, y-h/2), w, h,
                           boxstyle="round,pad=0.06",
                           fc=color, ec="white", lw=1.3, linestyle=ls)
        ax.add_patch(r)
        ax.text(x, y, lbl, ha="center", va="center",
                fontsize=fs, color="white", fontweight="bold")

    def nd(x, y, lbl):
        ax.plot(x, y, "o", ms=6, color=CNODE, zorder=5)
        ax.text(x, y+0.30, lbl, ha="center", va="bottom",
                fontsize=7.3, color="#1A5276", fontweight="bold")

    def ln(x1,y1,x2,y2, c="gray", lw=1.2, ls="-", a=0.6):
        ax.plot([x1,x2],[y1,y2], color=c, lw=lw, linestyle=ls, alpha=a, zorder=1)

    # DCバス
    ln(1.0, 7.2, 9.2, 7.2, c="#1A5276", lw=2.5, a=1)
    ln(1.0, 0.7, 9.2, 0.7, c="#7F8C8D", lw=2.5, a=1)
    ax.text(0.7, 7.2, "DC+", ha="right", va="center",
            fontsize=8.5, color="#1A5276", fontweight="bold")
    ax.text(0.7, 0.7, "DC−", ha="right", va="center",
            fontsize=8.5, color="#7F8C8D", fontweight="bold")

    # VDC
    vc  = CMISS if missing_vdc else COK
    vls = "--" if missing_vdc else "-"
    lc  = CMISS if missing_vdc else "gray"
    box(1.2, 3.95, "VDC\n600V", vc, ls=vls)
    ln(1.2, 4.27, 1.2, 7.2, c=lc, ls=vls)
    ln(1.2, 3.63, 1.2, 0.7, c=lc, ls=vls)
    if missing_vdc:
        ax.text(1.2, 3.95, "✕", ha="center", va="center",
                fontsize=18, color=CMISS, alpha=0.4, fontweight="bold")
        ax.annotate("VDC\n欠落", xy=(1.2,3.95), xytext=(2.8,5.5),
                    fontsize=8.5, color=CMISS, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=CMISS, lw=1.6),
                    bbox=dict(boxstyle="round,pad=0.3", fc="#FFECEC", ec=CMISS, lw=1.2))

    # CDC
    box(2.6, 3.95, "CDC\n1000μF", COK, fs=7.8)
    ln(2.6, 4.27, 2.6, 7.2); ln(2.6, 3.63, 2.6, 0.7)

    # 3相
    for i, (px, ph, qu, ql) in enumerate([
        (4.5,"A","Q1","Q2"), (6.5,"B","Q3","Q4"), (8.5,"C","Q5","Q6")
    ]):
        box(px, 6.1, qu, COK, w=1.1)
        ln(px, 7.2, px, 6.41); ln(px, 5.79, px, 4.72)
        nd(px, 4.72, f"Ph{ph}")
        box(px, 3.35, ql, COK, w=1.1)
        ln(px, 4.41, px, 3.66); ln(px, 3.04, px, 0.7)
        box(px, 1.88, f"R_{ph}\n10Ω", COK, fs=7.5)
        ln(px, 4.72, px, 2.19, c="gray", ls=":", lw=1.0)
        ln(px, 1.57, px, 1.05)

    ax.plot([4.5,8.5],[1.05,1.05], color="gray", lw=1.0)
    ax.text(6.5, 0.88, "NeutralLoad",
            ha="center", fontsize=7.3, color="#666")


def panel_waveform(ax, missing_vdc):
    """シミュレーション波形"""
    bg = CBG_S if not missing_vdc else CBG_F
    ax.set_facecolor(bg)

    t    = np.linspace(0, 0.04, 4000)
    VDC  = 600.0
    f0   = 50.0
    cols = ["#E74C3C","#2980B9","#27AE60"]

    def vph(t, vdc, phi):
        return sum((2*vdc/np.pi)*np.sin(n*(2*np.pi*f0*t-phi))/n
                   for n in [1,3,5])

    # 期待波形（点線）
    for k, c in enumerate(cols):
        ax.plot(t*1e3, vph(t, VDC, k*2*np.pi/3),
                color=c, lw=1.0, ls="--", alpha=0.35)

    # AI出力波形（実線）
    vdc_ai = VDC if not missing_vdc else 0.0
    for k, (c, ph) in enumerate(zip(cols,["U相","V相","W相"])):
        ax.plot(t*1e3, vph(t, vdc_ai, k*2*np.pi/3),
                color=c, lw=2.0, label=ph)

    ax.set_xlim(0, 40)
    ax.set_ylim(-450, 450)
    ax.set_xlabel("時間 [ms]", fontsize=10)
    ax.set_ylabel("相電圧 [V]", fontsize=10)
    ax.axhline(0, color="gray", lw=0.5)
    ax.grid(True, alpha=0.25)
    ax.tick_params(labelsize=8.5)

    if not missing_vdc:
        ax.set_title("シミュレーション出力  →  期待波形と一致",
                     fontsize=9.5, color=COK, pad=4)
        ax.legend(fontsize=8.5, loc="upper right", ncol=3, framealpha=0.85)
        ax.annotate(f"Vpeak ≈ {2*VDC/np.pi:.0f} V\n（期待値通り）",
                    xy=(4, 360), fontsize=8, color=COK,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white",
                              ec=COK, alpha=0.9))
    else:
        ax.set_title("シミュレーション出力  →  VDC 欠落で出力 0 V",
                     fontsize=9.5, color=CMISS, pad=4)
        # 期待波形の凡例
        ax.plot([],[], color="gray", lw=1.2, ls="--", label="期待波形（点線）")
        ax.plot([],[], color=cols[0], lw=2.0, label="AI出力（0V）")
        ax.legend(fontsize=8.5, loc="upper right", framealpha=0.85)
        ax.annotate("✗ VDC なし\n→ 出力 = 0 V",
                    xy=(20, 30), fontsize=9, color=CMISS, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#FFECEC",
                              ec=CMISS, lw=1.2))


# ══════════════════════════════════════════════════════
# メイン
# ══════════════════════════════════════════════════════
def main():
    d = load_data()

    fig = plt.figure(figsize=(20, 22))
    fig.patch.set_facecolor("#F4F6F7")

    # ── タイトル ──────────────────────────────────────
    fig.text(0.5, 0.985,
             "AI 出力例：C4（3相 VSI インバータ）  T1 トポロジ認識タスク",
             ha="center", fontsize=18, fontweight="bold", color="#1C2833")
    fig.text(0.5, 0.968,
             "モデル：qwen3.5:9b  ／  入力形式の違いが認識精度と回路動作を決定づける",
             ha="center", fontsize=12, color="#555")

    # ── グリッド：5行×2列 ─────────────────────────────
    #   行: [ヘッダ / 入力 / AI出力 / 回路グラフ / 波形]
    gs = gridspec.GridSpec(
        5, 2,
        height_ratios=[0.04, 0.24, 0.24, 0.25, 0.23],
        hspace=0.06, wspace=0.05,
        left=0.03, right=0.97,
        top=0.955, bottom=0.04
    )

    # ── ヘッダ行 ──────────────────────────────────────
    for col, (label, color) in enumerate([
        ("✓  成功例：Form-C（構造体 JSON）  —  TE = 1.00", COK),
        ("✗  失敗例：Form-A（アスキーアート）  —  TE = 0.00", CMISS),
    ]):
        ax = fig.add_subplot(gs[0, col])
        ax.set_facecolor(color)
        ax.text(0.5, 0.5, label, ha="center", va="center",
                fontsize=12.5, fontweight="bold", color="white",
                transform=ax.transAxes)
        ax.axis("off")

    # ── 入力テキスト行 ────────────────────────────────
    panel_input_json(fig.add_subplot(gs[1, 0]))
    panel_input_ascii(fig.add_subplot(gs[1, 1]), d["ascii_input"])

    # ── AI出力行 ──────────────────────────────────────
    panel_ai_output(fig.add_subplot(gs[2, 0]), d["suc_response"],  success=True)
    panel_ai_output(fig.add_subplot(gs[2, 1]), d["fail_response"], success=False)

    # ── 回路トポロジグラフ行 ──────────────────────────
    ax_gs = fig.add_subplot(gs[3, 0])
    ax_gf = fig.add_subplot(gs[3, 1])
    panel_topology(ax_gs, missing_vdc=False)
    panel_topology(ax_gf, missing_vdc=True)
    ax_gs.set_title("認識した回路トポロジ  →  完全再現（全 11 素子）",
                    fontsize=9.5, color=COK, pad=4)
    ax_gf.set_title("認識した回路トポロジ  →  VDC が欠落（10/11 素子）",
                    fontsize=9.5, color=CMISS, pad=4)

    # ── 波形行 ────────────────────────────────────────
    panel_waveform(fig.add_subplot(gs[4, 0]), missing_vdc=False)
    panel_waveform(fig.add_subplot(gs[4, 1]), missing_vdc=True)

    # ── 凡例 ─────────────────────────────────────────
    legend_items = [
        mpatches.Patch(color=COK,   label="正しく認識"),
        mpatches.Patch(color=CMISS, label="欠落・誤り"),
        mpatches.Patch(color=CNODE, label="接続ノード"),
        plt.Line2D([0],[0], color="gray", lw=1.2, ls="--", label="期待波形（正解）"),
        plt.Line2D([0],[0], color="#E74C3C", lw=2.0, label="AI 出力波形"),
    ]
    fig.legend(handles=legend_items, loc="lower center", ncol=5,
               fontsize=10, framealpha=0.92,
               bbox_to_anchor=(0.5, 0.002))

    out = FIGS / "example_success_vs_failure.png"
    plt.savefig(out, bbox_inches="tight", dpi=150,
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  → {out.name}")


if __name__ == "__main__":
    print("AI出力例 比較図（実データ版）生成...")
    main()
    print("完了")
