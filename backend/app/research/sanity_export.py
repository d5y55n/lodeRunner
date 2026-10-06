"""Inspectable Phase 2.5 artifacts with decision features and future labels separated."""
from collections import Counter
from dataclasses import asdict
from itertools import product
import csv
import json
from pathlib import Path
from .detectors import make_detector
from .models import identity, canonical, validate_candles
from .zones import construct
from .interactions import track, ExitRule
from .outcomes import measure
from .volume import aggregate, VolumeConcentration, zone_features, TradeIndex


def compact_bin(b):
    value = asdict(b) if not isinstance(b,dict) else dict(b)
    ids = value.pop("trade_ids")
    value.update(trade_count=len(ids),trade_ids_sha256=identity(ids))
    return value


def select_sample(candidates, interactions):
    """Earliest per detector/kind, then earliest repeated/overlapping zones. No labels."""
    ordered = sorted(candidates,key=lambda c:(c["known_at"],c["id"]))
    groups = {}
    selected = set()
    reasons = {}
    def add(c,reason):
        selected.add(c["zone_id"])
        reasons.setdefault(c["zone_id"],[]).append(reason)
    for c in ordered:
        key = (c["configuration_id"],c["kind"])
        group = groups.setdefault(key,[])
        if len(group) < (6 if c["detector"] == "D" else 3):
            group.append(c)
            add(c,"earliest_by_configuration_and_kind")
    counts = Counter(v["zone_id"] for v in interactions)
    repeated = Counter()
    for c in ordered:
        if counts[c["zone_id"]] >= 2 and repeated[c["detector"]] < 2:
            add(c,"earliest_repeated_visit_zone_retrospective")
            repeated[c["detector"]] += 1
    overlaps = []
    for i,a in enumerate(ordered):
        for b in ordered[i+1:]:
            if a["detector"] != b["detector"] and max(a["zone_lower"],b["zone_lower"]) <= min(a["zone_upper"],b["zone_upper"]):
                overlaps.append((a,b))
    for a,b in overlaps[:3]:
        add(a,"earliest_cross_detector_overlap")
        add(b,"earliest_cross_detector_overlap")
    return {"zone_ids":sorted(selected),"reasons":reasons,
            "rule":"First 3 per configuration/kind (D:6), first 2 repeated zones per detector, first 3 cross-detector overlapping pairs, all ordered by known_at then candidate id; no outcome inputs.",
            "retrospective_selection":True,
            "overlap_pairs_total":len(overlaps),
            "selected_counts":dict(Counter(c["detector"]+":"+c["kind"] for c in ordered if c["zone_id"] in selected))}


