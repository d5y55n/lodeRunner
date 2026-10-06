from copy import deepcopy
import json
from pathlib import Path
import pytest
from app.website import manual, scoring
from app.website.events import YouTubeProvider, EventMonitor
from test_website_symbols import populated


@pytest.mark.parametrize('value',['0','-1','NaN','Infinity','-inf','abc','','1e999',None,'1_000','0x10'])
def test_invalid_manual_price(value):
    with pytest.raises(ValueError):manual.valid_price(value)


def test_manual_price_map_reuse_and_market_parity(tmp_path,monkeypatch):
    d,t=populated(tmp_path,'ETHUSDT',3)
    try:
        base=d.replay(t);d.snapshot=base
        current=manual.evaluate(d)
        assert current['scoring']==base['scoring']
        equal=manual.evaluate(d,str(base['price']))
        assert equal['scoring']==base['scoring']
        maps=deepcopy({tf:cs for tf,(f,cs) in d.manual_maps[(t,base['config_hash'])].items()})
        monkeypatch.setattr(scoring,'candidates',lambda _:pytest.fail('Manual P must reuse existing candidates'))
        result=manual.evaluate(d,'0.00000123')
        assert result['analysis_price']==.00000123 and result['price_mode']=='manual'
        assert result['scoring']!=base['scoring']
        assert result['converging']==base['converging']
        assert result['charts']==base['charts'] and d.snapshot==base
        assert result['price']==base['price']
        assert maps=={tf:cs for tf,(f,cs) in d.manual_maps[(t,base['config_hash'])].items()}
    finally:d.stop()


class YouTube:
    key='test-only'
    def __init__(self):self.state='OFFLINE';self.video='abcdefghijk';self.fail=False
    def check(self,*args):
        if self.fail:raise ValueError('YouTube HTTP 403')
        return dict(state=self.state,video_id=self.video if self.state=='LIVE' else None,title='Live title')


def test_youtube_new_video_dedup_and_error(tmp_path):
    now=[1800000000];yt=YouTube();m=EventMonitor(tmp_path/'events.sqlite3',youtube=yt,clock=lambda:now[0])
    m.tick();assert m.status()['youtube']['state']=='OFFLINE'
    yt.state='LIVE';now[0]+=3600;m.tick()
    now[0]+=3600;m.tick();assert len(m.status()['alerts'])==1
    yt.video='lmnopqrstuv';now[0]+=3600;m.tick();assert len(m.status()['alerts'])==2
    yt.fail=True;now[0]+=3600;m.tick();s=m.status()['youtube']
    assert s['state']=='ERROR' and s['title']=='Live title' and s['stale']
    yt.fail=False;yt.state='OFFLINE';now[0]+=3600;m.tick()
    assert m.status()['youtube']['state']=='OFFLINE'


@pytest.mark.parametrize('mode',['LIVE','OFFLINE','UPCOMING'])
def test_official_youtube_contract(monkeypatch,mode):
    p=YouTubeProvider('fake-not-secret');calls=[];saved=[];cid='UC'+'x'*22
    def get(resource,**params):
        calls.append((resource,params))
        if resource=='channels':return dict(items=[dict(id=cid)])
        if resource=='videos':return dict(items=[dict(liveStreamingDetails=dict(scheduledStartTime='2026-10-06T12:30:00Z'))])
        if params['eventType']==mode.lower():return dict(items=[dict(id=dict(videoId='abcdefghijk'),snippet=dict(channelId=cid,title='Current live title'))])
        return dict(items=[])
    monkeypatch.setattr(p,'get',get)
    result=p.check(save_channel=saved.append)
    assert result['state']==mode and saved==[cid]
    if mode!='OFFLINE':
        assert result['title']=='Current live title' and result['url']=='https://www.youtube.com/watch?v=abcdefghijk'
    p.check(channel_id=cid)
    assert len([r for r in calls if r[0]=='channels'])==1
    for resource,params in calls:
        if resource=='search':assert params['channelId']==cid and params['type']=='video'


def test_youtube_missing_key_never_scrapes(monkeypatch):
    p=YouTubeProvider('');monkeypatch.setattr(p,'get',lambda *a,**k:pytest.fail('No requests without key'))
    assert p.check()['state']=='UNCONFIGURED'


def test_calendar_retirement_preserves_youtube_and_restart_dedup(tmp_path):
    now=1800000000;yt=YouTube();yt.state='LIVE'
    m=EventMonitor(tmp_path/'events.sqlite3',youtube=yt,clock=lambda:now)
    m.save('calendar',{'events':[{'name':'retired'}]})
    m.save('channel_id','retained-channel')
    m.notify('calendar:old','ECONOMIC_EVENT_UPCOMING',{'event':{}})
    m.tick()
    restored=EventMonitor(m.path,youtube=yt,clock=lambda:now)
    restored.tick()
    assert restored.read('calendar') is None
    assert restored.read('channel_id')=='retained-channel'
    assert 'calendar' not in restored.status() and 'alert_minutes' not in restored.status()
    assert len(restored.status()['alerts'])==1
    assert len(restored.claim())==1 and restored.claim()==[]
    with restored.db() as db:
        assert db.execute("SELECT COUNT(*) FROM notifications WHERE id LIKE 'calendar:%'").fetchone()[0]==0


def test_monitor_has_no_calendar_provider_or_polling(tmp_path,monkeypatch):
    from app.website import events
    assert not hasattr(events,'InvestingCalendarProvider')
    monkeypatch.setattr(events.httpx,'Client',lambda *a,**k:pytest.fail('No calendar request may occur'))
    m=EventMonitor(tmp_path/'events.sqlite3',youtube=YouTube(),clock=lambda:1800000000)
    m.tick()
    with m.db() as db:
        assert [r[0] for r in db.execute('SELECT key FROM state')]==['youtube']


def test_manual_api_rejects_nonfinite_before_registry(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setattr(manual.registry,'get',lambda _:pytest.fail('Invalid P must not allocate workers'))
    client=TestClient(app)
    assert client.get('/dashboard/BTCUSDT/price?price=NaN').status_code==422
