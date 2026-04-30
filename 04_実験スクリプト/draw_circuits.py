"""
回路図生成スクリプト（schemdraw）
C1: 直列RLC、C2: H-bridge、C3: Buck、C4: 3相VSI
"""

import schemdraw
import schemdraw.elements as elm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

FIGURES_DIR = Path(__file__).parent.parent / "06_図表"
FIGURES_DIR.mkdir(exist_ok=True)

plt.rcParams["font.family"] = ["Hiragino Sans", "AppleGothic", "sans-serif"]


def draw_C1():
    """直列RLC回路"""
    path = FIGURES_DIR / "circuit_C1_series_RLC.png"
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=13)
        V = d.add(elm.SourceV().up().label("$V_s$\n10V", loc="left"))
        d.add(elm.Line().right())
        R = d.add(elm.Resistor().right().label("$R_1$\n100Ω"))
        L = d.add(elm.Inductor2().right().label("$L_1$\n10mH"))
        C = d.add(elm.Capacitor().right().label("$C_1$\n1μF"))
        d.add(elm.Line().down())
        d.add(elm.Line().left().tox(V.start))
        d.add(elm.Ground().at(V.start))
        d.save(str(path), dpi=150)
    plt.close("all")
    print("  → circuit_C1_series_RLC.png")


def draw_C2():
    """H-bridge（フルブリッジ）"""
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("C2: H-bridge インバータ  (VDC = 48 V)", fontsize=13, pad=10)

    # ノード座標
    nodes = {
        "VDC+": (3, 4.5), "VDC-": (3, 0.5),
        "ML":   (1, 2.5), "MR":   (5, 2.5),
    }

    # バス線
    ax.plot([1, 5], [4.5, 4.5], "k-", lw=2)   # 上バス
    ax.plot([1, 5], [0.5, 0.5], "k-", lw=2)   # 下バス
    ax.plot([3, 3], [4.5, 4.7], "k-", lw=1.5) # VDC上リード
    ax.plot([3, 3], [0.5, 0.3], "k-", lw=1.5) # VDC下リード

    # VDC（電源記号）
    for dy, sign in [(-0.15, "+"), (0.15, "−")]:
        ax.plot([2.7, 3.3], [4.7 + dy*2, 4.7 + dy*2], "k-", lw=2 if sign == "+" else 1)
    ax.annotate("$V_{DC}$\n48V", xy=(3, 5.0), ha="center", va="bottom", fontsize=11)
    ax.annotate("", xy=(3, 0.2), xytext=(3, 0.0),
                arrowprops=dict(arrowstyle="-", color="k"))

    # スイッチ（MOSFET）を矩形で表現
    sw_params = [
        ("Q1", 1, 3.5, "upper-L"), ("Q3", 5, 3.5, "upper-R"),
        ("Q2", 1, 1.5, "lower-L"), ("Q4", 5, 1.5, "lower-R"),
    ]
    for name, cx, cy, pos in sw_params:
        rect = plt.Rectangle((cx-0.4, cy-0.4), 0.8, 0.8,
                              fc="#AED6F1", ec="k", lw=1.5)
        ax.add_patch(rect)
        ax.text(cx, cy, name, ha="center", va="center", fontsize=10, fontweight="bold")
        # 上下接続線
        ax.plot([cx, cx], [cy+0.4, 4.5 if "upper" in pos else 2.5], "k-", lw=1.5)
        ax.plot([cx, cx], [cy-0.4, 0.5 if "lower" in pos else 2.5], "k-", lw=1.5)

    # 中点ノード
    ax.plot(1, 2.5, "ko", ms=5)
    ax.plot(5, 2.5, "ko", ms=5)

    # 負荷 R_load
    rx, ry = 3, 2.5
    rect = plt.Rectangle((rx-0.4, ry-0.5), 0.8, 1.0,
                          fc="#FDEBD0", ec="k", lw=1.5)
    ax.add_patch(rect)
    ax.text(rx, ry, "$R_{load}$\n10Ω", ha="center", va="center", fontsize=9)
    ax.plot([1, rx-0.4], [2.5, 2.5], "k-", lw=1.5)
    ax.plot([rx+0.4, 5], [2.5, 2.5], "k-", lw=1.5)

    # PWMペア注記
    ax.text(0.1, 4.8, "PWM pair: Q1+Q4 (0°)", fontsize=8, color="steelblue")
    ax.text(0.1, 4.5, "PWM pair: Q2+Q3 (180°)", fontsize=8, color="darkorange")

    # グランド記号
    for gx in [3]:
        ax.plot([gx-0.2, gx+0.2], [0.3, 0.3], "k-", lw=2)
        ax.plot([gx-0.12, gx+0.12], [0.15, 0.15], "k-", lw=1.5)
        ax.plot([gx-0.04, gx+0.04], [0.02, 0.02], "k-", lw=1)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "circuit_C2_hbridge.png", bbox_inches="tight", dpi=150)
    plt.close("all")
    print("  → circuit_C2_hbridge.png")


