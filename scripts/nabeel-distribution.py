#!/usr/bin/env python3
import argparse, json, os, subprocess, sys
from pathlib import Path

def load(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema')!='nabeel.distribution.v1': raise SystemExit('invalid_schema')
    return data

def resolved(dest):
    secret_name=dest.get('secret_env') or ''
    secret=os.environ.get(secret_name) if secret_name else None
    # Only an explicit JSON boolean can authorize a destination.
    enabled=dest.get('enabled',False) is True
    ready=enabled and bool(secret) and bool(dest.get('url'))
    reason='ready' if ready else ('disabled' if not enabled else ('missing_secret' if not secret else 'missing_url'))
    return {'id':dest.get('id'),'protocol':dest.get('protocol','rtmp'),'enabled':enabled,'ready':ready,'reason':reason,'secret_ref':secret_name}

def status(cfg):
    print(json.dumps({'source':cfg.get('source'),'destinations':[resolved(d) for d in cfg.get('destinations',[])]},indent=2))

def run(cfg,dest_id,dry):
    dest=next((d for d in cfg.get('destinations',[]) if d.get('id')==dest_id),None)
    if not dest: raise SystemExit('unknown_destination')
    st=resolved(dest)
    if not st['ready']:
        print(json.dumps(st),file=sys.stderr); raise SystemExit(4)
    secret=os.environ[dest['secret_env']]
    target=dest['url'].replace('{secret}',secret)
    source=cfg['source']
    cmd=['ffmpeg','-hide_banner','-loglevel','warning','-re','-i',source,'-c','copy','-f','flv',target]
    if dest.get('protocol')=='srt': cmd=['ffmpeg','-hide_banner','-loglevel','warning','-re','-i',source,'-c','copy','-f','mpegts',target]
    if dry:
        print(json.dumps({'destination':dest_id,'ready':True,'command_redacted':[x.replace(secret,'<secret>') for x in cmd]},indent=2)); return
    os.execvp(cmd[0],cmd)

p=argparse.ArgumentParser()
p.add_argument('--config',required=True)
sub=p.add_subparsers(dest='cmd',required=True)
sub.add_parser('status')
r=sub.add_parser('run'); r.add_argument('destination'); r.add_argument('--dry-run',action='store_true')
a=p.parse_args(); cfg=load(a.config)
status(cfg) if a.cmd=='status' else run(cfg,a.destination,a.dry_run)
