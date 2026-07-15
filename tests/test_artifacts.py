import pytest

from pvfactory.artifacts import LocalArtifactStore, is_ref, ref_name


def test_roundtrip_and_refs(tmp_path):
    store = LocalArtifactStore(tmp_path)
    ref = store.put_json("a/b.json", {"x": 1})
    assert is_ref(ref) and ref_name(ref) == "a/b.json"
    assert store.get_json(ref) == {"x": 1}
    assert store.exists(ref)
    assert len(store.sha256(ref)) == 64
    assert store.path_for(ref).is_file()


def test_name_escape_rejected(tmp_path):
    store = LocalArtifactStore(tmp_path)
    with pytest.raises(ValueError):
        store.put_bytes("../evil.txt", b"nope")
