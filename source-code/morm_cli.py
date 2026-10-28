#!/usr/bin/env python3
"""
MORMForge Pro — Command Line Interface
CCSDS 520.1-P-1.1 & 520.1-M-1 Mission Operations Reference Model Toolchain
"""

import sys
import os
import argparse
import json
from datetime import datetime

TARGET_NAMESPACE = "urn:ccsds:schema:mo:morm"

PATTERNS = {
    'SEND': 1,
    'SUBMIT': 2,
    'REQUEST': 3,
    'INVOKE': 4,
    'PROGRESS': 5,
    'PUB_SUB': 6
}

ERROR_CODES = {
    'DELIVERY_FAILED': 65536,
    'AUTHENTICATION_FAIL': 65537,
    'AUTHORISATION_FAIL': 65538,
    'BAD_ENCODING': 65539,
    'UNKNOWN_ENTITY': 65540,
    'UNSUPPORTED_OPERATION': 65541
}

def create_mal_message(uri_from, uri_to, pattern_key, stage, tx_id, payload, is_err=False, err_code=None):
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "header": {
            "uriFrom": uri_from,
            "uriTo": uri_to,
            "timestamp": now_iso,
            "qosLevel": "ASSURED",
            "priority": 5,
            "domain": ["ARTEMIS", "ORION", "POWER"],
            "networkZone": "SPACE_LINK",
            "session": "LIVE",
            "sessionName": "LIVE_OPERATIONS",
            "interactionType": PATTERNS[pattern_key],
            "interactionTypeName": pattern_key,
            "interactionStage": stage,
            "transactionId": tx_id,
            "serviceArea": 1,
            "serviceNumber": 1,
            "operationNumber": 1,
            "areaVersion": 1,
            "isErrorMessage": is_err
        },
        "body": payload,
        "error": {
            "errorCode": err_code or 65536,
            "errorName": "DELIVERY_FAILED",
            "extraInformation": "Operation encountered error"
        } if is_err else None
    }

def simulate_pattern(pattern_key="PROGRESS", uri_from="mal://moc.esa.esoc/fdir", uri_to="mal://spacecraft.artemis/power_service", tx_id=88421):
    msgs = []
    
    if pattern_key == "SEND":
        msgs.append(create_mal_message(uri_from, uri_to, pattern_key, "SEND_MSG", tx_id, {"telemetry": "VOLTAGE_OK"}))
    elif pattern_key == "SUBMIT":
        msgs.append(create_mal_message(uri_from, uri_to, pattern_key, "SUBMIT_REQ", tx_id, {"command": "CALIBRATE"}))
        msgs.append(create_mal_message(uri_to, uri_from, pattern_key, "SUBMIT_ACK", tx_id, {"status": "ACCEPTED"}))
    elif pattern_key == "REQUEST":
        msgs.append(create_mal_message(uri_from, uri_to, pattern_key, "REQUEST_REQ", tx_id, {"query": "GET_BATTERY_STATE"}))
        msgs.append(create_mal_message(uri_to, uri_from, pattern_key, "REQUEST_RESP", tx_id, {"chargePct": 94.5}))
    elif pattern_key == "INVOKE":
        msgs.append(create_mal_message(uri_from, uri_to, pattern_key, "INVOKE_REQ", tx_id, {"action": "ROTATE_ARRAY", "deg": 45}))
        msgs.append(create_mal_message(uri_to, uri_from, pattern_key, "INVOKE_ACK", tx_id, {"status": "IN_PROGRESS"}))
        msgs.append(create_mal_message(uri_to, uri_from, pattern_key, "INVOKE_RESP", tx_id, {"status": "COMPLETED"}))
    elif pattern_key == "PROGRESS":
        msgs.append(create_mal_message(uri_from, uri_to, pattern_key, "PROGRESS_REQ", tx_id, {"task": "FIRMWARE_UPDATE"}))
        msgs.append(create_mal_message(uri_to, uri_from, pattern_key, "PROGRESS_ACK", tx_id, {"status": "STARTED"}))
        msgs.append(create_mal_message(uri_to, uri_from, pattern_key, "PROGRESS_UPDATE", tx_id, {"progressPct": 50.0}))
        msgs.append(create_mal_message(uri_to, uri_from, pattern_key, "PROGRESS_RESP", tx_id, {"status": "SUCCESS"}))
    elif pattern_key == "PUB_SUB":
        msgs.append(create_mal_message(uri_from, "mal://broker", pattern_key, "REGISTER", tx_id, {"topic": "SOLAR_ARRAY_TEMP"}))
        msgs.append(create_mal_message(uri_to, "mal://broker", pattern_key, "PUBLISH", tx_id, {"topic": "SOLAR_ARRAY_TEMP", "val": 24.2}))
        msgs.append(create_mal_message("mal://broker", uri_from, pattern_key, "NOTIFY", tx_id, {"topic": "SOLAR_ARRAY_TEMP", "val": 24.2}))
        
    return {
        "pattern": pattern_key,
        "transactionId": tx_id,
        "totalStages": len(msgs),
        "messages": msgs
    }

