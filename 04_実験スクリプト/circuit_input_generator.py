"""
回路定義JSON → 3形式（ASCII/自然言語/構造体JSON）変換モジュール
"""

import json
import textwrap
from pathlib import Path


# ===========================================================
# Form-A: アスキーアート形式
# ===========================================================

ASCII_TEMPLATES = {
    "C1": textwrap.dedent("""\
        直列RLC回路のアスキーアート表現:

             N1      N2      N3
        N0 ──┤V1├──┬──┤R1├──┬──┤L1├──┬──┤C1├──┐
                   │         │         │         │
                   │         │         │         │
        GND ───────┴─────────┴─────────┴─────────┘

        凡例:
          V1  : 電圧源（10V直流）
          R1  : 抵抗（100Ω）
          L1  : インダクタ（10mH）
          C1  : キャパシタ（1μF）
          N0  : 正極ノード
          GND : グランドノード
    """),

    "C2": textwrap.dedent("""\
        H-bridgeインバータのアスキーアート表現:

         VDC+────────────────────────────────────────┐
              │                                      │
             [Q1]  upper-left                      [Q3]  upper-right
              │                                      │
         MidLeft────────[Rload]────────────MidRight
              │                                      │
             [Q2]  lower-left                      [Q4]  lower-right
              │                                      │
         VDC-────────────────────────────────────────┘

        凡例:
          VDC : DC電源（48V）
          Q1-Q4 : MOSFETスイッチ
          Rload : 負荷抵抗（10Ω）
          [Q1,Q4] : ペア動作（0° phase）
          [Q2,Q3] : ペア動作（180° phase）
    """),

    "C3": textwrap.dedent("""\
        Buckコンバータのアスキーアート表現:

        N_in ──┬──[Q1]──N_sw──┬──[L1]──N_out──┬──[Rload]──┐
               │       SW      │                │            │
              [Vin]          [D1]             [C1]          │
               │               │                │            │
        GND ───┴───────────────┴────────────────┴────────────┘

        凡例:
          Vin   : 入力電圧源（24V）
          Q1    : MOSFETスイッチ（デューティ比 D=0.5, fsw=100kHz）
          D1    : フリーホイールダイオード
          L1    : インダクタ（100μH）
          C1    : 出力コンデンサ（100μF）
          Rload : 負荷抵抗（5Ω）
    """),

    "C4": textwrap.dedent("""\
        3相VSIインバータのアスキーアート表現:

        DC+──┬─────────────────────────────────────────────┐
             │         │                 │                   │
           [CDC]      [Q1]upper-A      [Q3]upper-B        [Q5]upper-C
             │         │                 │                   │
        DC-──┤        PhA               PhB                PhC
             │         │                 │                   │
             │        [Q2]lower-A      [Q4]lower-B        [Q6]lower-C
             │         │                 │                   │
             └────────────────────────────────────────────────
                        │                 │                   │
                     [Rload_A]         [Rload_B]          [Rload_C]
                        │                 │                   │
                     NeutralLoad────────────────────────────

        凡例:
          VDC : DC母線電圧（600V）
          CDC : DCリンクコンデンサ（1000μF）
          Q1-Q6 : IGBT（各相上下アーム）
          Rload_A/B/C : 星形三相負荷（各10Ω）
          変調方式 : SVPWM
    """),
}


# ===========================================================
# Form-B: 自然言語記述形式
# ===========================================================

