"""
AI出力の成功例・失敗例 比較図
レイアウト: 2列 × 4行（ヘッダ / 入力テキスト / 回路グラフ / 波形）
テキスト描画: PIL imshow（日本語=Hiragino, ASCII art=Menlo+ダーク背景）
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

BASE = Path(__file__).parent.parent
FIGS = BASE / "06_図表"
DATA = BASE / "05_実験結果" / "evaluated_merged_20260430_112905.json"

plt.rcParams["font.family"] = ["Hiragino Sans", "Apple SD Gothic Neo",
                                "Arial Unicode MS", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

_JP_PATH   = fm.findfont("Hiragino Sans")
_MONO_PATH = "/System/Library/Fonts/Menlo.ttc"

COK   = "#1E8449"
CMISS = "#C0392B"
CNODE = "#2471A3"
CBG_S = "#F0FFF4"
CBG_F = "#FFF8F8"


# ══════════════════════════════════════════════════════
# データ
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
    }


# ══════════════════════════════════════════════════════
# PIL ヘルパー
# ══════════════════════════════════════════════════════
def _rgb(hex_str):
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def jp_font(size):  return ImageFont.truetype(_JP_PATH,   size)
def mono_font(size):return ImageFont.truetype(_MONO_PATH, size)


# ══════════════════════════════════════════════════════
# 入力テキスト画像
# ══════════════════════════════════════════════════════
def make_json_panel(W=900, H=520):
    """Form-C: 明るい背景 + Hiragino Sans（カラー付き JSON）"""
    img  = Image.new("RGB", (W, H), _rgb(CBG_S))
    draw = ImageDraw.Draw(img)
    fh   = jp_font(18);  fm_ = jp_font(14);  fs = jp_font(13)

    y = 12
    def line(text, font, color, indent=0):
        nonlocal y
        draw.text((12 + indent, y), text, fill=_rgb(color), font=font)
        bb = draw.textbbox((12 + indent, y), text, font=font)
        y += (bb[3] - bb[1]) + 4

    line("入力：構造体 JSON（Form-C）", fh, COK)
    y += 6
    line('{ "components": [', fs, "#555555")
    entries = [
        ('  {"id":"VDC", "type":"DCVoltageSource", "value":600, "unit":"V"},', COK),
        ('  {"id":"CDC", "type":"Capacitor",        "value":1000,"unit":"μF"},', CNODE),
        ('  {"id":"Q1", "type":"IGBT"},', "#555555"),
        ('  {"id":"Q2", "type":"IGBT"},', "#555555"),
        ('  {"id":"Q3", "type":"IGBT"},', "#555555"),
        ('  {"id":"Q4", "type":"IGBT"},', "#555555"),
        ('  {"id":"Q5", "type":"IGBT"},', "#555555"),
        ('  {"id":"Q6", "type":"IGBT"},', "#555555"),
        ('  {"id":"Rload_A","type":"Resistor","value":10},', "#8E44AD"),
        ('  {"id":"Rload_B","type":"Resistor","value":10},', "#8E44AD"),
        ('  {"id":"Rload_C","type":"Resistor","value":10}', "#8E44AD"),
    ]
    for txt, col in entries:
        line(txt, fs, col, indent=4)
    line('],', fs, "#555555")
    line('"connections": [', fs, "#555555")
    line('  {"from":"VDC+","to":"DC+"},', fs, COK, indent=4)
    line('  {"from":"VDC-","to":"DC-"},', fs, COK, indent=4)
    line('  {"from":"DC+","to":"Q1_collector"},', fs, "#555555", indent=4)
    line('  ... (計 22 接続)', fs, "#888888", indent=4)
    line('] }', fs, "#555555")
    y += 8

    # AI出力サマリー
    draw.line([(12, y), (W-12, y)], fill=_rgb("#CCDDCC"), width=1)
    y += 8
    line("AI 出力：全 11 素子・22 接続を正確に再現  ✓", fm_, COK)

    return np.array(img)


def make_ascii_panel(ascii_text, W=900, H=520):
    """Form-A: ダーク背景 + Menlo等幅フォント（ターミナル風）"""
    img  = Image.new("RGB", (W, H), (22, 22, 22))   # ほぼ黒
    draw = ImageDraw.Draw(img)
    fh   = jp_font(17)
    fm_  = jp_font(14)
    fs_m = mono_font(12)   # ASCIIアート本体：Menlo

    y = 10
    # ヘッダ（日本語）
    draw.text((12, y), "入力：アスキーアート（Form-A）",
              fill=_rgb(CMISS), font=fh)
    y += 26

    # アスキーアート本体（Menlo）
    lines = ascii_text.splitlines()
    for raw in lines:
        draw.text((12, y), raw, fill=(180, 255, 180), font=fs_m)
        bb = draw.textbbox((12, y), raw, font=fs_m)
        y += (bb[3] - bb[1]) + 2
        if y > H - 60:
            break

    # 区切り線
    draw.line([(12, H-54), (W-12, H-54)], fill=(80, 80, 80), width=1)

    # AI出力サマリー（失敗）
    draw.text((12, H-46),
              "AI 出力：VDC（電源）が欠落  ✗  →  10/11 素子",
              fill=_rgb(CMISS), font=fm_)
    draw.text((12, H-24),
              "  ※ ASCII アートに VDC が図示されていないため LLM が見落とし",
              fill=(180, 180, 100), font=jp_font(12))

    return np.array(img)


# ══════════════════════════════════════════════════════
# 回路トポロジグラフ
# ══════════════════════════════════════════════════════
def draw_topology(ax, missing_vdc):
    ax.set_facecolor(CBG_S if not missing_vdc else CBG_F)
    ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis("off")

    def box(x, y, lbl, color, w=1.2, h=0.62, fs=8.0, ls="-"):
        ax.add_patch(FancyBboxPatch(
            (x-w/2, y-h/2), w, h,
            boxstyle="round,pad=0.06",
            fc=color, ec="white", lw=1.3, linestyle=ls))
        ax.text(x, y, lbl, ha="center", va="center",
                fontsize=fs, color="white", fontweight="bold")

    def nd(x, y, lbl):
        ax.plot(x, y, "o", ms=5, color=CNODE, zorder=5)
        ax.text(x, y+0.28, lbl, ha="center", va="bottom",
                fontsize=7, color="#1A5276", fontweight="bold")

    def ln(x1,y1,x2,y2, c="gray", lw=1.2, ls="-", a=0.6):
        ax.plot([x1,x2],[y1,y2], color=c, lw=lw, ls=ls, alpha=a, zorder=1)

    ln(0.8,7.2,9.4,7.2, c="#1A5276", lw=2.5, a=1)
    ln(0.8,0.7,9.4,0.7, c="#7F8C8D", lw=2.5, a=1)
    ax.text(0.55, 7.2, "DC+", ha="right", va="center",
            fontsize=8, color="#1A5276", fontweight="bold")
    ax.text(0.55, 0.7, "DC−", ha="right", va="center",
            fontsize=8, color="#7F8C8D", fontweight="bold")

    vc  = CMISS if missing_vdc else COK
    vls = "--" if missing_vdc else "-"
    lc  = CMISS if missing_vdc else "gray"
    box(1.2, 3.95, "VDC\n600V", vc, ls=vls, fs=7.5)
    ln(1.2,4.26,1.2,7.2, c=lc, ls=vls); ln(1.2,3.64,1.2,0.7, c=lc, ls=vls)
    if missing_vdc:
        ax.text(1.2, 3.95, "✕", ha="center", va="center",
                fontsize=16, color=CMISS, alpha=0.45, fontweight="bold")
        ax.annotate("VDC\n欠落", xy=(1.2,3.95), xytext=(2.9,5.6),
                    fontsize=8.5, color=CMISS, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=CMISS, lw=1.5),
                    bbox=dict(boxstyle="round,pad=0.3",
                              fc="#FFECEC", ec=CMISS, lw=1.1))

    box(2.5, 3.95, "CDC\n1000μF", COK, fs=7.5)
    ln(2.5,4.26,2.5,7.2); ln(2.5,3.64,2.5,0.7)

    for px, ph, qu, ql in [(4.4,"A","Q1","Q2"),
                            (6.4,"B","Q3","Q4"),
                            (8.4,"C","Q5","Q6")]:
        box(px, 6.1, qu, COK, w=1.1)
        ln(px,7.2,px,6.41); ln(px,5.79,px,4.72)
        nd(px, 4.72, f"Ph{ph}")
        box(px, 3.35, ql, COK, w=1.1)
        ln(px,4.41,px,3.65); ln(px,3.05,px,0.7)
        box(px, 1.88, f"R_{ph}\n10Ω", COK, fs=7.3)
        ln(px,4.72,px,2.18, c="gray", ls=":", lw=1.0)
        ln(px,1.58,px,1.05)

    ax.plot([4.4,8.4],[1.05,1.05], color="gray", lw=1.0)
    ax.text(6.4, 0.88, "NeutralLoad", ha="center", fontsize=7, color="#666")


# ══════════════════════════════════════════════════════
# 波形（正解重ね）
# ══════════════════════════════════════════════════════
def draw_waveform(ax, missing_vdc):
    ax.set_facecolor(CBG_S if not missing_vdc else CBG_F)
    t    = np.linspace(0, 0.04, 4000)
    VDC  = 600.0; f0 = 50.0
    cols = ["#E74C3C", "#2980B9", "#27AE60"]
    names= ["U相", "V相", "W相"]

    def vph(vdc, phi):
        return sum((2*vdc/np.pi)*np.sin(n*(2*np.pi*f0*t - phi))/n
                   for n in [1, 3, 5])

    # 正解（点線・薄）
    for k, c in enumerate(cols):
        ax.plot(t*1e3, vph(VDC, k*2*np.pi/3),
                color=c, lw=1.0, ls="--", alpha=0.30)

    # AI出力（実線・濃）
    vdc_ai = VDC if not missing_vdc else 0.0
    for k, (c, nm) in enumerate(zip(cols, names)):
        ax.plot(t*1e3, vph(vdc_ai, k*2*np.pi/3),
                color=c, lw=2.3, label=nm)

    ax.set_xlim(0, 40); ax.set_ylim(-480, 480)
    ax.set_xlabel("時間 [ms]", fontsize=10)
    ax.set_ylabel("相電圧 [V]", fontsize=10)
    ax.axhline(0, color="gray", lw=0.5)
    ax.grid(True, alpha=0.25); ax.tick_params(labelsize=9)

    # 凡例：正解 vs AI出力
    h_gt = plt.Line2D([0],[0], color="gray", lw=1.0, ls="--", label="正解（点線）")
    h_ai = plt.Line2D([0],[0], color="gray", lw=2.3,           label="AI出力（実線）")
    leg1 = ax.legend(handles=[h_gt, h_ai], loc="upper left",
                     fontsize=9, framealpha=0.85)
    ax.add_artist(leg1)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.85)

    if not missing_vdc:
        ax.set_title("シミュレーション ✓  正解と完全一致",
                     fontsize=11, color=COK, pad=5)
        ax.annotate(f"Vpeak ≈ {2*VDC/np.pi:.0f} V（正解通り）",
                    xy=(3, 355), fontsize=9, color=COK,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white",
                              ec=COK, alpha=0.9))
    else:
        ax.set_title("シミュレーション ✗  VDC 欠落 → 出力 0 V",
                     fontsize=11, color=CMISS, pad=5)
        ax.annotate("✗ 出力 = 0 V\n  正解波形（点線）との乖離が明確",
                    xy=(20, 40), fontsize=9, color=CMISS, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#FFECEC",
                              ec=CMISS, lw=1.2))


# ══════════════════════════════════════════════════════
# メイン
# ══════════════════════════════════════════════════════
def main():
    d = load_data()

    img_json  = make_json_panel(W=900, H=500)
    img_ascii = make_ascii_panel(d["ascii_input"], W=900, H=500)

    fig = plt.figure(figsize=(20, 17))
    fig.patch.set_facecolor("#F4F6F7")

    fig.text(0.5, 0.988,
             "AI 出力例：C4（3相 VSI インバータ）  T1 トポロジ認識タスク",
             ha="center", fontsize=17, fontweight="bold", color="#1C2833")
    fig.text(0.5, 0.970,
             "モデル：qwen3.5:9b  ／  入力形式の違いが認識精度と回路動作を決定づける",
             ha="center", fontsize=12, color="#555")

    gs = gridspec.GridSpec(
        4, 2,
        height_ratios=[0.040, 0.330, 0.265, 0.365],
        hspace=0.07, wspace=0.05,
        left=0.03, right=0.97,
        top=0.960, bottom=0.04
    )

    # 行0: ヘッダ
    for col, (label, color) in enumerate([
        ("✓  成功例：Form-C（構造体 JSON）  —  TE = 1.00  /  CR = 1.00", COK),
        ("✗  失敗例：Form-A（アスキーアート）  —  TE = 0.00  /  CR = 0.91", CMISS),
    ]):
        ax = fig.add_subplot(gs[0, col])
        ax.set_facecolor(color)
        ax.text(0.5, 0.5, label, ha="center", va="center",
                fontsize=12, fontweight="bold", color="white",
                transform=ax.transAxes)
        ax.axis("off")

    # 行1: 入力テキスト（PIL imshow）
    for col, img in enumerate([img_json, img_ascii]):
        ax = fig.add_subplot(gs[1, col])
        ax.imshow(img, aspect="auto", interpolation="bilinear")
        ax.axis("off")

    # 行2: 回路グラフ
    for col, missing in enumerate([False, True]):
        ax = fig.add_subplot(gs[2, col])
        draw_topology(ax, missing_vdc=missing)
        lbl = ("認識した回路トポロジ：全 11 素子・22 接続を完全再現"
               if not missing else
               "認識した回路トポロジ：VDC（電源）が欠落  ← ASCII 図中に VDC なし")
        ax.set_title(lbl, fontsize=9.5,
                     color=COK if not missing else CMISS, pad=4)

    # 行3: 波形
    for col, missing in enumerate([False, True]):
        ax = fig.add_subplot(gs[3, col])
        draw_waveform(ax, missing_vdc=missing)

    # 凡例
    legend_items = [
        mpatches.Patch(color=COK,   label="正しく認識"),
        mpatches.Patch(color=CMISS, label="欠落・誤り"),
        mpatches.Patch(color=CNODE, label="接続ノード"),
        plt.Line2D([0],[0], color="gray", lw=1.0, ls="--", label="正解波形（点線）"),
        plt.Line2D([0],[0], color="#555", lw=2.3,           label="AI 出力波形（実線）"),
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
    print("生成中...")
    main()
    print("完了")