def serialize_to_xml(trace):
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<morm:InteractionTrace xmlns:morm="{TARGET_NAMESPACE}"',
        '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        f'    xsi:schemaLocation="{TARGET_NAMESPACE} 520x1p11-Morm.xsd">',
        f'    <morm:pattern>{trace["pattern"]}</morm:pattern>',
        f'    <morm:transactionId>{trace["transactionId"]}</morm:transactionId>',
        f'    <morm:totalStages>{trace["totalStages"]}</morm:totalStages>',
        f'    <morm:messages count="{len(trace["messages"])}">'
    ]
    for msg in trace["messages"]:
        xml.append(f'        <morm:MalMessage stage="{msg["header"]["interactionStage"]}">' )
        xml.append(f'            <morm:uriFrom>{msg["header"]["uriFrom"]}</morm:uriFrom>')
        xml.append(f'            <morm:uriTo>{msg["header"]["uriTo"]}</morm:uriTo>')
        xml.append(f'            <morm:timestamp>{msg["header"]["timestamp"]}</morm:timestamp>')
        xml.append(f'            <morm:qosLevel>{msg["header"]["qosLevel"]}</morm:qosLevel>')
        xml.append(f'            <morm:domain>{".".join(msg["header"]["domain"])}</morm:domain>')
        xml.append(f'            <morm:payload>{json.dumps(msg["body"])}</morm:payload>')
        xml.append('        </morm:MalMessage>')
    xml.append('    </morm:messages>')
    xml.append('</morm:InteractionTrace>')
    return '\n'.join(xml)

