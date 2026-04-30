"""
実験結果の可視化スクリプト
- fig01: 形式別 コンポーネント識別率（CR）、エラーバー付き
- fig02: 形式別 接続正確度（CA）
- fig03: 回路×形式 完全一致率ヒートマップ（TE）
- fig04: T1(認識) vs T2(解析) 精度比較（H2仮説検証）
- fig05: 総合比較レーダーチャート（3形式×モデル）★改善版
- fig06: 形式別数値正確度（NA）
- fig07: 応答時間（elapsed_s）比較 ★新規
- fig08: 全指標サマリーヒートマップ ★新規
"""

import json
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from collections import defaultdict

# 日本語フォント設定
plt.rcParams["font.family"] = ["Hiragino Sans", "Hiragino Kaku Gothic Pro",
                                "AppleGothic", "Yu Gothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150

FIGURES_DIR = Path(__file__).parent.parent / "06_図表"
FIGURES_DIR.mkdir(exist_ok=True)

FORM_LABELS = {
    "form_a": "Form-A\n(アスキーアート)",
    "form_b": "Form-B\n(自然言語)",
    "form_c": "Form-C\n(構造体JSON)",
}
FORM_COLORS = {
    "form_a": "#E74C3C",   # 赤
    "form_b": "#F39C12",   # オレンジ
    "form_c": "#27AE60",   # 緑
}
CIRCUIT_LABELS = {
    "C1": "C1\n直列RLC",
    "C2": "C2\nH-bridge",
    "C3": "C3\nBuck",
    "C4": "C4\n3相VSI",
}


def load_evaluated(eval_path: str) -> tuple[list, dict]:
    with open(eval_path, encoding="utf-8") as f:
        data = json.load(f)
    return data["records"], data["summary"]


def collect_scores(records: list, task: str, metric: str, by: str = "form") -> dict:
    """task・metricを指定してby（form/circuit/model）でスコアを集計"""
    buckets = defaultdict(list)
    for r in records:
        if r["task"] != task:
            continue
        scores = r.get("scores", {})
        val = scores.get(metric)
        if val is not None:
            buckets[r[by]].append(float(val))
    return {k: np.mean(v) for k, v in buckets.items() if v}


def collect_scores_with_err(records: list, task: str, metric: str, by: str = "form") -> dict:
    """mean, min, max を返す"""
    buckets = defaultdict(list)
    for r in records:
        if r["task"] != task:
            continue
        val = r.get("scores", {}).get(metric)
        if val is not None:
            buckets[r[by]].append(float(val))
    return {k: (np.mean(v), np.min(v), np.max(v)) for k, v in buckets.items() if v}


# ===========================================================
# fig01: 形式別 CR（T1）
# ===========================================================

def fig01_cr_by_form(records, models):
    fig, axes = plt.subplots(1, len(models), figsize=(5 * len(models), 5), sharey=True)
    if len(models) == 1:
        axes = [axes]

    for ax, model in zip(axes, models):
        model_records = [r for r in records if r["model"] == model]
        scores = collect_scores_with_err(model_records, "T1", "CR", by="form")
        forms  = ["form_a", "form_b", "form_c"]
        means  = [scores.get(f, (0, 0, 0))[0] for f in forms]
        errs_lo = [means[i] - scores.get(f, (0, 0, 0))[1] for i, f in enumerate(forms)]
        errs_hi = [scores.get(f, (0, 0, 0))[2] - means[i] for i, f in enumerate(forms)]
        labels = [FORM_LABELS[f] for f in forms]
        colors = [FORM_COLORS[f] for f in forms]
        bars = ax.bar(labels, means, color=colors, edgecolor="white", linewidth=1.5)
        ax.errorbar(labels, means, yerr=[errs_lo, errs_hi],
                    fmt="none", color="black", capsize=5, linewidth=1.5)
        for bar, val in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.04,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=11, fontweight="bold")
        ax.set_ylim(0, 1.2)
        ax.set_ylabel("コンポーネント識別率 (CR)", fontsize=12)
        ax.set_title(f"モデル: {model}", fontsize=12)
        ax.axhline(1.0, color="gray", linestyle="--", alpha=0.5)
        ax.set_yticks(np.arange(0, 1.3, 0.2))

    fig.suptitle("図1: 入力形式別 コンポーネント識別率（T1: トポロジ認識）", fontsize=14, y=1.02)
    plt.tight_layout()
    path = FIGURES_DIR / "fig01_CR_by_form.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  → {path}")
    return path


# ===========================================================
# fig02: 形式別 CA（T1）
# ===========================================================