def draw_C3():
    """Buck コンバータ"""
    path = FIGURES_DIR / "circuit_C3_buck.png"
    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=13)
        V = d.add(elm.SourceV().up().label("$V_{in}$\n24V", loc="left"))
        d.add(elm.Line().right(1.5))
        SW = d.add(elm.Switch().right().label("$S_1$\n(MOSFET)", loc="top"))
        d.add(elm.Line().right(0.5))
        node_a = d.add(elm.Dot())
        L = d.add(elm.Inductor2().right().label("$L_1$\n500μH", loc="top"))
        node_b = d.add(elm.Dot())
        d.add(elm.Line().right(0.5))
        d.add(elm.Line().down(1))
        C = d.add(elm.Capacitor().down().label("$C_1$\n100μF", loc="right"))
        d.add(elm.Line().down(1))
        d.add(elm.Line().left().tox(V.start))
        d.add(elm.Ground().at(V.start))
        d.add(elm.Diode().at(node_a.end).down()
              .label("$D_1$", loc="right").reverse())
        d.save(str(path), dpi=150)
    plt.close("all")
    print("  → circuit_C3_buck.png")


def draw_C4():
    """3相VSI（シンプル図）"""
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.set_xlim(0, 7)
    ax.set_ylim(0, 5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("C4: 3相 VSI（電圧源インバータ）  VDC = 300 V", fontsize=13, pad=10)

    # DCバス
    ax.plot([0.5, 6.5], [4.5, 4.5], "k-", lw=2.5)  # 上バス P
    ax.plot([0.5, 6.5], [0.5, 0.5], "k-", lw=2.5)  # 下バス N
    ax.text(0.3, 4.5, "P", fontsize=12, fontweight="bold", va="center")
    ax.text(0.3, 0.5, "N", fontsize=12, fontweight="bold", va="center")

    # VDC
    ax.annotate("$V_{DC}$\n300V", xy=(0.1, 2.5), ha="center", va="center", fontsize=11)
    ax.plot([0.5, 0.5], [0.5, 4.5], "k--", lw=1, alpha=0.5)

    phases = [("U", 2), ("V", 3.5), ("W", 5)]
    colors_upper = ["#AED6F1", "#A9DFBF", "#F9E79F"]
    colors_lower = ["#85C1E9", "#82E0AA", "#F7DC6F"]

    for (ph, cx), cu, cl in zip(phases, colors_upper, colors_lower):
        # 上スイッチ
        rect = plt.Rectangle((cx-0.35, 3.3), 0.7, 0.8, fc=cu, ec="k", lw=1.5)
        ax.add_patch(rect)
        ax.text(cx, 3.7, f"T{ph}+", ha="center", va="center", fontsize=9, fontweight="bold")

        # 下スイッチ
        rect = plt.Rectangle((cx-0.35, 0.9), 0.7, 0.8, fc=cl, ec="k", lw=1.5)
        ax.add_patch(rect)
        ax.text(cx, 1.3, f"T{ph}−", ha="center", va="center", fontsize=9, fontweight="bold")

        # 接続線
        ax.plot([cx, cx], [4.5, 4.1], "k-", lw=1.5)   # 上バス→上SW
        ax.plot([cx, cx], [3.3, 2.5], "k-", lw=1.5)   # 上SW→中点
        ax.plot([cx, cx], [2.5, 1.7], "k-", lw=1.5)   # 中点→下SW
        ax.plot([cx, cx], [0.9, 0.5], "k-", lw=1.5)   # 下SW→下バス

        # 出力端子
        ax.plot(cx, 2.5, "ko", ms=6)
        ax.annotate(ph, xy=(cx, 2.2), ha="center", fontsize=11,
                    fontweight="bold", color="navy")

        # 出力線（負荷へ）
        ax.annotate("", xy=(cx, 1.9), xytext=(cx+0.5, 1.9),
                    arrowprops=dict(arrowstyle="->", color="gray", lw=1))

    # 負荷（Y結線）
    ax.text(6.2, 2.5, "Y負荷\n$R_{load}$", ha="center", va="center",
            fontsize=10, bbox=dict(boxstyle="round", fc="#FDEBD0", ec="k"))

    # グランド
    for gx in [3.5]:
        ax.plot([gx-0.2, gx+0.2], [0.3, 0.3], "k-", lw=2)
        ax.plot([gx-0.12, gx+0.12], [0.15, 0.15], "k-", lw=1.5)
        ax.plot([gx-0.04, gx+0.04], [0.02, 0.02], "k-", lw=1)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "circuit_C4_3phase_VSI.png", bbox_inches="tight", dpi=150)
    plt.close("all")
    print("  → circuit_C4_3phase_VSI.png")


if __name__ == "__main__":
    print("回路図生成開始...")
    draw_C1()
    draw_C2()
    draw_C3()
    draw_C4()
    print(f"\n全回路図 → {FIGURES_DIR}")
