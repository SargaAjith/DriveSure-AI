import os, sys
sys.path.insert(0, ".")
import predict_segmentation as e

sample = "0020.jpg"
print(f"Testing on: {sample}")

res = e.predict(sample)
print(f"Severity   : {res['severity']}")
print(f"Damage pct : {res['damage_pct']}%")
print(f"Cost       : {res['cost_range_inr']}")
print(f"Polygons   : {res['polygon_count']}")
print(f"Source     : {res['source']}")
print(f"Observation: {res['what_i_see']}")