def fig02_ca_by_form(records, models):
    fig, axes = plt.subplots(1, len(models), figsize=(5 * len(models), 5), sharey=True)
    if len(models) == 1:
        axes = [axes]

    for ax, model in zip(axes, models):
        model_records = [r for r in records if r["model"] == model]
        scores = collect_scores(model_records, "T1", "CA", by="form")
        forms  = ["form_a", "form_b", "form_c"]
        values = [scores.get(f, 0) for f in forms]
        labels = [FORM_LABELS[f] for f in forms]
        colors = [FORM_COLORS[f] for f in forms]
        bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=1.5)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=11, fontweight="bold")
        ax.set_ylim(0, 1.2)
        ax.set_ylabel("接続正確度 (CA)", fontsize=12)
        ax.set_title(f"モデル: {model}", fontsize=12)
        ax.axhline(1.0, color="gray", linestyle="--", alpha=0.5)

    fig.suptitle("図2: 入力形式別 接続正確度（T1: トポロジ認識）", fontsize=14, y=1.02)
    plt.tight_layout()
    path = FIGURES_DIR / "fig02_CA_by_form.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  → {path}")
    return path


# ===========================================================
# fig03: ヒートマップ（回路×形式, TE）
# ===========================================================

def fig03_te_heatmap(records, models):
    ncols = len(models)
    fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 4))
    if ncols == 1:
        axes = [axes]

    circuits = ["C1", "C2", "C3", "C4"]
    forms    = ["form_a", "form_b", "form_c"]

    for ax, model in zip(axes, models):
        model_records = [r for r in records if r["model"] == model and r["task"] == "T1"]
        matrix = []
        for circ in circuits:
            row = []
            for form in forms:
                vals = [
                    float(r["scores"]["TE"])
                    for r in model_records
                    if r["circuit"] == circ and r["form"] == form
                    and "TE" in r.get("scores", {})
                ]
                row.append(np.mean(vals) if vals else 0.0)
            matrix.append(row)
        matrix = np.array(matrix)

        im = ax.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
        ax.set_xticks(range(3))
        ax.set_xticklabels(["Form-A\n(ASCII)", "Form-B\n(自然言語)", "Form-C\n(JSON)"], fontsize=10)
        ax.set_yticks(range(4))
        ax.set_yticklabels([CIRCUIT_LABELS[c].replace("\n", " ") for c in circuits], fontsize=10)
        for i in range(4):
            for j in range(3):
                ax.text(j, i, f"{matrix[i, j]:.2f}",
                        ha="center", va="center", fontsize=12,
                        color="black" if matrix[i, j] > 0.4 else "white")
        ax.set_title(f"{model}", fontsize=11)
        plt.colorbar(im, ax=ax, label="完全一致率 (TE)")

    fig.suptitle("図3: 回路×入力形式 トポロジ完全一致率ヒートマップ", fontsize=13, y=1.02)
    plt.tight_layout()
    path = FIGURES_DIR / "fig03_TE_heatmap.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  → {path}")
    return path


# ===========================================================
# fig04: T1(認識) vs T2(解析) H2仮説検証
# ===========================================================

def fig04_t1_vs_t2(records, models):
    forms = ["form_a", "form_b", "form_c"]
    fig, ax = plt.subplots(figsize=(8, 5))

    x = np.arange(len(forms))
    width = 0.35 / len(models)
    offset = np.linspace(-0.15 * len(models), 0.15 * len(models), len(models))

    hatches_t1 = ["" , "//", "\\\\"]
    for mi, model in enumerate(models):
        model_records = [r for r in records if r["model"] == model]
        t1_cr = [collect_scores(model_records, "T1", "CR", "form").get(f, 0) for f in forms]
        t2_na = [collect_scores(model_records, "T2", "NA", "form").get(f, 0) for f in forms]

        bar_t1 = ax.bar(x + offset[mi] - width/2, t1_cr, width,
                        color=[FORM_COLORS[f] for f in forms], alpha=0.85,
                        label=f"{model} T1(認識)", hatch=hatches_t1[mi % 3])
        bar_t2 = ax.bar(x + offset[mi] + width/2, t2_na, width,
                        color=[FORM_COLORS[f] for f in forms], alpha=0.45,
                        label=f"{model} T2(解析)", hatch="xx")

    ax.set_xticks(x)
    ax.set_xticklabels([FORM_LABELS[f] for f in forms])
    ax.set_ylim(0, 1.2)
    ax.set_ylabel("精度スコア", fontsize=12)
    ax.set_title("図4: T1トポロジ認識 vs T2解析精度 — 形式依存性の非対称性（H2仮説）", fontsize=12)
    ax.axhline(1.0, color="gray", linestyle="--", alpha=0.3)

    # 凡例
    patches_form = [mpatches.Patch(color=FORM_COLORS[f], label=FORM_LABELS[f].replace("\n", " "))
                    for f in forms]
    legend1 = ax.legend(handles=patches_form, loc="upper left", title="入力形式", fontsize=9)
    ax.add_artist(legend1)

    solid_patch = mpatches.Patch(color="gray", alpha=0.9, label="T1: トポロジ認識 (CR)")
    light_patch = mpatches.Patch(color="gray", alpha=0.4, label="T2: 解析精度 (NA)")
    ax.legend(handles=[solid_patch, light_patch], loc="upper right", fontsize=10)

    plt.tight_layout()
    path = FIGURES_DIR / "fig04_T2_vs_T1.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  → {path}")
    return path


