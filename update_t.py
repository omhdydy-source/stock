import json
import os

state_file = "C:/Users/omh/Desktop/stock/infinite_v4_state.json"

def update_t_values(soxl_t, tqqq_t):
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    if "SOXL" not in data:
        data["SOXL"] = {"cycle": 1, "T": 0.0, "total_tranches": 40}
    if "TQQQ" not in data:
        data["TQQQ"] = {"cycle": 1, "T": 0.0, "total_tranches": 40}

    data["SOXL"]["T"] = float(soxl_t)
    data["TQQQ"]["T"] = float(tqqq_t)

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ T값 수동 업데이트 완료: SOXL T={soxl_t}, TQQQ T={tqqq_t}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        update_t_values(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python update_t.py <SOXL_T> <TQQQ_T>")
