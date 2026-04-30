"""
実験結果の評価スクリプト
- T1: コンポーネント識別率・接続精度・完全一致率
- T2: 数値正確度
- T3: 生成妥当性スコア
"""

import json
import re
import math
import sys
from pathlib import Path
from typing import Optional

BASE_DIR   = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from circuit_input_generator import get_ground_truth

CIRCUIT_DIR = BASE_DIR / "02_回路定義"

# 正解データ（回路ごとの期待値）
GROUND_TRUTH_T2 = {
    "C1": {
        "resonant_frequency_Hz": 503.3,
        "impedance_at_resonance_Ohm": 100.0,
        "Q_factor": 0.316,
    },
    "C2": {
        "output_voltage_peak_V": 48.0,
        "output_voltage_rms_V": 48.0,
        "current_at_full_load_A": 4.8,
    },
    "C3": {
        "output_voltage_V": 12.0,
        "inductor_current_ripple_A": 0.6,
        "capacitor_voltage_ripple_V": 0.045,
    },
    "C4": {
        "phase_voltage_rms_V": 173.2,
        "line_voltage_rms_V": 300.0,
        "dc_link_utilization": 0.816,
    },
}

GROUND_TRUTH_T1 = {
    "C1": {"component_count": 4, "node_count": 4},
    "C2": {"component_count": 6, "node_count": 4},
    "C3": {"component_count": 6, "node_count": 4},
    "C4": {"component_count": 11, "node_count": 7},
}


# ===========================================================
# JSON 抽出ユーティリティ
# ===========================================================

def extract_json(text: str) -> Optional[dict]:
    """応答テキストからJSONを抽出"""
    if not text:
        return None
    # thinking タグ除去（qwen3.5等のThinking mode対策）
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # コードブロック除去
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.replace("```", "")
    # オブジェクト { ... } を最長一致で取り出す（greedy）
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group())
            # components / calculations など主要キーを持っていれば採用
            if any(k in obj for k in ("components", "calculations", "topology_summary", "nodes")):
                return obj
        except json.JSONDecodeError:
            pass
    # トップレベル配列 [ {主要キーあり}, ... ] の場合は最初の要素を使う
    arr_m = re.search(r"\[.*\]", text, re.DOTALL)
    if arr_m:
        try:
            arr = json.loads(arr_m.group())
            if isinstance(arr, list) and arr and isinstance(arr[0], dict):
                first = arr[0]
                if any(k in first for k in ("components", "calculations", "topology_summary", "nodes")):
                    return first
        except json.JSONDecodeError:
            pass
    # 最後の手段：最長 { } をそのまま返す
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def extract_numbers(text: str) -> list[float]:
    """テキストから数値を全抽出"""
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", text)]


# ===========================================================
# T1 評価
# ===========================================================

def evaluate_t1(response: str, circuit_id: str) -> dict:
    """
    コンポーネント識別率 (CR) と接続精度 (CA)、完全一致率 (TE) を返す
    """
    gt = GROUND_TRUTH_T1[circuit_id]
    parsed = extract_json(response)

    if parsed is None:
        return {"CR": 0.0, "CA": 0.0, "TE": 0, "parse_ok": False, "notes": "JSON parse failed"}

    # コンポーネント数比較（厳密なリスト比較は難しいのでカウントベース）
    pred_components = parsed.get("components", [])
    pred_count      = len(pred_components)
    gt_count        = gt["component_count"]
    # 予測数が正解数と同じなら CR = 1.0、差があれば比例
    cr = min(pred_count, gt_count) / max(gt_count, 1)

    # 接続数比較
    pred_connections = parsed.get("connections", [])
    topology = parsed.get("topology_summary", {})
    pred_node_count  = topology.get("node_count", 0)
    gt_node_count    = gt["node_count"]
    # ノード数も考慮
    node_score = min(pred_node_count, gt_node_count) / max(gt_node_count, 1) if pred_node_count > 0 else 0.5
    # 接続数は素子数から推定（直列の場合ほぼ素子数と同じ）
    expected_connections = gt_count  # 最低限の接続数
    ca = min(len(pred_connections), expected_connections) / max(expected_connections, 1)

    # 完全一致: CR=1.0 かつ ノード数一致
    te = 1 if (cr >= 0.95 and abs(pred_node_count - gt_node_count) <= 1) else 0

    return {
        "CR": round(cr, 3),
        "CA": round(ca, 3),
        "TE": te,
        "parse_ok": True,
        "pred_component_count": pred_count,
        "gt_component_count": gt_count,
        "pred_node_count": pred_node_count,
        "gt_node_count": gt_node_count,
        "notes": "",
    }