# ===========================================================
# fig05: レーダーチャート
# ===========================================================

def fig05_radar_chart(records, models):
    categories  = ["CR (T1)", "CA (T1)", "TE (T1)", "NA (T2)", "VS (T3)"]
    metrics_map = [("T1","CR"), ("T1","CA"), ("T1","TE"), ("T2","NA"), ("T3","VS")]
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    forms = ["form_a", "form_b", "form_c"]
    form_labels_short = {
        "form_a": "Form-A (アスキーアート)",
        "form_b": "Form-B (自然言語)",
        "form_c": "Form-C (構造体JSON)",
    }
    ncols = len(models)
    fig, axes = plt.subplots(1, ncols, figsize=(7 * ncols, 7),
                             subplot_kw=dict(polar=True))
    if ncols == 1:
        axes = [axes]

    for ax, model in zip(axes, models):
        model_records = [r for r in records if r["model"] == model]
        for form in forms:
            values = []
            for task, metric in metrics_map:
                sc = collect_scores(model_records, task, metric, "form")
                values.append(sc.get(form, 0.0))
            values += values[:1]
            ax.plot(angles, values, color=FORM_COLORS[form], linewidth=2.5,
                    label=form_labels_short[form])
            ax.fill(angles, values, color=FORM_COLORS[form], alpha=0.15)

        ax.set_thetagrids(np.degrees(angles[:-1]), categories, fontsize=13)
        ax.set_ylim(0, 1.0)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=10)
        ax.tick_params(axis="x", pad=12)
        ax.set_title(model, fontsize=13, pad=20)
        ax.legend(loc="upper right", bbox_to_anchor=(1.45, 1.15), fontsize=11,
                  framealpha=0.8)
        ax.grid(True, alpha=0.4)

    fig.suptitle("図5: 入力形式別 総合評価レーダーチャート", fontsize=15, y=1.02)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    path = FIGURES_DIR / "fig05_radar_chart.png"
    plt.savefig(path, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  → {path}")
    return path


# ===========================================================
# fig06: 形式×難易度 NA ヒートマップ
# ===========================================================

def fig06_na_by_difficulty(records, models):
    circuits = ["C1", "C2", "C3", "C4"]
    forms    = ["form_a", "form_b", "form_c"]
    ncols    = len(models)
    fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 4))
    if ncols == 1:
        axes = [axes]

    for ax, model in zip(axes, models):
        model_records = [r for r in records if r["model"] == model and r["task"] == "T2"]
        matrix = []
        for circ in circuits:
            row = []
            for form in forms:
                vals = [
                    float(r["scores"]["NA"])
                    for r in model_records
                    if r["circuit"] == circ and r["form"] == form
                    and "NA" in r.get("scores", {})
                ]
                row.append(np.mean(vals) if vals else 0.0)
            matrix.append(row)
        matrix = np.array(matrix)

        im = ax.imshow(matrix, vmin=0, vmax=1, cmap="Blues", aspect="auto")
        ax.set_xticks(range(3))
        ax.set_xticklabels(["Form-A", "Form-B", "Form-C"], fontsize=10)
        ax.set_yticks(range(4))
        ax.set_yticklabels([CIRCUIT_LABELS[c].replace("\n", " ") for c in circuits], fontsize=10)
        for i in range(4):
            for j in range(3):
                ax.text(j, i, f"{matrix[i, j]:.2f}",
                        ha="center", va="center", fontsize=12,
                        color="black" if matrix[i, j] < 0.6 else "white")
        ax.set_title(f"{model}", fontsize=11)
        plt.colorbar(im, ax=ax, label="数値正確度 (NA)")

    fig.suptitle("図6: 回路×入力形式 数値解析精度ヒートマップ（T2）", fontsize=13, y=1.02)
    plt.tight_layout()
    path = FIGURES_DIR / "fig06_NA_heatmap.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  → {path}")
    return path