def build_exports(candles,trades,plan):
    validate_candles(candles)
    start,end = plan["start"],plan["end"]
    if end > plan["original_research_end"]:
        raise ValueError("Sanity window must stay within original research period")
    if not candles or candles[0].start != start or candles[-1].end != end:
        raise ValueError("Sanity candles do not cover exact requested window")
    if any(not start <= t.timestamp < end for t in trades):
        raise ValueError("Trade data outside sanity window")
    trades = trades if isinstance(trades,TradeIndex) else TradeIndex(trades)
    candidates,decisions,visits,outcomes,vap = [],[],[],[],[]
    window = plan["volume_window_ms"]
    for width in plan["bin_sizes"]:
        for t in range(start,end-window+1,window):
            for b in aggregate(trades,width,t,t+window,t+window):
                vap.append({"bin_size":width,"anchor":0,"interval":"[lower,upper)",**compact_bin(b)})
    for config in plan["detectors"]:
        name = config["detector"]
        parameters = config["parameters"]
        config_id = identity(config)
        detector = (VolumeConcentration(trades,start=start,**parameters) if name == "D" else
                    make_detector(name,parameters))
        found = detector.detect(candles,plan["timeframe"],end)
        for event in found:
            z = construct(event,"fixed_percentage",plan["zone_half_width"])
            metadata = dict(event.metadata)
            if "bin" in metadata:
                metadata["bin"] = compact_bin(metadata["bin"])
            record = {**asdict(event),"metadata":metadata,"id":event.id,"zone_id":z.id,
                      "configuration_id":config_id,"zone_lower":z.lower,"zone_upper":z.upper,
                      "width_model":z.width_model,"width_parameter":z.width_parameter,
                      "volume_at_known":zone_features(z,trades,event.known_at,window,start,end)}
            candidates.append(record)
            interactions = track(z,candles,ExitRule(**plan["exit_rule"]))
            for v in interactions:
                key = identity([config_id,z.id,v.number,v.observed_at])
                feature = {"event_id":key,"configuration_id":config_id,"zone_id":z.id,
                           "detector":name,"kind":event.kind,"source_time":event.source_timestamp,
                           "known_at":event.known_at,"reference_price":event.price,
                           "zone_lower":z.lower,"zone_upper":z.upper,
                           "interaction_number":v.number,"interaction_start":v.start,
                           "decision_time":v.observed_at,"entry_reference_close":v.entry_price,
                           "approach":v.approach,
                           "volume":zone_features(z,trades,v.observed_at,window,start,end)}
                decisions.append(feature)
                visits.append({"event_id":key,"detector":name,"retrospective":True,**asdict(v)})
                for direction,tp,sl,horizon in product(("LONG","SHORT"),plan["tp_grid"],plan["sl_grid"],plan["horizons"]):
                    outcomes.append({"event_id":key,"decision_time":v.observed_at,"future_only":True,
                                     **asdict(measure(v.entry_price,v.observed_at,candles,direction,tp,sl,horizon))})
    sample = select_sample(candidates,visits)
    summary = {"candidate_counts":dict(sorted(Counter(c["detector"]+":"+c["kind"] for c in candidates).items())),
               "D_by_bin_size":dict(sorted(Counter(str(c["metadata"]["bin_size"]) for c in candidates if c["detector"]=="D").items())),
               "volume_attachment_status":dict(sorted(Counter(d["detector"]+":"+d["volume"]["status"] for d in decisions).items())),
               "candidate_volume_status":dict(sorted(Counter(c["detector"]+":"+c["volume_at_known"]["status"] for c in candidates).items())),
               "zero_baseline_ratios":sum(d["volume"].get("status")=="AVAILABLE" and d["volume"].get("relative_zone_volume") is None for d in decisions),
               "interactions":len(visits),"repeated_zones":sum(n>=2 for n in Counter(v["zone_id"] for v in visits).values()),
               "vap_bins":len(vap),"outcome_rows":len(outcomes),"final_test_used":False,
               "outcome_labels":dict(sorted(Counter(str(o["label"]) for o in outcomes).items()))}
    return {"plan":plan,"candles":[asdict(c) for c in candles],"candidates":candidates,
            "decision_features":decisions,"interactions_retrospective":visits,
            "outcomes_future":outcomes,"volume_at_price":vap,"sample":sample,"summary":summary}


def flat(row,prefix=""):
    result = {}
    for key,value in row.items():
        name = prefix+key
        if isinstance(value,dict):
            result.update(flat(value,name+"."))
        elif isinstance(value,(list,tuple)):
            result[name] = canonical(value)
        else:
            result[name] = value
    return result


def write_exports(bundle,destination):
    root = Path(destination)
    root.mkdir(parents=True,exist_ok=True)
    generated = []
    for name,value in bundle.items():
        (root/(name+".json")).write_text(canonical(value)+"\n",encoding="utf-8")
        generated.append(root/(name+".json"))
        if isinstance(value,list) and value:
            records = [flat(row) for row in value]
            columns = sorted({key for row in records for key in row})
            with (root/(name+".csv")).open("w",encoding="utf-8",newline="") as stream:
                writer = csv.DictWriter(stream,fieldnames=columns,lineterminator="\n")
                writer.writeheader()
                writer.writerows(records)
            generated.append(root/(name+".csv"))
    # Future outcomes and completed-visit facts are deliberately not embedded in HTML.
    display = {key:bundle[key] for key in ("plan","candles","candidates","decision_features","sample")}
    template = Path(__file__).with_name("sanity_template.html").read_text(encoding="utf-8")
    html = template.replace("__RESEARCH_DATA__",canonical(display).replace("<","\\u003c"))
    (root/"sanity.html").write_text(html,encoding="utf-8")
    generated.append(root/"sanity.html")
    files = sorted(generated)
    import hashlib
    hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (root/"export-manifest.json").write_text(canonical(hashes)+"\n",encoding="utf-8")
    return hashes