# ===========================================================
# T2 評価
# ===========================================================

def evaluate_t2(response: str, circuit_id: str) -> dict:
    """数値正確度 (NA) を返す。正解の±10%以内で正解"""
    gt_values = GROUND_TRUTH_T2[circuit_id]
    parsed = extract_json(response)

    results = {}
    correct = 0
    total   = len(gt_values)

    # JSON解析できた場合
    # 全数値をヒューリスティックに正解と比較（キー名不一致でも検出できるよう常に実行）
    numbers = extract_numbers(response)

    if parsed and "calculations" in parsed:
        calcs = parsed["calculations"]
        # 全calculationsの数値を抽出してnumbersに追加
        for pred_key, pred_data in calcs.items():
            v = pred_data.get("value") if isinstance(pred_data, dict) else pred_data
            if isinstance(v, (int, float)):
                numbers.append(float(v))

    for gt_key, gt_val in gt_values.items():
        # キー名部分一致（JSON解析できた場合）
        found_val = None
        if parsed and "calculations" in parsed:
            for pred_key, pred_data in parsed["calculations"].items():
                if gt_key.lower() in pred_key.lower() or pred_key.lower() in gt_key.lower():
                    v = pred_data.get("value") if isinstance(pred_data, dict) else pred_data
                    if isinstance(v, (int, float)):
                        found_val = float(v)
                        break
        # ヒューリスティック：正解値に近い数値が応答に含まれているか
        heuristic_match = any(
            abs(n - gt_val) / max(abs(gt_val), 1e-9) <= 0.10
            for n in numbers
        )
        ok = heuristic_match or (
            found_val is not None
            and abs(found_val - gt_val) / max(abs(gt_val), 1e-9) <= 0.10
        )
        if ok:
            best_pred = found_val or next(
                (n for n in numbers if abs(n - gt_val) / max(abs(gt_val), 1e-9) <= 0.10),
                None,
            )
            rel_err = abs(best_pred - gt_val) / max(abs(gt_val), 1e-9) if best_pred else None
            results[gt_key] = {"pred": best_pred, "gt": gt_val,
                                "rel_err": round(rel_err, 4) if rel_err else None, "ok": True}
            correct += 1
        else:
            results[gt_key] = {"pred": found_val, "gt": gt_val, "rel_err": None, "ok": False}

    na = correct / max(total, 1)
    confidence_raw = (parsed or {}).get("confidence", "unknown")

    return {
        "NA": round(na, 3),
        "correct": correct,
        "total": total,
        "parse_ok": parsed is not None,
        "confidence": confidence_raw,
        "details": results,
    }


# ===========================================================
# T3 評価
# ===========================================================

