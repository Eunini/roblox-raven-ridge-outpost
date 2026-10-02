"""Meaningful checks on native place geometry and structural export integrity."""
import json, math, pathlib, xml.etree.ElementTree as ET
from collections import Counter
from build_scene import matrix
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
by_geometry={native_key(i):i for i in native}
for p in scene['parts']:
    i=by_geometry[(p['name'],tuple(p['pos']),tuple(p['size']))]
    if p['shape']=='sphere':
        assert i.find('Item[@class="SpecialMesh"]/Properties/token[@name="MeshType"]').text=='3','Native ellipsoid mesh missing'
    if p['shape']=='corner':
        cf=i.find('Properties/CoordinateFrame[@name="CFrame"]')
        native_rot=[float(cf.find('R'+str(r)+str(c)).text) for r in range(3) for c in range(3)]
        native_apex=[p['size'][0]/2,p['size'][1]/2,-p['size'][2]/2]
        expected_apex=[-p['size'][0]/2,p['size'][1]/2,p['size'][2]/2]
        preview_rot=matrix(p)
        for row in range(3):
            actual=sum(native_rot[row*3+j]*native_apex[j] for j in range(3))
            expected=sum(preview_rot[row*3+j]*expected_apex[j] for j in range(3))
            assert abs(actual-expected)<.0001,'Native corner orientation differs from preview'
print(json.dumps({'verified':True,'parts':len(native),'referents':len(refs),'groups':scene['stats']['models'],'interactions':2},indent=2))
