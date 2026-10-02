"""Meaningful checks on native place geometry and structural export integrity."""
import json, math, pathlib, xml.etree.ElementTree as ET
from collections import Counter
root=pathlib.Path(__file__).resolve().parents[1]
scene=json.loads((root/'viewer/scene.json').read_text())
tree=ET.parse(root/'build/RavenRidge.rbxlx')
items=tree.findall('.//Item'); refs=[i.attrib['referent'] for i in items]
assert len(refs)==len(set(refs)), 'Duplicate native referents'
native=[i for i in items if i.attrib['class'] in ('Part','WedgePart','CornerWedgePart','SpawnLocation')]
assert len(native)==len(scene['parts']), 'Viewer/native geometry count mismatch'
for p,item in zip(scene['parts'],native):
    # Parts are grouped alphabetically in both exports? Native nodes retain group
    # insertion order but XML traversal groups them; match by referent later.
    assert all(math.isfinite(v) and v>0 for v in p['size']), p['name']
    assert all(math.isfinite(v) for v in p['pos']), p['name']
    assert item.find('Properties/bool[@name="Anchored"]').text=='true'
assert len([p for p in scene['parts'] if p.get('spawn')])==1
assert any(p.get('prompt') for p in scene['parts'] if p.get('dynamic')=='bunker')
assert any(p.get('prompt') for p in scene['parts'] if p['name']=='Gate control')
assert len([p for p in scene['parts'] if p['name']=='Observation deck'])==4
assert len([p for p in scene['parts'] if p['name']=='Main rotor'])==2
assert not any('http' in (i.find('Properties/ProtectedString[@name="Source"]').text or '') for i in items if i.find('Properties/ProtectedString[@name="Source"]') is not None)
assert len(tree.findall('.//Item[@class="Script"]'))==1
assert len(tree.findall('.//Item[@class="LocalScript"]'))==1
assert len(tree.findall('.//Item[@class="ProximityPrompt"]'))==2
for group in ('Command','Helipad','Logistics','Forest','Mountains','Checkpoint'):
    assert sum(p['group']==group for p in scene['parts'])>20,group
# Independently compare geometry multiset, not traversal order, including transforms.
def native_key(i):
    pr=i.find('Properties');pos=pr.find('CoordinateFrame[@name="CFrame"]');sz=pr.find('Vector3[@name="size"]')
    return (pr.find('string[@name="Name"]').text,tuple(round(float(pos.find(a).text),4) for a in ('X','Y','Z')),tuple(round(float(sz.find(a).text),4) for a in ('X','Y','Z')))
assert Counter(native_key(i) for i in native)==Counter((p['name'],tuple(p['pos']),tuple(p['size'])) for p in scene['parts'])
print(json.dumps({'verified':True,'parts':len(native),'referents':len(refs),'groups':scene['stats']['models'],'interactions':2},indent=2))
