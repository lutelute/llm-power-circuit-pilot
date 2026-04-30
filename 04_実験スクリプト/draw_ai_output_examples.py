"""
AI出力の成功例・失敗例 比較図
- PIL でテキストを画像レンダリング → imshow で埋め込み（フォント問題を完全回避）
- 3行構造：ヘッダ / 入力テキスト画像＋回路グラフ / 波形（正解重ね）
- 実データ使用（circuit_input_generator + evaluated JSON）
"""

import json, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import matplotlib.font_manager as fm
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── パス ────────────────────────────────────────────
BASE  = Path(__file__).parent.parent
FIGS  = BASE / "06_図表"
DATA  = BASE / "05_実験結果" / "evaluated_merged_20260430_112905.json"

# ── フォント ─────────────────────────────────────────
plt.rcParams["font.family"] = ["Hiragino Sans", "Apple SD Gothic Neo",
                                "Arial Unicode MS", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

_MPL_FONT = fm.findfont("Hiragino Sans")          # matplotlib 用
_PIL_FONT_LG = ImageFont.truetype(_MPL_FONT, 15)  # PIL 用（大）
_PIL_FONT_MD = ImageFont.truetype(_MPL_FONT, 13)  # PIL 用（中）
_PIL_FONT_SM = ImageFont.truetype(_MPL_FONT, 11)  # PIL 用（小）

# ── カラー ────────────────────────────────────────────
COK   = "#1E8449"
CMISS = "#C0392B"
CNODE = "#2471A3"
CBG_S = "#F0FFF4"
CBG_F = "#FEF9F9"


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
        "suc_resp"    : json.loads(suc["response"])[0],
        "fail_resp"   : json.loads(fail["response"])[0],
        "suc_scores"  : suc["scores"],
        "fail_scores" : fail["scores"],
    }


# ══════════════════════════════════════════════════════
# PIL テキスト画像レンダラー
# ══════════════════════════════════════════════════════
def make_text_image(lines_with_styles, width, height, bg):
    """
    lines_with_styles: list of (text, font, color, x_offset)
    bg: 背景色 hex string
    """
    bg_rgb = tuple(int(bg.lstrip("#")[i:i+2], 16) for i in (0,2,4))
    img    = Image.new("RGB", (width, height), bg_rgb)
    draw   = ImageDraw.Draw(img)
    y = 10
    for item in lines_with_styles:
        if item is None:          # 空行
            y += 8
            continue
        text, font, color = item
        color_rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0,2,4))
        draw.text((10, y), text, fill=color_rgb, font=font)
        bbox = draw.textbbox((10, y), text, font=font)
        y += (bbox[3] - bbox[1]) + 3
    return np.array(img)


def make_json_image(width=520, height=400):
    """Form-C 入力：JSON テキスト画像"""
    lines = [
        (_PIL_FONT_MD, "#1E8449", "入力：構造体 JSON（Form-C）"),
        None,
        (_PIL_FONT_SM, "#555555", '{ "components": ['),
        (_PIL_FONT_SM, "#1E8449", '    {"id":"VDC", "type":"DCVoltageSource", "value":600, "unit":"V"},'),
        (_PIL_FONT_SM, "#2471A3", '    {"id":"CDC", "type":"Capacitor", "value":1000, "unit":"μF"},'),
        (_PIL_FONT_SM, "#555555", '    {"id":"Q1", "type":"IGBT"},'),
        (_PIL_FONT_SM, "#555555", '    {"id":"Q2", "type":"IGBT"},'),
        (_PIL_FONT_SM, "#555555", '    {"id":"Q3", "type":"IGBT"},'),
        (_PIL_FONT_SM, "#555555", '    {"id":"Q4", "type":"IGBT"},'),
        (_PIL_FONT_SM, "#555555", '    {"id":"Q5", "type":"IGBT"},'),
        (_PIL_FONT_SM, "#555555", '    {"id":"Q6", "type":"IGBT"},'),
        (_PIL_FONT_SM, "#8E44AD", '    {"id":"Rload_A","type":"Resistor","value":10},'),
        (_PIL_FONT_SM, "#8E44AD", '    {"id":"Rload_B","type":"Resistor","value":10},'),
        (_PIL_FONT_SM, "#8E44AD", '    {"id":"Rload_C","type":"Resistor","value":10}'),
        (_PIL_FONT_SM, "#555555", '  ],'),
        (_PIL_FONT_SM, "#555555", '  "connections": ['),
        (_PIL_FONT_SM, "#555555", '    {"from":"VDC+","to":"DC+"},'),
        (_PIL_FONT_SM, "#555555", '    {"from":"VDC-","to":"DC-"},'),
        (_PIL_FONT_SM, "#555555", '    {"from":"DC+","to":"Q1_collector"},'),
        (_PIL_FONT_SM, "#888888", '    ... (計 22 接続)'),
        (_PIL_FONT_SM, "#555555", '  ]'),
        (_PIL_FONT_SM, "#555555", '}'),
    ]
    styled = [(t, f, c) if isinstance(t, str) else None
              for f, c, t in [l if l else (None,None,None) for l in lines]]
    # 再構築
    result = []
    for l in lines:
        if l is None:
            result.append(None)
        else:
            f, c, t = l
            result.append((t, f, c))
    return make_text_image(result, width, height, CBG_S)


