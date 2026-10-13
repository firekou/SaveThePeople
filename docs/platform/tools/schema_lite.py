#!/usr/bin/env python3
"""極簡 JSON Schema 子集驗證器（只使用標準函式庫）。

支援：type（含陣列）、enum、const、required、properties、additionalProperties（bool 或 schema）、items、
minItems、minLength、pattern、minimum、oneOf、本檔內 $ref（"#/definitions/名稱"）。其餘關鍵字一律**拒絕**（不默默忽略）。

範圍聲明（重要）：這個驗證器與 `schemas/*.schema.json` 只檢查**結構、型別、必要欄位、列舉值與未知鍵**。
跨欄位與語意規則（例如 `effective_unknown` 與 `effective_to` 必須一致、口徑範圍鍵是否被引擎支援、
CUSTOM 運算式需引用每個條件一次）不是這個驗證器的能力，由 `examples/ref_engine.py` 的驗證處理，
並由 `check_examples.py` 與 `tools/test_checks.py` 的反例測試。頂層欄位名稱檢查不等於完整 schema 驗證。
"""
import json
import re
from pathlib import Path

KNOWN = {"$schema", "$id", "title", "description", "type", "enum", "const", "required", "properties", "additionalProperties",
         "items", "minItems", "minLength", "pattern", "minimum", "oneOf", "$ref", "definitions", "x-note"}
TYPES = {"string": str, "boolean": bool, "object": dict, "array": list, "null": type(None)}


def _type_ok(v, t):
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    return isinstance(v, TYPES[t]) and not (t != "boolean" and isinstance(v, bool) and t in ("string", "object", "array", "null"))


def _resolve(ref, root):
    if not ref.startswith("#/definitions/"):
        raise ValueError(f"unsupported $ref {ref}")
    return root["definitions"][ref.split("/")[-1]]


def validate(value, schema, root=None, path="$"):
    """回傳錯誤字串清單（空清單＝通過）。"""
    root = root if root is not None else schema
    errs = []
    for k in schema:
        if k not in KNOWN:
            raise ValueError(f"schema keyword {k!r} is not supported by schema_lite (refusing to ignore it)")
    if "$ref" in schema:
        return validate(value, _resolve(schema["$ref"], root), root, path)
    if "oneOf" in schema:
        n = sum(1 for s in schema["oneOf"] if not validate(value, s, root, path))
        if n != 1:
            errs.append(f"{path}: must match exactly one of oneOf (matched {n})")
        return errs
    if "type" in schema:
        ts = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(value, t) for t in ts):
            return [f"{path}: expected type {ts}, got {type(value).__name__}"]
    if "const" in schema and value != schema["const"]:
        errs.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and (not isinstance(value, (str, int, float, bool, type(None))) or value not in schema["enum"]):
        errs.append(f"{path}: {value!r} not in enum {schema['enum']}")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errs.append(f"{path}: shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errs.append(f"{path}: does not match {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
        errs.append(f"{path}: below minimum {schema['minimum']}")
    if isinstance(value, dict):
        for r in schema.get("required", []):
            if r not in value:
                errs.append(f"{path}: missing required {r!r}")
        props = schema.get("properties", {})
        ap = schema.get("additionalProperties", True)
        for k, v in value.items():
            if k in props:
                errs += validate(v, props[k], root, f"{path}.{k}")
            elif ap is False:
                errs.append(f"{path}: unknown key {k!r}")
            elif isinstance(ap, dict):
                errs += validate(v, ap, root, f"{path}.{k}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errs.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for i, v in enumerate(value):
                errs += validate(v, schema["items"], root, f"{path}[{i}]")
    return errs


def load_schema(name):
    p = Path(__file__).resolve().parents[1] / "schemas" / f"{name}.schema.json"
    return json.loads(p.read_text(encoding="utf-8"))
