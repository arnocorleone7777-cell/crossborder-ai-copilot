import asyncio
import hmac
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from backend.config import DB_PATH, GENERATED, ROOT, provider
from backend.db.seed_anomaly_data import seed_sqlite
from backend.models import ChatRequest, Filters
from backend.agent.graph import build_graph
from backend.services.analytics import build_report
from backend.services import history, llm
from backend.services.mcp_client import connect_tools

@asynccontextmanager
async def lifespan(app):
    if os.getenv('DATABASE_ENGINE','sqlite')=='sqlite' and not DB_PATH.exists(): await asyncio.to_thread(seed_sqlite)
    GENERATED.mkdir(exist_ok=True)
    yield

def authorize(authorization: str | None=Header(default=None)):
    expected=os.getenv('API_TOKEN','')
    if expected and not hmac.compare_digest(authorization or '',f'Bearer {expected}'):
        raise HTTPException(401,'访问凭证无效')

app=FastAPI(title='CrossBorder Copilot',version='1.0.0',lifespan=lifespan,dependencies=[Depends(authorize)])
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('ALLOWED_ORIGINS','http://127.0.0.1:5173,http://localhost:5173').split(','),allow_methods=['GET','POST'],allow_headers=['Content-Type','Authorization'])
slots=asyncio.Semaphore(3)

@app.get('/api/health')
async def health():
    return {'status':'ok','mode':provider(),'database':os.getenv('DATABASE_ENGINE','sqlite'),
            'ollama':await llm.health(),'synthetic':True,'mcp_transport':'stdio'}

@app.get('/api/dashboard')
async def dashboard(start:str='2026-10-25',end:str='2026-10-31',platform:str='all',sku:str='all'):
    try: filters=Filters(start=start,end=end,platform=platform,sku=sku)
    except ValueError as exc: raise HTTPException(422,'筛选范围无效') from exc
    try: return await asyncio.to_thread(build_report,filters)
    except Exception as exc:
        logging.exception('Dashboard failed')
        raise HTTPException(503,'查询暂不可用，请检查数据库或缩小查询范围') from exc

@app.get('/api/runs')
async def runs(): return await asyncio.to_thread(history.recent)

@app.get('/api/runs/{run_id}')
async def run(run_id:str):
    record=await asyncio.to_thread(history.get,run_id)
    if not record: raise HTTPException(404,'分析记录不存在')
    return record

@app.get('/assets/generated/{filename}')
async def asset(filename:str):
    if not filename.endswith('.png') or '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(404)
    path=GENERATED/filename
    if not path.is_file(): raise HTTPException(404)
    return FileResponse(path,media_type='image/png')

@app.post('/api/chat/stream')
async def stream(body:ChatRequest,request:Request):
    try: await asyncio.wait_for(slots.acquire(),.2)
    except TimeoutError: raise HTTPException(429,'已有 3 个分析运行中，请稍后再试')
    run_id=uuid.uuid4().hex
    async def events():
        queue=asyncio.Queue(maxsize=64)
        final=None
        async def produce():
            try:
                async with connect_tools() as (bi,creative):
                    graph=build_graph(bi,creative)
                    async for event in graph.astream(body.model_dump(mode='json'),stream_mode='custom',config={'recursion_limit':25}):
                        await queue.put(event)
            except asyncio.CancelledError: raise
            except Exception as exc:
                logging.exception('Run %s failed',run_id)
                await queue.put({'type':'done','result':{'status':'failed','mode':provider(),'message':f'运行失败（{type(exc).__name__}），请查看服务日志与连接配置。'}})
            finally:
                try: queue.put_nowait(None)
                except asyncio.QueueFull: pass
        task=asyncio.create_task(produce())
        sequence=0
        try:
            yield f'event: run\ndata: {json.dumps({"type":"run","run_id":run_id})}\n\n'
            while True:
                try: event=await asyncio.wait_for(queue.get(),10)
                except TimeoutError:
                    if await request.is_disconnected(): break
                    yield ': heartbeat\n\n';continue
                if event is None: break
                if event['type']=='done':
                    final={**event['result'],'run_id':run_id}
                    await asyncio.to_thread(history.save,run_id,body.prompt,final)
                sequence+=1
                payload=json.dumps({**event,'run_id':run_id,'seq':sequence},ensure_ascii=False,allow_nan=False)
                yield f'id: {sequence}\nevent: {event["type"]}\ndata: {payload}\n\n'
        finally:
            task.cancel()
            try: await task
            except asyncio.CancelledError: pass
            slots.release()
    return StreamingResponse(events(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

dist=ROOT/'frontend/dist'
if dist.is_dir(): app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