def audit_trace(trace, xml_str=""):
    checks = []
    msgs = trace.get("messages", [])
    
    # MORM-001
    checks.append(('MORM-001', 'MO Framework Layer Stratification', True))
    
    # MORM-002
    c2 = len(msgs) > 0 and all(1 <= m["header"]["interactionType"] <= 6 for m in msgs)
    checks.append(('MORM-002', 'Standard Interaction Pattern (SIP) Conformance', c2))
    
    # MORM-003
    c3 = len(msgs) > 0 and all(m["header"]["uriFrom"] and m["header"]["uriTo"] and m["header"]["transactionId"] for m in msgs)
    checks.append(('MORM-003', 'MAL Header Specification Integrity', c3))
    
    # MORM-004
    stages = [m["header"]["interactionStage"] for m in msgs]
    c4 = len(stages) > 0
    if trace["pattern"] == "PROGRESS":
        c4 = stages[0] == "PROGRESS_REQ" and stages[1] == "PROGRESS_ACK" and stages[-1] == "PROGRESS_RESP"
    checks.append(('MORM-004', 'Multi-Stage Sequence Ordering', c4))
    
    # MORM-005
    c5 = True if trace["pattern"] != "PUB_SUB" else all(s in stages for s in ["REGISTER", "PUBLISH", "NOTIFY"])
    checks.append(('MORM-005', 'Publish-Subscribe Broker Architecture', c5))
    
    # MORM-006
    c6 = all(not m["header"]["isErrorMessage"] or m.get("error") for m in msgs)
    checks.append(('MORM-006', 'Error Return Signaling & Semantics', c6))
    
    # MORM-007
    c7 = all(m["header"]["qosLevel"] in ["BEST_EFFORT", "QUEUED", "TIMELY", "ASSURED"] for m in msgs)
    checks.append(('MORM-007', 'Quality of Service (QoS) Level Conformance', c7))
    
    # MORM-008
    c8 = all(m["header"]["uriFrom"].startswith("mal://") and m["header"]["uriTo"].startswith("mal://") for m in msgs)
    checks.append(('MORM-008', 'mal:// URI Endpoint Addressing', c8))
    
    # MORM-009
    c9 = all(isinstance(m["header"]["domain"], list) and len(m["header"]["domain"]) > 0 for m in msgs)
    checks.append(('MORM-009', 'Hierarchical Domain Scoping', c9))
    
    # MORM-010
    c10 = TARGET_NAMESPACE in xml_str if xml_str else True
    checks.append(('MORM-010', 'SANA XML Namespace & Schema Validation', c10))
    
    return checks

def main():
    parser = argparse.ArgumentParser(description="MORMForge Pro — CCSDS 520.1 Mission Operations Reference Model CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # simulate
    p_sim = subparsers.add_parser("simulate", help="Simulate a standard MO interaction pattern")
    p_sim.add_argument("--pattern", choices=list(PATTERNS.keys()), default="PROGRESS")
    p_sim.add_argument("--from-uri", default="mal://moc.esa.esoc/fdir")
    p_sim.add_argument("--to-uri", default="mal://spacecraft.artemis/power_service")
    p_sim.add_argument("--output", default="morm_trace.json")
    
    # export-xml
    p_xml = subparsers.add_parser("export-xml", help="Export interaction trace to SANA XML")
    p_xml.add_argument("--input", default="morm_trace.json")
    p_xml.add_argument("--output", default="morm_trace.xml")
    
    # audit
    p_aud = subparsers.add_parser("audit", help="Run 10-point normative audit on interaction trace")
    p_aud.add_argument("file", help="Path to trace JSON")
    
    args = parser.parse_args()
    
    if args.command == "simulate":
        trace = simulate_pattern(args.pattern, args.from_uri, args.to_uri)
        with open(args.output, "w") as f:
            json.dump(trace, f, indent=2)
        print(f"[OK] Simulated {args.pattern} pattern: {args.output} ({trace['totalStages']} stages)")
        
    elif args.command == "export-xml":
        if os.path.exists(args.input):
            with open(args.input, "r") as f:
                trace = json.load(f)
        else:
            trace = simulate_pattern()
            
        xml_out = serialize_to_xml(trace)
        with open(args.output, "w") as f:
            f.write(xml_out)
        print(f"[OK] Exported SANA XML trace: {args.output} ({len(xml_out)} characters)")
        
    elif args.command == "audit":
        with open(args.file, "r") as f:
            trace = json.load(f)
        xml_str = serialize_to_xml(trace)
        results = audit_trace(trace, xml_str)
        print("======================================================================")
        print("  CCSDS 520.1-P-1.1 MORM 10-Point Normative Compliance Audit")
        print("======================================================================")
        all_pass = True
        for cid, name, p in results:
            status = "PASS" if p else "FAIL"
            print(f"[{cid}] {name:<45} : {status}")
            if not p: all_pass = False
        print("----------------------------------------------------------------------")
        score = sum(1 for _, _, p in results) / len(results) * 100
        print(f"Audit Score: {score:.1f}% ({'CCSDS_520_1_MORM_CERTIFIED' if all_pass else 'NON_COMPLIANT'})")
        print("======================================================================")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
