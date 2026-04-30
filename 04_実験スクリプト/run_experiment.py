"""
LLMによる回路認識・生成 入力形式依存性実験
対応モデル: Ollama (qwen3.5:9b, qwen3:8b, gemma3:4b) / Claude API / OpenAI API
"""

import json
import time
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Literal

# パス設定
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from circuit_input_generator import get_all_inputs, get_ground_truth
from prompts import (
    TASK_T1_SYSTEM, TASK_T1_USER,
    TASK_T2_SYSTEM, TASK_T2_USERS,
    TASK_T3_SYSTEM, TASK_T3_USERS, TASK_T3_SPECS,
)

CIRCUIT_IDS = ["C1", "C2", "C3", "C4"]
FORM_NAMES = ["form_a", "form_b", "form_c"]
TASK_IDS = ["T1", "T2", "T3"]
N_REPEATS = 3  # 各条件の繰り返し回数

CIRCUIT_DIR  = BASE_DIR / "02_回路定義"
RESULTS_DIR  = BASE_DIR / "05_実験結果" / "raw"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ===========================================================
# モデルバックエンド
# ===========================================================

def call_ollama(model: str, system: str, user: str, temperature: float = 0.1) -> str:
    """Ollama REST API経由（think:false でthinking modeを無効化）"""
    import requests, re
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    resp = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"temperature": temperature, "num_predict": 2048},
        },
        timeout=180,
    )
    content = resp.json()["message"]["content"]
    # <think>...</think> タグが残っていた場合は除去
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    return content


def call_anthropic(model: str, system: str, user: str, temperature: float = 0.1) -> str:
    """Anthropic API経由で呼び出し"""
    import anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=2048,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


def call_openai(model: str, system: str, user: str, temperature: float = 0.1) -> str:
    """OpenAI API経由で呼び出し"""
    import openai
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = openai.OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
        max_tokens=2048,
    )
    return resp.choices[0].message.content.strip()


MODEL_BACKENDS = {
    # Ollama ローカルモデル
    "qwen3.5:9b":         ("ollama", "qwen3.5:9b"),
    "qwen3:8b":           ("ollama", "qwen3:8b"),
    "gemma3:4b":          ("ollama", "gemma3:4b"),
    "bonsai:8b":          ("ollama", "bonsai:8b"),
    "qwen2.5-coder:32b":  ("ollama", "qwen2.5-coder:32b"),
    # Anthropic API
    "claude-sonnet":      ("anthropic", "claude-sonnet-4-6"),
    "claude-haiku":       ("anthropic", "claude-haiku-4-5-20251001"),
    # OpenAI API
    "gpt-4o":             ("openai", "gpt-4o"),
    "gpt-4o-mini":        ("openai", "gpt-4o-mini"),
}


def call_model(model_key: str, system: str, user: str) -> tuple[str, float]:
    """モデルを呼び出してレスポンスと経過時間を返す"""
    if model_key not in MODEL_BACKENDS:
        # 未登録モデルはOllamaローカルとして自動扱い
        MODEL_BACKENDS[model_key] = ("ollama", model_key)
    backend, model_name = MODEL_BACKENDS[model_key]
    t0 = time.time()
    if backend == "ollama":
        response = call_ollama(model_name, system, user)
    elif backend == "anthropic":
        response = call_anthropic(model_name, system, user)
    elif backend == "openai":
        response = call_openai(model_name, system, user)
    else:
        raise ValueError(f"Unknown backend: {backend}")
    elapsed = time.time() - t0
    return response, elapsed


# ===========================================================
# プロンプト組み立て
# ===========================================================

