import sys, re, pandas as pd
W = sys.argv[1]
df = pd.read_parquet(W + "/dl/pexels_meta/pexels_400k.parquet")
df["id"] = df.video.str.extract(r"/video/(\d+)").astype(int)
df["t"] = df.title.str.replace(" · Free Stock Video", "", regex=False)
for q in sys.argv[2:]:
    inc, _, exc = q.partition("!")
    m = df.t.str.contains(inc, case=False, regex=True)
    if exc:
        m &= ~df.t.str.contains(exc, case=False, regex=True)
    r = df[m & (df.duration >= 5)].sort_values("view_count", ascending=False)
    print(f"\n### {q}  ({len(r)} hits)")
    for _, x in r.head(25).iterrows():
        print(f"  {x.id:>9}  {x.duration:>4}s  {int(x.view_count):>9}  {x.t[:90]}")
