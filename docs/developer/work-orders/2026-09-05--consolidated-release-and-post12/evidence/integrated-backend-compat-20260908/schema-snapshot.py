from pathlib import Path
import hashlib,json,sys
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
ROOT=Path('/opt/r12/integrated-compat-20260908')
label=sys.argv[1];assert label in ('after-previous','after-current','after-rollback')
p=ROOT/('schema-'+label+'.json');assert not p.exists()
e=create_engine(dotenv_values(ROOT/'config.env')['DATABASE_URL'],hide_parameters=True)
with e.connect() as c:
 cols=[list(r) for r in c.execute(text("SELECT table_name,column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position"))]
 indexes=[list(r) for r in c.execute(text("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename,indexname"))]
 constraints=[list(r) for r in c.execute(text("SELECT t.relname,c.conname,pg_get_constraintdef(c.oid) FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname='public' ORDER BY t.relname,c.conname"))]
e.dispose();data={'columns':cols,'indexes':indexes,'constraints':constraints};p.write_text(json.dumps(data,indent=2)+'\n')
digest=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
if label!='after-previous':assert data==json.loads((ROOT/'schema-after-previous.json').read_text()),'schema changed between previous/current/rollback'
print(json.dumps({'label':label,'columns':len(cols),'indexes':len(indexes),'constraints':len(constraints),'schema_sha256':digest,'same_as_previous':label!='after-previous'}))
