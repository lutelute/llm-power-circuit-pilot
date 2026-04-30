"""
回路シミュレーション波形生成スクリプト（scipy / numpy）
C1: インピーダンス-周波数特性 + 過渡応答
C2: H-bridge 出力波形（PWM + フィルタ後）
C3: Buck コンバータ 出力電圧過渡応答
C4: 3相VSI 出力電圧波形
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import signal

FIGURES_DIR = Path(__file__).parent.parent / "06_図表"
FIGURES_DIR.mkdir(exist_ok=True)

plt.rcParams["font.family"] = ["Hiragino Sans", "AppleGothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150


# -------------------------------------------------------
# C1: 直列RLC — インピーダンス特性 + ステップ応答
# -------------------------------------------------------
def sim_C1():
    R, L, C = 100.0, 10e-3, 1e-6
    f0 = 1 / (2 * np.pi * np.sqrt(L * C))
    Q  = (1 / R) * np.sqrt(L / C)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    fig.suptitle("C1: 直列RLC回路  シミュレーション結果", fontsize=14)

    # --- 左: インピーダンス-周波数特性 ---
    ax = axes[0]
    freqs = np.logspace(2, 5, 1000)
    omega = 2 * np.pi * freqs
    Z = np.abs(R + 1j * omega * L + 1 / (1j * omega * C))
    ax.loglog(freqs, Z, color="#2980B9", lw=2)
    ax.axvline(f0, color="red", linestyle="--", lw=1.5, label=f"共振点 $f_0$ = {f0:.0f} Hz")
    ax.axhline(R,  color="gray", linestyle=":",  lw=1.5, label=f"$R$ = {R} Ω（共振時インピーダンス）")
    ax.set_xlabel("周波数 [Hz]", fontsize=12)
    ax.set_ylabel("|Z| [Ω]", fontsize=12)
    ax.set_title(f"インピーダンス特性  ($f_0$={f0:.0f} Hz, Q={Q:.3f})", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, which="both", alpha=0.3)

    # --- 右: ステップ応答（コンデンサ電圧） ---
    ax = axes[1]
    Vs = 10.0
    # 伝達関数: Vc/Vs = ω0² / (s² + ω0/Q·s + ω0²)
    omega0 = 2 * np.pi * f0
    num = [omega0**2]
    den = [1, omega0 / Q, omega0**2]
    sys = signal.TransferFunction(num, den)
    t = np.linspace(0, 0.005, 5000)
    t_out, y_out = signal.step(sys, T=t)
    ax.plot(t_out * 1e3, y_out * Vs, color="#27AE60", lw=2)
    ax.axhline(Vs, color="gray", linestyle="--", lw=1, alpha=0.7, label="定常値 10V")
    ax.set_xlabel("時間 [ms]", fontsize=12)
    ax.set_ylabel("コンデンサ電圧 $V_C$ [V]", fontsize=12)
    ax.set_title("ステップ応答（$V_s$ = 10V 印加）", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = FIGURES_DIR / "sim_C1_series_RLC.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  → {path.name}")


# -------------------------------------------------------
# C2: H-bridge — PWM出力 + フィルタ後波形
# -------------------------------------------------------
def sim_C2():
    VDC = 48.0
    f_pwm = 10e3
    f_out = 50.0
    Rload = 10.0
    t = np.linspace(0, 0.04, 40000)

    # PWM変調（正弦波基準）
    carrier = signal.sawtooth(2 * np.pi * f_pwm * t, width=0.5)
    ref = np.sin(2 * np.pi * f_out * t)
    pwm_u = np.where(ref > carrier, 1.0, -1.0) * VDC

    # 1次LCフィルタ（概略）
    L_f, C_f = 500e-6, 10e-6
    omega_lc = 1 / np.sqrt(L_f * C_f)
    b, a = signal.butter(2, omega_lc / (2 * np.pi), btype="low", fs=40000 / 0.04)
    v_filtered = signal.lfilter(b, a, pwm_u)

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    fig.suptitle("C2: H-bridge インバータ  出力波形（$f_{out}$=50Hz, $V_{DC}$=48V）", fontsize=14)

    axes[0].plot(t * 1e3, pwm_u, color="#E74C3C", lw=0.5, alpha=0.8)
    axes[0].set_ylabel("PWM出力電圧 [V]", fontsize=11)
    axes[0].set_title("PWM出力（未フィルタ）", fontsize=11)
    axes[0].grid(True, alpha=0.3)
    axes[0].set_ylim(-60, 60)

    axes[1].plot(t * 1e3, v_filtered, color="#2980B9", lw=2)
    axes[1].set_ylabel("フィルタ後電圧 [V]", fontsize=11)
    axes[1].set_xlabel("時間 [ms]", fontsize=12)
    axes[1].set_title("LCフィルタ後（正弦波近似）", fontsize=11)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlim(0, 40)

    plt.tight_layout()
    path = FIGURES_DIR / "sim_C2_hbridge.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  → {path.name}")


# -------------------------------------------------------
# C3: Buck コンバータ — 出力電圧過渡応答
# -------------------------------------------------------
def sim_C3():
    Vin  = 24.0
    Vout_target = 12.0   # デューティ比 0.5
    D    = Vout_target / Vin
    L    = 500e-6
    C    = 100e-6
    R    = 5.0
    fs   = 50e3

    # スイッチングシミュレーション（簡易：インダクタ電流・コンデンサ電圧を差分法で解く）
    dt = 1 / fs / 20
    T_sim = 0.005
    N = int(T_sim / dt)
    t = np.arange(N) * dt
    iL = np.zeros(N)
    vC = np.zeros(N)

    for k in range(1, N):
        sw = 1.0 if (t[k] % (1/fs)) < D / fs else 0.0
        dvC = (iL[k-1] - vC[k-1] / R) / C
        diL = (sw * Vin - vC[k-1]) / L
        vC[k] = vC[k-1] + dvC * dt
        iL[k] = iL[k-1] + diL * dt

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    fig.suptitle(f"C3: Buck コンバータ  過渡応答  ($V_{{in}}$={Vin}V → $V_{{out}}$≈{Vout_target}V, D={D:.2f})", fontsize=13)

    axes[0].plot(t * 1e3, vC, color="#27AE60", lw=1.5)
    axes[0].axhline(Vout_target, color="gray", linestyle="--", lw=1.2, label=f"目標 {Vout_target}V")
    axes[0].set_ylabel("出力電圧 $V_C$ [V]", fontsize=11)
    axes[0].set_title("出力電圧（コンデンサ電圧）", fontsize=11)
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(t * 1e3, iL, color="#E67E22", lw=1.5)
    axes[1].set_ylabel("インダクタ電流 $i_L$ [A]", fontsize=11)
    axes[1].set_xlabel("時間 [ms]", fontsize=12)
    axes[1].set_title("インダクタ電流", fontsize=11)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    path = FIGURES_DIR / "sim_C3_buck.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  → {path.name}")


# -------------------------------------------------------
# C4: 3相VSI — 3相出力電圧波形
# -------------------------------------------------------
def sim_C4():
    VDC = 300.0
    f   = 50.0
    t   = np.linspace(0, 0.04, 4000)

    # 180°導通モード（方形波 3相）
    phi = [0, 2*np.pi/3, 4*np.pi/3]
    labels = ["$v_U$", "$v_V$", "$v_W$"]
    colors = ["#E74C3C", "#2980B9", "#27AE60"]

    # 線間電圧
    theta = 2 * np.pi * f * t
    van = (2*VDC/np.pi) * (np.sin(theta) + np.sin(3*theta)/3 + np.sin(5*theta)/5)
    vbn = (2*VDC/np.pi) * (np.sin(theta - 2*np.pi/3) + np.sin(3*(theta-2*np.pi/3))/3
                            + np.sin(5*(theta-2*np.pi/3))/5)
    vcn = (2*VDC/np.pi) * (np.sin(theta - 4*np.pi/3) + np.sin(3*(theta-4*np.pi/3))/3
                            + np.sin(5*(theta-4*np.pi/3))/5)
    phases_v = [van, vbn, vcn]

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    fig.suptitle(f"C4: 3相VSI  出力波形  ($V_{{DC}}$={VDC}V, $f$={f}Hz)", fontsize=14)

    # 相電圧
    for v, lbl, col in zip(phases_v, labels, colors):
        axes[0].plot(t * 1e3, v, color=col, lw=1.5, label=lbl)
    axes[0].set_ylabel("相電圧 [V]", fontsize=11)
    axes[0].set_title("相電圧（フーリエ近似、5次高調波まで）", fontsize=11)
    axes[0].legend(fontsize=10, loc="upper right")
    axes[0].grid(True, alpha=0.3)
    axes[0].axhline(0, color="k", lw=0.5)

    # 線間電圧 UV
    v_uv = van - vbn
    axes[1].plot(t * 1e3, v_uv, color="#8E44AD", lw=1.8, label="$v_{UV}$")
    axes[1].set_ylabel("線間電圧 [V]", fontsize=11)
    axes[1].set_xlabel("時間 [ms]", fontsize=12)
    axes[1].set_title("線間電圧 $v_{UV}$", fontsize=11)
    axes[1].legend(fontsize=10)
    axes[1].grid(True, alpha=0.3)
    axes[1].axhline(0, color="k", lw=0.5)
    axes[1].set_xlim(0, 40)

    plt.tight_layout()
    path = FIGURES_DIR / "sim_C4_3phase_VSI.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  → {path.name}")


if __name__ == "__main__":
    print("シミュレーション波形生成開始...")
    sim_C1()
    sim_C2()
    sim_C3()
    sim_C4()
    print(f"\n全波形図 → {FIGURES_DIR}")
