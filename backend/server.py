from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import os, uuid, hashlib, hmac, base64

ROOT = Path(__file__).parent
load_dotenv(ROOT / '.env')
mongo = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = mongo[os.environ['DB_NAME']]
app = FastAPI(title='Dinho Rodas API')
api = APIRouter(prefix='/api')
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get('CORS_ORIGINS','*').split(','), allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

ADMIN_EMAIL = os.environ['ADMIN_EMAIL']
ADMIN_PASSWORD = os.environ['ADMIN_PASSWORD']
TOKEN_SECRET = os.environ['TOKEN_SECRET']
COLLECTIONS = ['services','testimonials','gallery','faqs','leads','quotes']

ASSET = '/assets'
IMG_FACADE   = f'{ASSET}/fachada-gol.png'
IMG_WHEELS   = f'{ASSET}/photo-cta.png'
IMG_SERVICE  = f'{ASSET}/atendimento-presencial.png'
IMG_PAINT    = f'{ASSET}/pintura-rodas-sprinter.png'
IMG_WHEEL_VW = f'{ASSET}/roda-vw-premium.png'

DEMO = {
 'services': [
  {'title':'Rodas','description':'Encontre opções para diferentes estilos de veículos e projetos.','category':'Rodas','image_url':IMG_WHEELS,'active':True,'demo':True},
  {'title':'Pintura das rodas','description':'Recuperação, pintura e personalização de rodas.','category':'Personalização','image_url':IMG_PAINT,'active':True,'demo':True,'crop':'top'},
  {'title':'Serviços automotivos','description':'Atendimento especializado no conjunto roda e pneu.','category':'Serviços','image_url':IMG_SERVICE,'active':True,'demo':True,'crop':'bottom'},
 ],
 'testimonials': [],
 'gallery': [
  {'title':'Fachada Dinho Rodas','category':'Loja','description':'Nossa loja em Belo Horizonte.','image_url':IMG_FACADE,'active':True,'demo':True},
  {'title':'Rodas personalizadas','category':'Rodas','description':'Trabalho de recuperação e pintura.','image_url':IMG_WHEELS,'active':True,'demo':True},
  {'title':'Pintura das rodas','category':'Personalização','description':'Sprinter finalizada.','image_url':IMG_PAINT,'active':True,'demo':True,'crop':'top'},
  {'title':'Atendimento presencial','category':'Serviços','description':'Equipe Dinho Rodas em ação.','image_url':IMG_SERVICE,'active':True,'demo':True,'crop':'bottom'},
  {'title':'Roda VW premium','category':'Rodas','description':'Detalhe de roda VW disponível na loja.','image_url':IMG_WHEEL_VW,'active':True,'demo':True},
 ],
 'faqs': [
  {'question':'Como faço um orçamento?','answer':'Preencha o formulário nesta página ou fale direto com a equipe pelo WhatsApp.','order':1,'active':True,'demo':True},
  {'question':'Posso enviar uma foto do meu carro?','answer':'Sim. Você pode anexar fotos no formulário — ajuda muito na avaliação.','order':2,'active':True,'demo':True},
  {'question':'Quais os horários de atendimento?','answer':'Segunda a sexta das 08h às 18h e sábado das 08h às 13h. Domingos e feriados: fechado.','order':3,'active':True,'demo':True},
  {'question':'Como chegar até a loja?','answer':'Estamos na Rua João Caetano, 1013, Ambrosina, Belo Horizonte - MG. Use o botão "Como chegar" para abrir a rota.','order':4,'active':True,'demo':True},
 ]
}

