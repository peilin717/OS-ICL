import threading
import urllib.error
from http.server import ThreadingHTTPServer

import pytest
import server
import workflows
from test_judge36_http import req


def test_only_current_tasks_are_exposed_and_created():
    http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
    thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{http.server_port}'
    try:
        assert req(base,'/api/health')['cases']==36
        assert req(base,'/api/health')['legacy_cases']==0
        ids={c['id'] for c in req(base,'/api/v2/cases')['cases']}
        assert len(ids)==36 and not any(c.startswith('OS-LH-') for c in ids)
        for path,body,status in [('/api/v1/cases',None,410),('/api/v1/sessions',{},410),('/legacy',None,410),('/api/v2/sessions',{'case_id':'OS-LH-01'},400),('/api/v2/sessions',{'case_id':'OS-SEL-01'},400)]:
            with pytest.raises(urllib.error.HTTPError) as error:req(base,path,body)
            assert error.value.code==status
        current=req(base,'/api/v2/sessions',{'convention':0,'seed':42})
        assert current['case']['id']=='OS-E-01'
        for cid in ['OS-LH-01','OS-SEL-01']:
            with pytest.raises(ValueError):workflows.generate(cid)
    finally:
        http.shutdown();http.server_close();thread.join(2)