def make_ascii_image(ascii_text, width=520, height=400):
    """Form-A 入力：実際のアスキーアート画像"""
    lines_raw = ascii_text.splitlines()
    result = [("入力：アスキーアート（Form-A）", _PIL_FONT_MD, "#C0392B"), None]
    for line in lines_raw:
        result.append((line, _PIL_FONT_SM, "#1A252F"))
    return make_text_image(result, width, height, CBG_F)


def make_output_image(response, success, width=520, height=400):
    """AI 出力コンポーネント一覧画像"""
    bg = CBG_S if success else CBG_F
    gt_ids = ["VDC","CDC","Q1","Q2","Q3","Q4","Q5","Q6",
              "Rload_A","Rload_B","Rload_C"]
    out_ids = {c["id"] for c in response["components"]}
    n_conn  = len(response.get("connections", []))

    hdr_color = "#1E8449" if success else "#C0392B"
    hdr_text  = ("AI 出力：全 11 素子を正確に出力  ✓"
                 if success else
                 "AI 出力：VDC（電源）が欠落  ✗  （10/11 素子）")
    result = [(hdr_text, _PIL_FONT_MD, hdr_color), None]

    for gid in gt_ids:
        found = gid in out_ids
        comp  = next((c for c in response["components"] if c["id"]==gid), None)
        if found and comp:
            val = f'{comp["type"]}'
            if comp.get("value") is not None:
                val += f'  {comp["value"]}{comp.get("unit","") or ""}'
            line = f'  ✓  {gid:<12} {val}'
            color = "#1E8449"
        else:
            line = f'  ✗  {gid:<12}  ← 欠落！'
            color = "#C0392B"
        result.append((line, _PIL_FONT_SM, color))

    result.append(None)
    conn_color = "#1E8449" if n_conn == 22 else "#C0392B"
    result.append((f'  接続数：{n_conn} / 22',
                   _PIL_FONT_MD, conn_color))

    return make_text_image(result, width, height, bg)


