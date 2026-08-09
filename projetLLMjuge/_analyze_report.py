import json
from collections import defaultdict

d = json.load(open("rapport_comparaison_2026-08-02.json", encoding="utf-8"))
by_strat = defaultdict(lambda: {"c_f1": [], "g_f1": [], "c_r": [], "g_r": []})
for it in d["per_item"]:
    s = it["stratum_code"]
    by_strat[s]["c_f1"].append(it["current_pipeline"]["f1"])
    by_strat[s]["g_f1"].append(it["global_judge"]["f1"])
    by_strat[s]["c_r"].append(it["current_pipeline"]["recall"])
    by_strat[s]["g_r"].append(it["global_judge"]["recall"])

print(f"{'STRATE':<22} {'actuel F1':>10} {'global F1':>10} {'delta':>8}   {'actuel R':>9} {'global R':>9}")
for strat, v in by_strat.items():
    c = sum(v["c_f1"]) / len(v["c_f1"])
    g = sum(v["g_f1"]) / len(v["g_f1"])
    cr = sum(v["c_r"]) / len(v["c_r"])
    gr = sum(v["g_r"]) / len(v["g_r"])
    print(f"{strat:<22} {c:>10.2f} {g:>10.2f} {g-c:>+8.2f}   {cr:>9.2f} {gr:>9.2f}")
