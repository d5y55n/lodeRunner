"""YouTube-only monitoring and durable, at-most-once local event delivery."""
from html import unescape
from pathlib import Path
import json
import os
import re
import sqlite3
import threading
import time
import httpx
from fastapi import APIRouter
from .config import PROJECT

class YouTubeProvider:
    def __init__(self,key=None):
        self.key=self.local_key() if key is None else key

    @staticmethod
    def local_key():
        if os.getenv('YOUTUBE_API_KEY'):
            return os.environ['YOUTUBE_API_KEY']
        if os.name!='nt':
            return ''
        path=Path(os.getenv('LOCALAPPDATA',''))/'lodeRunner/youtube-key.dpapi'
        if not path.exists():
            return ''
        # Windows user-bound DPAPI; the key never enters source control or logs.
        import ctypes
        from ctypes import wintypes
        class Blob(ctypes.Structure):
            _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_byte))]
        raw=bytes.fromhex(path.read_text().strip())
        buffer=(ctypes.c_byte*len(raw)).from_buffer_copy(raw)
        source=Blob(len(raw),buffer);out=Blob()
        if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source),None,None,None,None,0,ctypes.byref(out)):
            return ''
        try:
            return ctypes.string_at(out.data,out.size).decode('utf-16-le')
        finally:
            free=ctypes.windll.kernel32.LocalFree
            free.argtypes=[ctypes.c_void_p];free.restype=ctypes.c_void_p
            free(out.data)

    def get(self,resource,**params):
        with httpx.Client(timeout=20) as client:
            r=client.get('https://www.googleapis.com/youtube/v3/'+resource,params=dict(key=self.key,**params))
            if r.status_code!=200:
                # Never expose request URLs containing the API key.
                raise ValueError('YouTube HTTP '+str(r.status_code))
            return r.json()

    def check(self,channel_id=None,save_channel=lambda value:None):
        if not self.key:
            return dict(state='UNCONFIGURED',channel_id=channel_id)
        if not channel_id:
            items=self.get('channels',part='id',forHandle='@EZPZNOW')['items']
            if len(items)!=1 or not re.fullmatch(r'UC[\w-]{22}',items[0]['id']):
                raise ValueError('EZPZNOW channel identity unresolved')
            channel_id=items[0]['id'];save_channel(channel_id)
        for event_type,state in [('live','LIVE'),('upcoming','UPCOMING')]:
            items=self.get('search',part='snippet',channelId=channel_id,eventType=event_type,type='video',maxResults=5)['items']
            if not items:
                continue
            item=items[0];video=item['id']['videoId'];snippet=item['snippet']
            if snippet['channelId']!=channel_id or not re.fullmatch(r'[\w-]{11}',video):
                raise ValueError('YouTube identity mismatch')
            details=self.get('videos',part='liveStreamingDetails',id=video)['items']
            if len(details)!=1:
                raise ValueError('YouTube video details unavailable')
            timing=details[0].get('liveStreamingDetails',{})
            if timing.get('actualEndTime'):
                continue
            return dict(state=state,channel_id=channel_id,video_id=video,title=unescape(snippet['title']),
                        url='https://www.youtube.com/watch?v='+video,
                        thumbnail=snippet.get('thumbnails',{}).get('default',{}).get('url'),
                        scheduled_start=timing.get('scheduledStartTime'),actual_start=timing.get('actualStartTime'))
        return dict(state='OFFLINE',channel_id=channel_id,video_id=None)