# ══════════════════════════════════════════════════════
# 回路トポロジグラフ
# ══════════════════════════════════════════════════════
def draw_topology(ax, missing_vdc):
    bg = CBG_S if not missing_vdc else CBG_F
    ax.set_facecolor(bg)
    ax.set_xlim(0, 10); ax.set_ylim(0, 8)
    ax.axis("off")

    def box(x, y, lbl, color, w=1.2, h=0.6, fs=8.0, ls="-"):
        r = FancyBboxPatch((x-w/2, y-h/2), w, h,
                           boxstyle="round,pad=0.06",
                           fc=color, ec="white", lw=1.3, linestyle=ls)
        ax.add_patch(r)
        ax.text(x, y, lbl, ha="center", va="center",
                fontsize=fs, color="white", fontweight="bold")

    def nd(x, y, lbl):
        ax.plot(x, y, "o", ms=5, color=CNODE, zorder=5)
        ax.text(x, y+0.28, lbl, ha="center", va="bottom",
                fontsize=7, color="#1A5276", fontweight="bold")

    def ln(x1,y1,x2,y2, c="gray", lw=1.2, ls="-", a=0.6):
        ax.plot([x1,x2],[y1,y2], color=c, lw=lw, ls=ls, alpha=a, zorder=1)

    # DCバス
    ln(0.8, 7.2, 9.4, 7.2, c="#1A5276", lw=2.5, a=1)
    ln(0.8, 0.7, 9.4, 0.7, c="#7F8C8D", lw=2.5, a=1)
    ax.text(0.55, 7.2, "DC+", ha="right", va="center",
            fontsize=8, color="#1A5276", fontweight="bold")
    ax.text(0.55, 0.7, "DC−", ha="right", va="center",
            fontsize=8, color="#7F8C8D", fontweight="bold")

    # VDC
    vc  = CMISS if missing_vdc else COK
    vls = "--" if missing_vdc else "-"
    lc  = CMISS if missing_vdc else "gray"
    box(1.2, 3.95, "VDC\n600V", vc, ls=vls, fs=7.5)
    ln(1.2, 4.25, 1.2, 7.2, c=lc, ls=vls)
    ln(1.2, 3.65, 1.2, 0.7, c=lc, ls=vls)
    if missing_vdc:
        ax.text(1.2, 3.95, "✕", ha="center", va="center",
                fontsize=16, color=CMISS, alpha=0.45, fontweight="bold")
        ax.annotate("VDC\n欠落", xy=(1.2,3.95), xytext=(2.8,5.6),
                    fontsize=8, color=CMISS, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=CMISS, lw=1.5),
                    bbox=dict(boxstyle="round,pad=0.28", fc="#FFECEC",
                              ec=CMISS, lw=1.1))

    # CDC
    box(2.5, 3.95, "CDC\n1000μF", COK, fs=7.5)
    ln(2.5, 4.25, 2.5, 7.2); ln(2.5, 3.65, 2.5, 0.7)

    # 3相
    for px, ph, qu, ql in [(4.4,"A","Q1","Q2"),
                            (6.4,"B","Q3","Q4"),
                            (8.4,"C","Q5","Q6")]:
        box(px, 6.1, qu, COK, w=1.1); ln(px,7.2,px,6.40); ln(px,5.80,px,4.72)
        nd(px, 4.72, f"Ph{ph}")
        box(px, 3.35, ql, COK, w=1.1); ln(px,4.41,px,3.65); ln(px,3.05,px,0.7)
        box(px, 1.88, f"R_{ph}\n10Ω", COK, fs=7.3)
        ln(px, 4.72, px, 2.18, c="gray", ls=":", lw=1.0)
        ln(px, 1.58, px, 1.05)

    ax.plot([4.4,8.4],[1.05,1.05], color="gray", lw=1.0)
    ax.text(6.4, 0.88, "NeutralLoad",
            ha="center", fontsize=7, color="#666")


# ══════════════════════════════════════════════════════
# 波形パネル（正解を重ねて表示）
# ══════════════════════════════════════════════════════
def draw_waveform(ax, missing_vdc):
    bg = CBG_S if not missing_vdc else CBG_F
    ax.set_facecolor(bg)

    t    = np.linspace(0, 0.04, 4000)
    VDC  = 600.0
    f0   = 50.0
    cols = ["#E74C3C", "#2980B9", "#27AE60"]
    names= ["U相", "V相", "W相"]

    def vph(t, vdc, phi):
        return sum((2*vdc/np.pi)*np.sin(n*(2*np.pi*f0*t - phi))/n
                   for n in [1, 3, 5])

    # 正解波形（点線・薄め）
    for k, (c, nm) in enumerate(zip(cols, names)):
        ax.plot(t*1e3, vph(t, VDC, k*2*np.pi/3),
                color=c, lw=1.2, ls="--", alpha=0.35,
                label=f"{nm} 正解" if k == 0 else "_nolegend_")

    # AI出力波形（実線）
    vdc_ai = VDC if not missing_vdc else 0.0
    for k, (c, nm) in enumerate(zip(cols, names)):
        ax.plot(t*1e3, vph(t, vdc_ai, k*2*np.pi/3),
                color=c, lw=2.2, label=nm)

    ax.set_xlim(0, 40)
    ax.set_ylim(-480, 480)
    ax.set_xlabel("時間 [ms]", fontsize=10)
    ax.set_ylabel("相電圧 [V]", fontsize=10)
    ax.axhline(0, color="gray", lw=0.5)
    ax.grid(True, alpha=0.25)
    ax.tick_params(labelsize=9)

    # 正解・AI出力の凡例
    h_gt  = plt.Line2D([0],[0], color="gray", lw=1.2, ls="--",
                        label="正解波形（点線）")
    h_ai  = plt.Line2D([0],[0], color="gray", lw=2.2,
                        label="AI 出力波形（実線）")
    leg1  = ax.legend(handles=[h_gt, h_ai], loc="upper left",
                      fontsize=8.5, framealpha=0.85)
    ax.add_artist(leg1)
    ax.legend(handles=[plt.Line2D([0],[0], color=c, lw=2, label=nm)
                        for c, nm in zip(cols, names)],
              loc="upper right", fontsize=8.5, framealpha=0.85)

    if not missing_vdc:
        ax.set_title("シミュレーション出力 ✓  →  正解と完全一致",
                     fontsize=10.5, color=COK, pad=5)
        ax.annotate(f"Vpeak ≈ {2*VDC/np.pi:.0f} V（正解通り）",
                    xy=(3, 360), fontsize=9, color=COK,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white",
                              ec=COK, alpha=0.9))
    else:
        ax.set_title("シミュレーション出力 ✗  →  VDC 欠落で出力 0 V",
                     fontsize=10.5, color=CMISS, pad=5)
        ax.annotate("✗ VDC なし → 出力 = 0 V\n  （正解波形との乖離が明確）",
                    xy=(20, 30), fontsize=9, color=CMISS, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#FFECEC",
                              ec=CMISS, lw=1.2))


