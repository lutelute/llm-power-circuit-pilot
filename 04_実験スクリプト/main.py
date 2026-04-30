"""
実験全体の実行スクリプト
Usage:
  # ローカルモデルで全実験（推奨・APIキー不要）
  python main.py --models qwen3.5:9b qwen3:8b gemma3:4b

  # 単一モデルで動作確認
  python main.py --models qwen3.5:9b --circuits C1 --repeats 1

  # Anthropic API（要 ANTHROPIC_API_KEY）
  python main.py --models claude-sonnet --repeats 3
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from run_experiment import run_experiment
from evaluate       import evaluate_all, compute_summary
from visualize      import generate_all_figures


def main():
    parser = argparse.ArgumentParser(description="LLM回路認識実験 一括実行")
    parser.add_argument("--models",   nargs="+",
                        default=["qwen3.5:9b", "qwen3:8b", "gemma3:4b"],
                        help="使用モデル（スペース区切り）")
    parser.add_argument("--tasks",    nargs="+", default=["T1", "T2", "T3"])
    parser.add_argument("--circuits", nargs="+", default=["C1", "C2", "C3", "C4"])
    parser.add_argument("--forms",    nargs="+", default=["form_a", "form_b", "form_c"])
    parser.add_argument("--repeats",  type=int,  default=3)
    parser.add_argument("--tag",      type=str,  default="")
    parser.add_argument("--eval-only", type=str, default=None,
                        help="評価・可視化のみ実行（raw JSONファイルを指定）")
    parser.add_argument("--skip-viz",  action="store_true",
                        help="可視化をスキップ（matplotlib不要）")
    args = parser.parse_args()

    base_dir   = Path(__file__).parent.parent
    results_dir= base_dir / "05_実験結果"

    if args.eval_only:
        raw_path = Path(args.eval_only)
    else:
        # --- Phase 1: 実験実行 ---
        print("\n" + "="*60)
        print("Phase 1: LLM実験実行")
        print("="*60)
        results, raw_path = run_experiment(
            models   = args.models,
            tasks    = args.tasks,
            circuits = args.circuits,
            forms    = args.forms,
            n_repeats= args.repeats,
            output_tag=args.tag,
        )

    # --- Phase 2: 評価 ---
    print("\n" + "="*60)
    print("Phase 2: 結果評価")
    print("="*60)
    with open(raw_path, encoding="utf-8") as f:
        results = json.load(f)

    evaluated = evaluate_all(results)
    summary   = compute_summary(evaluated)

    eval_path = results_dir / f"evaluated_{raw_path.name}"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump({"records": evaluated, "summary": summary}, f,
                  ensure_ascii=False, indent=2)
    print(f"評価結果 → {eval_path}")

    # サマリー表示
    print("\n=== 評価サマリー ===")
    for k, v in sorted(summary.items()):
        metrics_str = ", ".join(
            f"{m}={d['mean']:.3f}" for m, d in v.items()
        )
        print(f"  {k}: {metrics_str}")

    # --- Phase 3: 可視化 ---
    if not args.skip_viz:
        print("\n" + "="*60)
        print("Phase 3: 図表生成")
        print("="*60)
        try:
            generate_all_figures(str(eval_path))
        except ImportError as e:
            print(f"matplotlib not available: {e}")
            print("可視化をスキップ（--skip-viz で非表示）")

    print("\n" + "="*60)
    print("実験完了")
    print(f"  raw結果    : {raw_path}")
    print(f"  評価結果   : {eval_path}")
    print(f"  図表       : {base_dir / '06_図表'}")
    print("="*60)


if __name__ == "__main__":
    main()
