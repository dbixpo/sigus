"""Reinicia só o SIGUS (run.py na porta 5001), em segundo plano e sem janela.

Em Sorocaba o IIS é compartilhado com o esussamu: nunca iisreset nem reciclar pool.
Aborta se o processo da porta 5001 não for o run.py.
Resultado em scripts/_reiniciar.log; saída do servidor em logs/sigus_5001.log.
"""
import os
import re
import subprocess
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(REPO, 'scripts', '_reiniciar.log')


def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')


def pids_5001():
    saida = subprocess.run(['netstat', '-ano'], capture_output=True, text=True).stdout
    pids = set()
    for linha in saida.splitlines():
        if re.search(r':5001\s', linha) and 'LISTENING' in linha:
            pids.add(linha.split()[-1])
    return pids


def cmdline(pid):
    r = subprocess.run(
        ['powershell', '-NoProfile', '-Command',
         f'(Get-CimInstance Win32_Process -Filter "ProcessId={pid}").CommandLine'],
        capture_output=True, text=True)
    return r.stdout.strip()


open(LOG, 'w').close()
for pid in pids_5001():
    cl = cmdline(pid)
    log(f'pid {pid}: {cl}')
    if 'run.py' not in cl:
        log('ABORTADO: processo na 5001 nao e o run.py')
        sys.exit(1)
    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
    log(f'encerrado {pid}')

time.sleep(2)
env = dict(os.environ, FLASK_ENV='production', SIGUS_PORT='5001', PYTHONUNBUFFERED='1')
os.makedirs(os.path.join(REPO, 'logs'), exist_ok=True)
saida_servidor = open(os.path.join(REPO, 'logs', 'sigus_5001.log'), 'a', encoding='utf-8')
saida_servidor.write(f'\n===== inicio {time.strftime("%Y-%m-%d %H:%M:%S")} =====\n')
saida_servidor.flush()
flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
abrir = dict(cwd=REPO, env=env, stdin=subprocess.DEVNULL,
             stdout=saida_servidor, stderr=subprocess.STDOUT, close_fds=True)
try:
    # 0x01000000 = CREATE_BREAKAWAY_FROM_JOB: o servidor sobrevive ao fim deste script.
    subprocess.Popen([sys.executable, 'run.py'], creationflags=flags | 0x01000000, **abrir)
except OSError:
    subprocess.Popen([sys.executable, 'run.py'], creationflags=flags, **abrir)
saida_servidor.close()

for _ in range(30):
    time.sleep(2)
    try:
        code = urllib.request.urlopen('http://localhost/sigus/login', timeout=5).status
        log(f'login status {code}; listeners {pids_5001()}')
        break
    except Exception as e:
        log(f'aguardando... {e}')