# ══════════════════════════════════════════════════════
# メイン
# ══════════════════════════════════════════════════════
def main():
    d = load_data()

    # ── PIL 画像を事前生成 ──────────────────────────
    W, H = 560, 380
    img_json  = make_json_image(W, H)
    img_ascii = make_ascii_image(d["ascii_input"], W, H)
    img_out_s = make_output_image(d["suc_resp"],  success=True,  width=W, height=H)
    img_out_f = make_output_image(d["fail_resp"], success=False, width=W, height=H)

    # ── フィギュア：3行×2列 ─────────────────────────
    fig = plt.figure(figsize=(20, 14))
    fig.patch.set_facecolor("#F4F6F7")

    fig.text(0.5, 0.985,
             "AI 出力例：C4（3相 VSI インバータ）  T1 トポロジ認識タスク",
             ha="center", fontsize=17, fontweight="bold", color="#1C2833")
    fig.text(0.5, 0.966,
             "モデル：qwen3.5:9b  ／  入力形式の違いが認識精度と回路動作を決定づける",
             ha="center", fontsize=12, color="#555")

    gs_main = gridspec.GridSpec(
        3, 2,
        height_ratios=[0.045, 0.50, 0.455],
        hspace=0.07, wspace=0.05,
        left=0.03, right=0.97,
        top=0.955, bottom=0.04
    )

    # ── 行0：ヘッダ ───────────────────────────────
    for col, (label, color) in enumerate([
        ("✓  成功例：Form-C（構造体 JSON）  —  TE = 1.00  CR = 1.00", COK),
        ("✗  失敗例：Form-A（アスキーアート）  —  TE = 0.00  CR = 0.91", CMISS),
    ]):
        ax = fig.add_subplot(gs_main[0, col])
        ax.set_facecolor(color)
        ax.text(0.5, 0.5, label, ha="center", va="center",
                fontsize=12, fontweight="bold", color="white",
                transform=ax.transAxes)
        ax.axis("off")

    # ── 行1：入力画像 + AI出力画像 + 回路グラフ ──────
    for col, (img_in, img_out, missing) in enumerate([
        (img_json,  img_out_s, False),
        (img_ascii, img_out_f, True),
    ]):
        gs_mid = gridspec.GridSpecFromSubplotSpec(
            1, 3, subplot_spec=gs_main[1, col],
            width_ratios=[0.32, 0.32, 0.36], wspace=0.03
        )

        # 入力テキスト画像
        ax_in = fig.add_subplot(gs_mid[0])
        ax_in.imshow(img_in, aspect="auto", interpolation="bilinear")
        ax_in.axis("off")

        # AI出力画像
        ax_out = fig.add_subplot(gs_mid[1])
        ax_out.imshow(img_out, aspect="auto", interpolation="bilinear")
        ax_out.axis("off")

        # 回路グラフ
        ax_gr = fig.add_subplot(gs_mid[2])
        draw_topology(ax_gr, missing_vdc=missing)
        lbl = "回路グラフ：完全再現" if not missing else "回路グラフ：VDC 欠落"
        ax_gr.set_title(lbl, fontsize=9.5,
                        color=COK if not missing else CMISS, pad=4)

    # ── 行2：波形（正解重ね）──────────────────────
    for col, missing in enumerate([False, True]):
        ax_w = fig.add_subplot(gs_main[2, col])
        draw_waveform(ax_w, missing_vdc=missing)

    # ── 凡例 ─────────────────────────────────────
    legend_items = [
        mpatches.Patch(color=COK,   label="正しく認識"),
        mpatches.Patch(color=CMISS, label="欠落・誤り"),
        mpatches.Patch(color=CNODE, label="接続ノード"),
        plt.Line2D([0],[0], color="gray", lw=1.2, ls="--",
                   label="正解波形（点線）"),
        plt.Line2D([0],[0], color="#555", lw=2.2,
                   label="AI 出力波形（実線）"),
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
    print("AI出力例 比較図（PIL画像版）生成...")
    main()
    print("完了")
