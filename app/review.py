"""Diagnostic locations are listening hints, expressed on the exported audio timeline."""
import math


def listening_regions(stats, duration, padding=0, reference_times=(), source_offset=0):
    regions = []
    def add(start, end, kind):
        if not math.isfinite(start) or not math.isfinite(end):
            return
        start, end = max(0, start), min(duration, end)
        if end <= start:
            return
        regions.append({"start":round(start, 3), "end":round(end, 3), "kind":kind,
                        "source_start":round(source_offset+start, 3), "source_end":round(source_offset+end, 3)})
    for phrase in (stats or {}).get("phrases_exceeding_range", []):
        add(float(phrase["start_seconds"])-padding, float(phrase["end_seconds"])-padding, "range")
    groups = []
    for value in sorted(reference_times):
        if not groups or value-groups[-1][-1] > .25:
            groups.append([value])
        else:
            groups[-1].append(value)
    for group in groups:
        add(float(group[0]), float(group[-1])+.01, "pitch")
    # Overlapping phrases of the same kind can arise at padded edges.
    merged = []
    for item in sorted(regions, key=lambda r:(r["kind"],r["start"])):
        if merged and item["kind"]==merged[-1]["kind"] and item["start"]<=merged[-1]["end"]+.1:
            merged[-1]["end"]=max(item["end"],merged[-1]["end"])
            merged[-1]["source_end"]=source_offset+merged[-1]["end"]
        else:
            merged.append(item)
    return sorted(merged, key=lambda r:r["start"])