CANONICAL_SETTINGS = {
    'company_name':'Dinho Rodas',
    'phone':'(31) 99131-0824',
    'whatsapp':'5531991310824',
    'whatsapp_display':'+55 31 99131-0824',
    'instagram':'https://instagram.com/dinho_rodas',
    'address':'Rua João Caetano, 1013 - Ambrosina, Belo Horizonte - MG, 30421-090',
    'address_short':'Rua João Caetano, 1013 · Ambrosina · BH',
    'hours':'Seg a Sex 08h às 18h · Sábado 08h às 13h · Domingo e feriado fechado',
    'hours_short':'Seg-Sex 08h-18h · Sáb 08h-13h',
    'maps_url':'https://www.google.com/maps/search/?api=1&query=Rua+Jo%C3%A3o+Caetano+1013+Ambrosina+Belo+Horizonte',
    'meta_title':'Dinho Rodas | Rodas em Belo Horizonte',
    'meta_description':'Dinho Rodas: loja e oficina especializada em rodas em Belo Horizonte, no bairro Ambrosina. Solicite seu orçamento pelo WhatsApp.',
    'settings_version': 3,
}

def now(): return datetime.now(timezone.utc).isoformat()
def clean(doc):
    if not doc: return None
    doc.pop('_id', None); return doc
def token_for(email):
    raw=f'{email}:{TOKEN_SECRET}'.encode(); return hashlib.sha256(raw).hexdigest()
def require_auth(authorization: Optional[str]):
    if not authorization or not hmac.compare_digest(authorization.replace('Bearer ','').strip(), token_for(ADMIN_EMAIL)): raise HTTPException(401, 'Não autorizado')

async def seed():
    existing = await db.settings.find_one({'id':'main'}) or {}
    version = existing.get('settings_version', 0)
    migrating = version < CANONICAL_SETTINGS['settings_version']
    for name, rows in DEMO.items():
        empty = await db[name].count_documents({}) == 0
        if empty or migrating:
            if migrating and not empty:
                await db[name].delete_many({'demo': True})
            for row in rows:
                await db[name].insert_one({**row,'id':str(uuid.uuid4()),'created_at':now()})
    if migrating:
        preserved = {k: v for k, v in existing.items() if k not in ('_id',) and k not in CANONICAL_SETTINGS}
        merged = {**CANONICAL_SETTINGS, **preserved, 'id':'main'}
        await db.settings.update_one({'id':'main'},{'$set':merged}, upsert=True)

@app.on_event('startup')
async def startup(): await seed()

class Login(BaseModel): email: str; password: str
class Item(BaseModel): model_config={'extra':'allow'}

@api.get('/public')
async def public_data():
    out={}
    for name in ['services','testimonials','gallery','faqs']:
        cursor = db[name].find({'active':{'$ne':False}}).sort('order',1)
        out[name]=[clean(x) for x in await cursor.to_list(200)]
    out['settings']=clean(await db.settings.find_one({'id':'main'}))
    return out

@api.get('/health')
async def health():
    await db.command('ping')
    return {'status':'ok','database':'connected'}

@api.post('/auth/login')
async def login(data: Login):
    if not hmac.compare_digest(data.email,ADMIN_EMAIL) or not hmac.compare_digest(data.password,ADMIN_PASSWORD):
        raise HTTPException(401,'E-mail ou senha inválidos')
    return {'token':token_for(data.email),'email':data.email}

@api.post('/quotes')
async def create_quote(name: str=Form(...), phone: str=Form(...), vehicle: str=Form(''), year: str=Form(''), interest: str=Form(''), message: str=Form(''), origin: str=Form('site-form'), photos: list[UploadFile]=File(default=[])):
    files=[]
    for photo in photos[:5]:
        if not photo.content_type or not photo.content_type.startswith('image/'): continue
        file_id=str(uuid.uuid4()); contents=await photo.read()
        if len(contents)>10*1024*1024: continue
        await db.files.insert_one({'id':file_id,'content':base64.b64encode(contents).decode(),'content_type':photo.content_type,'original_filename':photo.filename,'created_at':now()})
        files.append(f'/api/files/{file_id}')
    lead={'id':str(uuid.uuid4()),'name':name,'phone':phone,'vehicle':vehicle,'year':year,'interest':interest,'message':message,'photos':files,'origin':origin,'status':'Novo','created_at':now()}
    await db.quotes.insert_one(lead); await db.leads.insert_one({**lead,'source':origin})
    return clean(lead)

@api.get('/files/{file_id}')
async def get_file(file_id:str):
    record=await db.files.find_one({'id':file_id})
    if not record: raise HTTPException(404,'Arquivo não encontrado')
    return Response(base64.b64decode(record['content']), media_type=record.get('content_type','image/jpeg'))