NATURAL_LANG_TEMPLATES = {
    "C1": textwrap.dedent("""\
        【直列RLC回路の自然言語記述】

        この回路は電圧源・抵抗・インダクタ・キャパシタの4素子を直列に接続した基本的なフィルタ回路です。

        構成要素:
        - 電圧源 V1（10V、直流）: 回路に電力を供給する
        - 抵抗 R1（100Ω）: エネルギーを消費し、Q値を決定する
        - インダクタ L1（10ミリヘンリ）: 磁気エネルギーを蓄積し、電流変化に抵抗する
        - キャパシタ C1（1マイクロファラド）: 電気エネルギーを蓄積し、電圧変化に抵抗する

        接続関係:
        V1の正極をノードN1に接続する。
        N1からR1を経てノードN2に接続する。
        N2からL1を経てノードN3に接続する。
        N3からC1を経てグランドノードN0に戻る。
        V1の負極もグランドN0に接続される。

        回路の動作特性:
        この回路は約503Hzの共振周波数を持ち、その周波数でインピーダンスが最小（= R1 = 100Ω）になる。
        Q値（Quality Factor）は約0.316で、やや過減衰気味の特性を示す。
    """),

    "C2": textwrap.dedent("""\
        【H-bridgeインバータの自然言語記述】

        この回路は4つのMOSFETスイッチと1つのDC電源、1つの負荷抵抗で構成される全橋（フルブリッジ）インバータです。

        構成要素:
        - DC電源 VDC（48V）: 直流電力を供給するバスライン
        - MOSFETスイッチ Q1（左上アーム）: 上側左アーム
        - MOSFETスイッチ Q2（左下アーム）: 下側左アーム
        - MOSFETスイッチ Q3（右上アーム）: 上側右アーム
        - MOSFETスイッチ Q4（右下アーム）: 下側右アーム
        - 負荷抵抗 Rload（10Ω）: 橋の中央に接続される出力負荷

        接続関係:
        DC正母線（VDC+）から左上アーム Q1 のドレインと、右上アーム Q3 のドレインに接続される。
        Q1のソースが左中間点（MidLeft）に接続される。
        Q3のソースが右中間点（MidRight）に接続される。
        左中間点（MidLeft）から Q2 のドレインが接続され、Q2のソースがDC負極（VDC−）に接続される。
        右中間点（MidRight）から Q4 のドレインが接続され、Q4のソースがDC負極（VDC−）に接続される。
        負荷抵抗 Rload は MidLeft と MidRight の間に接続される。

        スイッチング動作:
        Q1とQ4を同時にON（0°フェーズペア）し、Q2とQ3を同時にON（180°フェーズペア）することで、
        負荷に48Vと−48Vを交互に印加し、交流出力を生成する。
    """),

    "C3": textwrap.dedent("""\
        【Buckコンバータの自然言語記述】

        この回路は入力電圧を降圧するDC-DC変換器で、スイッチ・ダイオード・インダクタ・キャパシタで構成されます。

        構成要素:
        - 入力電源 Vin（24V）: 降圧前のDC入力
        - MOSFETスイッチ Q1: メインスイッチ（100kHzでPWM動作、デューティ比50%）
        - フリーホイールダイオード D1: スイッチOFF時に電流を連続させる環流ダイオード
        - インダクタ L1（100マイクロヘンリ）: 出力電流の平滑化と電力転送
        - 出力コンデンサ C1（100マイクロファラド）: 出力電圧のリプル低減
        - 負荷抵抗 Rload（5Ω）: 出力負荷

        接続関係:
        Vinの正極がノードN_inに接続される。
        N_inからQ1のドレインに接続し、Q1のソースからスイッチングノードN_swに接続される。
        N_swからD1のカソードに接続し、D1のアノードはグランド（GND）に接続される。
        N_swからL1の一端に接続し、L1の他端が出力ノードN_outに接続される。
        N_outからC1の正極に接続し、C1の負極はGNDに接続される。
        N_outからRloadの一端に接続し、他端はGNDに接続される。
        VinのマイナスもGNDに接続される。

        回路の動作:
        デューティ比50%で動作時、出力電圧 = 24V × 0.5 = 12V が得られる。
        インダクタ電流リプルは約0.6A、出力電圧リプルは約45mVとなる。
    """),

    "C4": textwrap.dedent("""\
        【3相電圧形インバータ（VSI）の自然言語記述】

        この回路はDC母線から3相交流を生成するインバータで、6つのIGBTと3相スター結線負荷で構成されます。

        構成要素:
        - DC電源 VDC（600V）: 直流母線電圧
        - DCリンクコンデンサ CDC（1000マイクロファラド）: 母線電圧を安定化
        - IGBT Q1（A相上アーム）、Q2（A相下アーム）: A相ブリッジアーム
        - IGBT Q3（B相上アーム）、Q4（B相下アーム）: B相ブリッジアーム
        - IGBT Q5（C相上アーム）、Q6（C相下アーム）: C相ブリッジアーム
        - 負荷抵抗 Rload_A、Rload_B、Rload_C（各10Ω）: スター結線三相負荷

        接続関係:
        DC正母線（DC+）はCDCの正極、Q1・Q3・Q5の各コレクタに接続される。
        DC負母線（DC−）はCDCの負極、Q2・Q4・Q6の各エミッタに接続される。
        Q1のエミッタとQ2のコレクタが中間点PhAに接続される（A相出力点）。
        Q3のエミッタとQ4のコレクタが中間点PhBに接続される（B相出力点）。
        Q5のエミッタとQ6のコレクタが中間点PhCに接続される（C相出力点）。
        PhAからRload_Aを経て中性点に、PhBからRload_Bを経て中性点に、PhCからRload_Cを経て中性点に接続される。

        動作特性:
        SVPWM変調時、DC母線600Vから線間電圧実効値300V（相電圧実効値173V）の三相交流を生成する。
        変調指数は0.816で、DC母線利用率を最大化する。
    """),
}


# ===========================================================
# Form-C: 構造体JSON形式（実験で使うのはこのJSON文字列）
# ===========================================================

def generate_structured_json(circuit_path: Path) -> str:
    """回路定義JSONをそのまま構造体JSON形式として整形返却"""
    with open(circuit_path) as f:
        data = json.load(f)
    # ground_truthは除いて入力として使う
    input_data = {k: v for k, v in data.items() if k != "ground_truth"}
    return json.dumps(input_data, ensure_ascii=False, indent=2)


def get_all_inputs(circuit_id: str, circuit_dir: Path) -> dict:
    """3形式すべての入力を返す"""
    circuit_files = list(circuit_dir.glob(f"{circuit_id}_*.json"))
    if not circuit_files:
        raise FileNotFoundError(f"Circuit {circuit_id} not found in {circuit_dir}")
    circuit_path = circuit_files[0]

    return {
        "form_a": ASCII_TEMPLATES[circuit_id],
        "form_b": NATURAL_LANG_TEMPLATES[circuit_id],
        "form_c": generate_structured_json(circuit_path),
    }


def get_ground_truth(circuit_id: str, circuit_dir: Path) -> dict:
    """正解データを返す"""
    circuit_files = list(circuit_dir.glob(f"{circuit_id}_*.json"))
    with open(circuit_files[0]) as f:
        data = json.load(f)
    return data.get("ground_truth", {})


if __name__ == "__main__":
    circuit_dir = Path(__file__).parent.parent / "02_回路定義"
    for cid in ["C1", "C2", "C3", "C4"]:
        inputs = get_all_inputs(cid, circuit_dir)
        print(f"\n{'='*60}")
        print(f"Circuit: {cid}")
        print(f"--- Form-A (ASCII) ---")
        print(inputs["form_a"][:200], "...")
        print(f"--- Form-B (Natural) ---")
        print(inputs["form_b"][:200], "...")
        print(f"--- Form-C (JSON) ---")
        print(inputs["form_c"][:200], "...")