def evaluate_t3(response: str, circuit_id: str, form: str) -> dict:
    """
    生成妥当性スコア (VS) を返す
    form_c: JSON検証ができるので厳密、form_a/b: ルーブリックベース
    """
    if not response:
        return {"VS": 0.0, "spec_ok": False, "struct_ok": False, "num_ok": False, "parse_ok": False}

    gt_t1 = GROUND_TRUTH_T1[circuit_id]
    gt_t2 = GROUND_TRUTH_T2[circuit_id]

    # --- 構造的妥当性 ---
    if form == "form_c":
        parsed = extract_json(response)
        struct_ok = (
            parsed is not None
            and "components" in parsed
            and "connections" in parsed
            and len(parsed.get("components", [])) >= max(gt_t1["component_count"] - 2, 1)
        )
        pred_comp_count = len(parsed.get("components", [])) if parsed else 0
    else:
        # form_a/b: 素子名称が含まれているかチェック
        component_keywords = {
            "C1": ["R", "L", "C", "V", "抵抗", "インダクタ", "キャパシタ"],
            "C2": ["Q", "MOSFET", "bridge", "スイッチ", "Rload"],
            "C3": ["Q", "D", "L", "C", "Buck", "降圧", "インダクタ", "ダイオード"],
            "C4": ["IGBT", "Q", "三相", "3相", "VSI", "インバータ"],
        }
        keywords = component_keywords.get(circuit_id, [])
        keyword_hits = sum(1 for kw in keywords if kw.lower() in response.lower())
        struct_ok = keyword_hits >= len(keywords) // 2
        pred_comp_count = None
        parsed = None

    # --- 仕様充足性 ---
    # 仕様に含まれる数値が応答に含まれているかチェック
    spec_numbers = {
        "C1": [100, 10, 1, 500],      # R=100Ω, L=10mH, C=1μF, f≈500Hz
        "C2": [48, 10],               # VDC=48V, Rload=10Ω
        "C3": [24, 12, 100, 5],       # Vin=24V, Vout=12V, fsw=100kHz, R=5Ω
        "C4": [600, 10, 300, 173],    # VDC=600V, R=10Ω, Vline≈300V, Vphase≈173V
    }
    numbers_in_response = extract_numbers(response)
    spec_nums  = spec_numbers.get(circuit_id, [])
    spec_hits  = sum(
        1 for sn in spec_nums
        if any(abs(n - sn) / max(abs(sn), 1) < 0.15 for n in numbers_in_response)
    )
    spec_ok = spec_hits >= len(spec_nums) // 2

    # --- 数値妥当性（T2の正解に近いか） ---
    first_gt_val = list(gt_t2.values())[0]
    num_ok = any(
        abs(n - first_gt_val) / max(abs(first_gt_val), 1e-9) <= 0.15
        for n in numbers_in_response
    )

    # 重み付きスコア
    vs = 0.4 * int(spec_ok) + 0.4 * int(struct_ok) + 0.2 * int(num_ok)

    return {
        "VS": round(vs, 3),
        "spec_ok":   spec_ok,
        "struct_ok": struct_ok,
        "num_ok":    num_ok,
        "parse_ok":  parsed is not None if form == "form_c" else None,
        "pred_comp_count": pred_comp_count,
    }


# ===========================================================
# 全結果の評価
# ===========================================================

def evaluate_all(results: list[dict]) -> list[dict]:
    """実験結果リストを評価スコア付きに変換"""
    evaluated = []
    for rec in results:
        ev = dict(rec)  # コピー
        task     = rec["task"]
        circuit  = rec["circuit"]
        form     = rec["form"]
        response = rec.get("response", "")

        if rec.get("error"):
            ev["scores"] = {"error": rec["error"]}
        elif task == "T1":
            ev["scores"] = evaluate_t1(response, circuit)
        elif task == "T2":
            ev["scores"] = evaluate_t2(response, circuit)
        elif task == "T3":
            ev["scores"] = evaluate_t3(response, circuit, form)
        else:
            ev["scores"] = {}

        evaluated.append(ev)
    return evaluated


def compute_summary(evaluated: list[dict]) -> dict:
    """集計サマリーを計算"""
    from collections import defaultdict
    summary = defaultdict(lambda: defaultdict(list))

    for rec in evaluated:
        scores = rec.get("scores", {})
        key_model  = rec["model"]
        key_task   = rec["task"]
        key_circuit= rec["circuit"]
        key_form   = rec["form"]

        for metric in ["CR", "CA", "TE", "NA", "VS"]:
            val = scores.get(metric)
            if val is not None:
                summary[(key_model, key_form, key_task)][metric].append(float(val))

    result = {}
    for (model, form, task), metrics in summary.items():
        k = f"{model}|{form}|{task}"
        result[k] = {
            metric: {
                "mean": round(sum(vals)/len(vals), 4),
                "min":  round(min(vals), 4),
                "max":  round(max(vals), 4),
                "n":    len(vals),
            }
            for metric, vals in metrics.items()
        }

    return result


# ===========================================================
# CLI
# ===========================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="実験結果評価")
    parser.add_argument("result_file", help="raw結果JSONファイルのパス")
    args = parser.parse_args()

    with open(args.result_file, encoding="utf-8") as f:
        results = json.load(f)

    evaluated = evaluate_all(results)
    summary   = compute_summary(evaluated)

    # 評価済み結果を上書き保存
    eval_path = Path(args.result_file).parent.parent / f"evaluated_{Path(args.result_file).name}"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump({"records": evaluated, "summary": summary}, f, ensure_ascii=False, indent=2)

    print(f"評価完了 → {eval_path}")
    print("\n=== サマリー（一部） ===")
    for k, v in list(summary.items())[:10]:
        print(f"  {k}: {v}")
