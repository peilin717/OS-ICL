import copy,importlib.util,json
from pathlib import Path
import pytest
import workflows as w
ROOT=Path(__file__).resolve().parents[1]
def module(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
revise=module('revise108_examples');export=module('export_v2_episode')

@pytest.mark.parametrize('c',[0,1,2])
def test_quantity_examples_vary_and_cover_zero_remainder(c):
 evidence=revise.example_coverage(w.generate('OS-M-11',c,1016,'module-demo'))
 assert revise.validate_example_set([evidence])
 with pytest.raises(AssertionError):revise.validate_example_set([revise.example_coverage(w.generate('OS-M-11',c,1001,'module-demo'))])

@pytest.mark.parametrize('c',[0,1,2])
def test_rounding_examples_cover_both_directions(c):
 evidence=[revise.example_coverage(w.generate('OS-H-11',c,seed,'module-demo')) for seed in [1001,33,509]]
 assert revise.validate_example_set(evidence)
 with pytest.raises(AssertionError):revise.validate_example_set(evidence[:1])

def test_every_example_seed_is_query_disjoint_and_model_receives_one_url(tmp_path):
 manifest=json.loads((ROOT/'docs/STANDARD108_MANIFEST.json').read_text())
 row=next(x for x in manifest['videos'] if x['case_id']=='OS-H-11' and x['condition']=='C');row['example_seeds']=[1001,33,509]
 path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest))
 for seed in [1001,33,509]:
  ep=w.generate('OS-H-11',2,seed)
  assert export.manifest_demos(ep,path)==[]
  with pytest.raises(ValueError):export.build_export({'id':'osl_query','mode':'evaluation','episode':ep},[{'case_id':'OS-H-11','convention':2,'seed':1001,'example_seeds':[1001,33,509]}],'http://localhost:8790')
 ep=w.generate('OS-H-11',2,4201);demos=export.manifest_demos(ep,path);launch,_=export.build_export({'id':'osl_query','mode':'evaluation','episode':ep},demos,'http://localhost:8790')
 assert len(launch['demonstrations'])==1
 assert all(key not in json.dumps(launch) for key in ['example_seeds','segments','provenance','condition'])