ALLOWED_UPLOAD_TYPES={'image/png','image/jpeg','image/jpg','image/webp'}

@api.post('/admin/upload')
async def admin_upload(file: UploadFile=File(...), authorization: Optional[str]=Header(None)):
    require_auth(authorization)
    ctype=(file.content_type or '').lower()
    if ctype not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(400,'Formato não suportado. Envie PNG, JPG ou WEBP.')
    contents=await file.read()
    if len(contents) > 15*1024*1024:
        raise HTTPException(400,'Arquivo maior que 15MB.')
    file_id=str(uuid.uuid4())
    await db.files.insert_one({'id':file_id,'content':base64.b64encode(contents).decode(),'content_type':ctype,'original_filename':file.filename,'created_at':now(),'source':'admin_upload'})
    return {'id':file_id,'url':f'/api/files/{file_id}','content_type':ctype,'size':len(contents)}

@api.post('/leads/click')
async def whatsapp_click(data: Item):
    row={**data.model_dump(),'id':str(uuid.uuid4()),'status':'Novo','created_at':now()}
    await db.leads.insert_one(row); return clean(row)

@api.get('/dashboard/metrics')
async def metrics(authorization: Optional[str]=Header(None)):
    require_auth(authorization)
    return {
        'total_leads':await db.leads.count_documents({}),
        'total_quotes':await db.quotes.count_documents({}),
        'new_quotes':await db.quotes.count_documents({'status':'Novo'}),
        'converted':await db.leads.count_documents({'status':'Convertido'}),
        'services_count':await db.services.count_documents({'active':True}),
        'whatsapp_clicks':await db.leads.count_documents({'source':{'$regex':'WhatsApp'}}),
    }

@api.get('/admin/{collection}')
async def list_items(collection:str, authorization:Optional[str]=Header(None)):
    require_auth(authorization)
    if collection not in COLLECTIONS: raise HTTPException(404,'Coleção inválida')
    return [clean(x) for x in await db[collection].find({}).sort('created_at',-1).to_list(1000)]

@api.post('/admin/{collection}')
async def add_item(collection:str, data:Item, authorization:Optional[str]=Header(None)):
    require_auth(authorization)
    if collection not in COLLECTIONS: raise HTTPException(404,'Coleção inválida')
    row={**data.model_dump(),'id':str(uuid.uuid4()),'created_at':now()}
    await db[collection].insert_one(row); return clean(row)

@api.put('/admin/{collection}/{item_id}')
async def update_item(collection:str,item_id:str,data:Item,authorization:Optional[str]=Header(None)):
    require_auth(authorization)
    if collection not in COLLECTIONS: raise HTTPException(404,'Coleção inválida')
    payload=data.model_dump(); payload.pop('id',None); payload.pop('_id',None)
    await db[collection].update_one({'id':item_id},{'$set':payload})
    return clean(await db[collection].find_one({'id':item_id}))

@api.delete('/admin/{collection}/{item_id}')
async def delete_item(collection:str,item_id:str,authorization:Optional[str]=Header(None)):
    require_auth(authorization)
    if collection not in COLLECTIONS: raise HTTPException(404,'Coleção inválida')
    await db[collection].delete_one({'id':item_id}); return {'ok':True}

@api.get('/settings')
async def get_settings():
    doc = await db.settings.find_one({'id':'main'})
    if not doc:
        await db.settings.insert_one({**CANONICAL_SETTINGS,'id':'main'})
        doc = await db.settings.find_one({'id':'main'})
    return clean(doc)

@api.put('/settings')
async def update_settings(data:Item,authorization:Optional[str]=Header(None)):
    require_auth(authorization)
    payload=data.model_dump(); payload.pop('_id',None); payload.pop('id',None)
    await db.settings.update_one({'id':'main'},{'$set':payload},upsert=True)
    return clean(await db.settings.find_one({'id':'main'}))

app.include_router(api)

@app.on_event('shutdown')
async def shutdown(): mongo.close()
