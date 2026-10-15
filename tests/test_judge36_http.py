import json
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
import pytest
import server


def req(base,path,body=None):
    request=urllib.request.Request(base+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(request))


def test_judge_is_persisted_state_read_only_and_finish_agrees():
    http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{http.server_port}'
    try:
        catalogue=req(base,'/api/v2/cases?catalogue=36');assert len(catalogue['cases'])==36
        session=req(base,'/api/v2/sessions',{'case_id':'OS-E-01','mode':'evaluation','seed':4201,'convention':0});sid=session['id'];path=f'/api/v2/sessions/{sid}'
        judged=req(base,path+'/judge',{});assert not judged['result']['success'] and judged['status']=='active'
        for body in [{'success':True},{'state':{}},{'expected':[]},{'result':{'success':True}}]:
            with pytest.raises(urllib.error.HTTPError) as err:req(base,path+'/judge',body)
            assert err.value.code==400
        for action in server.SESSIONS[sid]['episode']['reference']:req(base,path+'/action',action)
        before=req(base,path);judged=req(base,path+'/judge',{});after=req(base,path)
        assert judged['result']['success'] and before==after
        finished=req(base,path+'/finish',{});assert finished['result']==judged['result']
        server.SESSIONS.pop(sid)
        assert req(base,path+'/judge',{})['result']['success']
        reset=req(base,path+'/reset',{});assert reset['state_hash']==session['state_hash']
        assert not req(base,path+'/judge',{})['result']['success']
        demo=req(base,'/api/v2/sessions',{'case_id':'OS-H-08','mode':'demo','convention':1,'seed':1001})
        assert demo['task_scope']=='demo' and demo['recorder_brief']['scope']=='local-method-only'
        assert len(server.SESSIONS[demo['id']]['episode']['reference'])==1
    finally:http.shutdown();http.server_close();thread.join(2)