class EventMonitor:
    def __init__(self,path=None,youtube=None,clock=time.time):
        self.path=Path(path or PROJECT/'data/live-dashboard/events.sqlite3');self.path.parent.mkdir(parents=True,exist_ok=True)
        self.youtube=youtube or YouTubeProvider();self.clock=clock
        self.youtube_interval=max(1800,int(os.getenv('YOUTUBE_POLL_SECONDS','3600')))
        self.lock=threading.RLock();self.stop_event=threading.Event();self.thread=None
        with self.db() as db:
            db.executescript('CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY,payload TEXT); CREATE TABLE IF NOT EXISTS notifications(id TEXT PRIMARY KEY,kind TEXT,payload TEXT,created REAL,delivered INTEGER DEFAULT 0);')

            # Retire only calendar state; retain YouTube identity and deduplication.
            db.execute("DELETE FROM state WHERE key='calendar'")
            db.execute("DELETE FROM notifications WHERE kind IN ('ECONOMIC_EVENT_UPCOMING','ECONOMIC_EVENT_RELEASE') OR id LIKE 'calendar:%'")

    def db(self):
        from contextlib import contextmanager
        @contextmanager
        def connection():
            db=sqlite3.connect(self.path,timeout=20)
            try:
                with db:yield db
            finally:db.close()
        return connection()

    def read(self,key,default=None):
        with self.db() as db:
            row=db.execute('SELECT payload FROM state WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default

    def save(self,key,value):
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO state VALUES(?,?)',(key,json.dumps(value,ensure_ascii=False)))

    def notify(self,key,kind,payload):
        with self.db() as db:
            db.execute('INSERT OR IGNORE INTO notifications(id,kind,payload,created) VALUES(?,?,?,?)',(key,kind,json.dumps(payload,ensure_ascii=False),self.clock()))

    def tick(self):
        with self.lock:
            now=self.clock()
            yt=self.read('youtube',{})
            if now-yt.get('checked_at',0)>=self.youtube_interval or (yt.get('state')=='UNCONFIGURED' and self.youtube.key):
                try:
                    new=self.youtube.check(self.read('channel_id'),lambda cid:self.save('channel_id',cid))
                    new.update(checked_at=now,valid_at=now,previous_video_id=yt.get('video_id'))
                    if new['state']=='LIVE' and (yt.get('state')!='LIVE' or yt.get('video_id')!=new['video_id']):
                        self.notify('youtube:'+new['video_id'],'YOUTUBE_LIVE_STARTED',new)
                    self.save('youtube',new)
                except Exception as exc:
                    self.save('youtube',dict(yt,state='ERROR',checked_at=now,error=str(exc) if isinstance(exc,ValueError) else 'YouTube source unavailable'))

    def status(self):
        now=self.clock();yt=self.read('youtube',dict(state='UNCONFIGURED' if not self.youtube.key else 'LOADING'))
        if yt.get('title'):
            yt['title']=unescape(yt['title'])
        yt['stale']=yt.get('state')=='ERROR' or now-yt.get('valid_at',0)>self.youtube_interval*2
        yt['poll_seconds']=self.youtube_interval
        with self.db() as db:
            rows=db.execute("SELECT id,kind,payload,created FROM notifications WHERE kind='YOUTUBE_LIVE_STARTED' ORDER BY created DESC LIMIT 20").fetchall()
        return dict(youtube=yt,alerts=[dict(id=i,kind=k,payload=json.loads(p),created=t) for i,k,p,t in rows],server_timestamp=now)

    def claim(self):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            rows=db.execute("SELECT id,kind,payload FROM notifications WHERE kind='YOUTUBE_LIVE_STARTED' AND delivered=0 AND created>=? ORDER BY created LIMIT 20",(self.clock()-120,)).fetchall()
            db.executemany('UPDATE notifications SET delivered=1 WHERE id=?',[(r[0],) for r in rows])
        return [dict(id=i,kind=k,payload=json.loads(p)) for i,k,p in rows]

    def start(self):
        if self.thread is not None:
            return
        with self.lock:
            if self.thread is None:
                self.thread=threading.Thread(target=self.run,daemon=True,name='public-events');self.thread.start()
    def run(self):
        while not self.stop_event.is_set():
            try:self.tick()
            except Exception:pass  # Keep retrying; persisted timestamps expose stale state.
            self.stop_event.wait(15)
    def stop(self):
        self.stop_event.set()
        if self.thread:self.thread.join(timeout=45)


router=APIRouter(tags=['events'])
_monitor=None
_monitor_lock=threading.Lock()


def monitor():
    global _monitor
    with _monitor_lock:
        if _monitor is None:_monitor=EventMonitor()
        return _monitor


@router.get('/events/status')
def event_status():
    m=monitor();m.start();return m.status()


@router.post('/events/notifications/claim')
def claim_notifications():
    return dict(notifications=monitor().claim())