def build_prompt(task_id: str, circuit_id: str, form: str, inputs: dict) -> tuple[str, str]:
    """(system_prompt, user_prompt) を返す"""
    circuit_input = inputs[form]

    if task_id == "T1":
        system = TASK_T1_SYSTEM
        user   = TASK_T1_USER.format(circuit_input=circuit_input)

    elif task_id == "T2":
        system = TASK_T2_SYSTEM
        user   = TASK_T2_USERS[circuit_id].format(circuit_input=circuit_input)

    elif task_id == "T3":
        # T3は「仕様→回路生成」なので入力形式によって出力形式が変わる
        system = TASK_T3_SYSTEM
        spec   = TASK_T3_SPECS[circuit_id]
        user   = TASK_T3_USERS[form].format(spec=spec)

    else:
        raise ValueError(f"Unknown task_id: {task_id}")

    return system, user


# ===========================================================
# 単一実験の実行
# ===========================================================

def run_single(model_key: str, task_id: str, circuit_id: str, form: str,
               trial: int, inputs: dict) -> dict:
    """1試行を実行してレコードを返す"""
    system, user = build_prompt(task_id, circuit_id, form, inputs)
    try:
        response, elapsed = call_model(model_key, system, user)
        error = None
    except Exception as e:
        response = ""
        elapsed = 0.0
        error = str(e)

    return {
        "model":      model_key,
        "task":       task_id,
        "circuit":    circuit_id,
        "form":       form,
        "trial":      trial,
        "response":   response,
        "elapsed_s":  round(elapsed, 2),
        "error":      error,
        "timestamp":  datetime.now().isoformat(),
    }


# ===========================================================
# メイン実験ループ
# ===========================================================

def run_experiment(models: list[str], tasks: list[str] = None,
                   circuits: list[str] = None, forms: list[str] = None,
                   n_repeats: int = N_REPEATS, output_tag: str = ""):
    tasks    = tasks    or TASK_IDS
    circuits = circuits or CIRCUIT_IDS
    forms    = forms    or FORM_NAMES

    total = len(models) * len(tasks) * len(circuits) * len(forms) * n_repeats
    print(f"\n{'='*60}")
    print(f"実験開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"モデル: {models}")
    print(f"総試行数: {total}")
    print(f"{'='*60}\n")

    all_results = []
    done = 0

    for model_key in models:
        for circuit_id in circuits:
            inputs = get_all_inputs(circuit_id, CIRCUIT_DIR)
            for task_id in tasks:
                for form in forms:
                    for trial in range(1, n_repeats + 1):
                        done += 1
                        print(f"[{done:3d}/{total}] {model_key} | {task_id} | {circuit_id} | {form} | trial={trial} ...", end=" ")
                        record = run_single(model_key, task_id, circuit_id, form, trial, inputs)
                        all_results.append(record)
                        status = "ERROR" if record["error"] else f"{record['elapsed_s']:.1f}s"
                        print(status)
                        # レート制限対策（ローカルモデルには不要だが一応）
                        if MODEL_BACKENDS[model_key][0] != "ollama":
                            time.sleep(0.5)

    # 結果保存
    tag = f"_{output_tag}" if output_tag else ""
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"results{tag}_{ts}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n結果保存: {out_path}")
    print(f"完了: {done}/{total} 試行")
    return all_results, out_path


# ===========================================================
# CLI
# ===========================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="回路認識・生成 LLM比較実験")
    parser.add_argument("--models",   nargs="+", default=["qwen3.5:9b", "qwen3:8b", "gemma3:4b"],
                        help="使用モデルキー（スペース区切り）")
    parser.add_argument("--tasks",    nargs="+", default=["T1", "T2", "T3"])
    parser.add_argument("--circuits", nargs="+", default=["C1", "C2", "C3", "C4"])
    parser.add_argument("--forms",    nargs="+", default=["form_a", "form_b", "form_c"])
    parser.add_argument("--repeats",  type=int,  default=3)
    parser.add_argument("--tag",      type=str,  default="")
    args = parser.parse_args()

    run_experiment(
        models=args.models,
        tasks=args.tasks,
        circuits=args.circuits,
        forms=args.forms,
        n_repeats=args.repeats,
        output_tag=args.tag,
    )