# ===========================================================
# fig07: 応答時間（elapsed_s）ボックスプロット
# ===========================================================

def fig07_elapsed_time(records, models):
    forms = ["form_a", "form_b", "form_c"]
    form_labels_x = ["Form-A\n(ASCII)", "Form-B\n(自然言語)", "Form-C\n(JSON)"]

    fig, axes = plt.subplots(1, len(models), figsize=(5 * len(models), 5), sharey=True)
    if len(models) == 1:
        axes = [axes]

    for ax, model in zip(axes, models):
        model_records = [r for r in records if r["model"] == model]
        data = []
        for form in forms:
            vals = [r["elapsed_s"] for r in model_records
                    if r["form"] == form and r.get("elapsed_s") is not None]
            data.append(vals)

        bp = ax.boxplot(data, patch_artist=True, widths=0.5,
                        medianprops=dict(color="black", linewidth=2))
        for patch, form in zip(bp["boxes"], forms):
            patch.set_facecolor(FORM_COLORS[form])
            patch.set_alpha(0.7)

        ax.set_xticks(range(1, 4))
        ax.set_xticklabels(form_labels_x, fontsize=11)
        ax.set_ylabel("応答時間 (秒)", fontsize=12)
        ax.set_title(f"モデル: {model}", fontsize=12)
        ax.grid(axis="y", alpha=0.4)

    fig.suptitle("図7: 入力形式別 応答時間分布", fontsize=14, y=1.02)
    plt.tight_layout()
    path = FIGURES_DIR / "fig07_elapsed_time.png"
    plt.savefig(path, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  → {path}")
    return path


# ===========================================================
# fig08: 全指標サマリーヒートマップ（形式 × 指標）
# ===========================================================

def fig08_summary_heatmap(records, models):
    metrics_info = [
        ("T1", "CR", "CR (T1)"),
        ("T1", "CA", "CA (T1)"),
        ("T1", "TE", "TE (T1)"),
        ("T2", "NA", "NA (T2)"),
        ("T3", "VS", "VS (T3)"),
    ]
    forms = ["form_a", "form_b", "form_c"]
    form_labels_x = ["Form-A\n(ASCII)", "Form-B\n(自然言語)", "Form-C\n(JSON)"]
    metric_labels = [m[2] for m in metrics_info]

    ncols = len(models)
    fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 5))
    if ncols == 1:
        axes = [axes]

    for ax, model in zip(axes, models):
        model_records = [r for r in records if r["model"] == model]
        matrix = []
        for task, metric, _ in metrics_info:
            sc = collect_scores(model_records, task, metric, "form")
            matrix.append([sc.get(f, 0.0) for f in forms])
        matrix = np.array(matrix)

        im = ax.imshow(matrix, vmin=0, vmax=1, cmap="YlGn", aspect="auto")
        ax.set_xticks(range(3))
        ax.set_xticklabels(form_labels_x, fontsize=11)
        ax.set_yticks(range(len(metric_labels)))
        ax.set_yticklabels(metric_labels, fontsize=11)
        for i in range(len(metrics_info)):
            for j in range(3):
                ax.text(j, i, f"{matrix[i, j]:.2f}",
                        ha="center", va="center", fontsize=13,
                        color="black" if matrix[i, j] < 0.75 else "white")
        ax.set_title(f"{model}", fontsize=12)
        plt.colorbar(im, ax=ax, label="スコア")

    fig.suptitle("図8: 全評価指標サマリーヒートマップ（形式 × 指標）", fontsize=14, y=1.02)
    plt.tight_layout()
    path = FIGURES_DIR / "fig08_summary_heatmap.png"
    plt.savefig(path, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  → {path}")
    return path


# ===========================================================
# CLI
# ===========================================================

def generate_all_figures(eval_path: str):
    records, summary = load_evaluated(eval_path)
    models = sorted(set(r["model"] for r in records))
    print(f"\n可視化開始（モデル: {models}）")
    fig01_cr_by_form(records, models)
    fig02_ca_by_form(records, models)
    fig03_te_heatmap(records, models)
    fig04_t1_vs_t2(records, models)
    fig05_radar_chart(records, models)
    fig06_na_by_difficulty(records, models)
    fig07_elapsed_time(records, models)
    fig08_summary_heatmap(records, models)
    print(f"\n全図表 → {FIGURES_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="実験結果可視化")
    parser.add_argument("eval_file", help="evaluated_*.json のパス")
    args = parser.parse_args()
    generate_all_figures(args.eval_file)
