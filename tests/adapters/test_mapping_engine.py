# -*- coding: utf-8 -*-
from domains.adapters.mapping import MappingEngine

def test_map_01_known_alias_high_confidence():
    columns = ["매출일자", "영수증번호", "실매출액", "메뉴명", "수량"]
    suggestions = MappingEngine.suggest_mapping("POS", columns)
    assert len(suggestions) == 5
    for s in suggestions:
        assert s.confidence == "HIGH"
        assert s.suggested_canonical_field is not None

def test_map_02_ambiguous_column():
    columns = ["일자", "금액"]
    suggestions = MappingEngine.suggest_mapping("POS", columns)
    assert len(suggestions) == 2
    for s in suggestions:
        assert s.suggested_canonical_field is not None

def test_map_03_unknown_column():
    columns = ["알수없는기타컬럼XYZ", "임의필드123"]
    suggestions = MappingEngine.suggest_mapping("POS", columns)
    for s in suggestions:
        assert s.confidence == "UNMAPPED"
        assert s.suggested_canonical_field is None

def test_map_04_manifest_repeatability():
    columns = ["매출일자", "영수증번호", "메뉴코드"]
    suggestions = MappingEngine.suggest_mapping("POS", columns)
    manifest1 = MappingEngine.build_manifest("M1", "POS", suggestions, version="1.0.0")
    manifest2 = MappingEngine.build_manifest("M1", "POS", suggestions, version="1.0.0")
    assert manifest1.column_mappings == manifest2.column_mappings

def test_map_05_mapping_version_lineage():
    columns = ["매출일자", "영수증번호"]
    suggestions = MappingEngine.suggest_mapping("POS", columns)
    v1 = MappingEngine.build_manifest("M1", "POS", suggestions, version="1.0.0")
    v2 = MappingEngine.build_manifest("M1", "POS", suggestions, version="1.1.0")
    assert v1.mapping_version == "1.0.0"
    assert v2.mapping_version == "1.1.0"

