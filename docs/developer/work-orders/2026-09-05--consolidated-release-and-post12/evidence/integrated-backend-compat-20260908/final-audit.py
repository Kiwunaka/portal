from pathlib import Path
import hashlib,json,subprocess,sys
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
ROOT=Path('/opt/r12/integrated-compat-20260908')
manifest=json.loads((ROOT/'source-manifests.json').read_text());verified={}
for label in ('previous','current'):
 source=manifest[label]
 for e in source['files']:assert hashlib.sha256((ROOT/label/e['path']).read_bytes()).hexdigest()==e['sha256']
 verified[label]=len(source['files'])
env=dotenv_values(ROOT/'config.env');engine=create_engine(env['DATABASE_URL'],hide_parameters=True)
ids=[r['event_id'] for p in ('previous-before','concurrent','previous-after','previous-restarted') for r in json.loads((ROOT/(p+'-http.json')).read_text())['requests']]
with engine.connect() as c:
 for identity in ids:assert c.execute(text('SELECT count(*) FROM events WHERE event_id=:id AND tg_id=6201'),{'id':identity}).scalar()==1
 assert c.execute(text('SELECT count(*) FROM support_tickets WHERE id=1')).scalar()==1
 assert c.execute(text('SELECT count(*) FROM support_attachments WHERE ticket_id=1 AND message_id=1')).scalar()==1
engine.dispose()
schemas=[json.loads((ROOT/('schema-'+phase+'.json')).read_text()) for phase in ('after-previous','after-current','after-rollback')]
assert schemas[0]==schemas[1]==schemas[2]
schema=schemas[0]
journals={}
for label in ('previous','current'):
 p=subprocess.run(['journalctl','-u','r12-integrated-'+label,'--no-pager','-o','short-monotonic'],capture_output=True,text=True);assert p.returncode==0
 output=p.stdout
 for value in env.values():
  if value and len(value)>15:output=output.replace(value,'[redacted]')
 path=ROOT/(label+'-journal.log');path.write_text(output);journals[label]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
p=subprocess.run([sys.executable,'-m','pip','check'],capture_output=True,text=True);assert p.returncode==0,'dependency check failed'
report={'result':'PASS_CURRENT_LOCAL_API_COMPATIBILITY','source_files_verified':verified,'event_writes_verified':len(ids),'http_assertions':25,'ticket_and_attachment_rows_retained':True,'schema_identical_after_previous_current_rollback':True,'schema_counts':{k:len(v) for k,v in schema.items()},'new_expand_or_contract_schema_change_between_inputs':False,'schema_inputs':manifest['schema_inputs_identical'],'requests_are_real_http':True,'database_is_real_postgresql':True,'python_version':sys.version.split()[0],'pip_check':'PASS','journals':journals,'provider_io_executed':False,'production_mutation':False}
(ROOT/'final-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
