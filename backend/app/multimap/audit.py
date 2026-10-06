"""Read-only audit of frozen prior research artifacts."""
from .contract import ROOT,PROJECT,read,sha256,write_json


def preservation():
    baseline=read(ROOT/'preserved-before.json');changed=[]
    for name,digest in baseline.items():
        path=PROJECT/name
        if not path.is_file() or sha256(path)!=digest:changed.append(name)
    result=dict(status='PASS' if not changed else 'FAIL',files=len(baseline),changed=changed,
                scope='Frozen Phase 3R/3R.1/3R.2 artifacts and engines; no market acquisition or outcomes')
    write_json(ROOT/'preservation-audit.json',result)
    if changed:raise ValueError('Prior research preservation failed')
    print('PRESERVATION_PASS',len(baseline),flush=True)


if __name__=='__main__':preservation()
