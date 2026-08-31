"""Mesures matérielles locales, tolérantes aux informations manquantes."""
from dataclasses import dataclass, asdict
import os, platform, shutil, subprocess

@dataclass(frozen=True)
class CPUStats:
    usage_percent: float | None; cores: int | None; threads: int | None; frequency_mhz: float | None; temperature_c: float | None
@dataclass(frozen=True)
class MemoryStats:
    total_bytes: int | None; used_bytes: int | None; available_bytes: int | None; usage_percent: float | None
@dataclass(frozen=True)
class GPUStats:
    name: str | None; vendor: str | None; usage_percent: float | None; memory_total_bytes: int | None; memory_used_bytes: int | None; temperature_c: float | None; driver: str | None

def cpu_stats():
    usage = None
    try:
        first = open('/proc/stat').readline().split()[1:]
        vals = list(map(int, first[:4])); total = sum(vals); idle = vals[3]
        cpu_stats._last = getattr(cpu_stats, '_last', (total, idle))
        old_total, old_idle = cpu_stats._last; cpu_stats._last = (total, idle)
        dt, di = total-old_total, idle-old_idle
        usage = round(100*(dt-di)/dt, 1) if dt else None
    except (OSError, ValueError): pass
    freq = None
    try: freq = float(open('/proc/cpuinfo').read().split('cpu MHz')[1].split(':')[1].split()[0])
    except (OSError, IndexError, ValueError): pass
    return CPUStats(usage, os.cpu_count(), os.cpu_count(), freq, None)

def memory_stats():
    try:
        info = {line.split(':',1)[0]: int(line.split()[1])*1024 for line in open('/proc/meminfo') if ':' in line}
        total, avail = info.get('MemTotal'), info.get('MemAvailable')
        used = total-avail if total is not None and avail is not None else None
        return MemoryStats(total, used, avail, round(100*used/total,1) if total and used is not None else None)
    except (OSError, ValueError): return MemoryStats(None,None,None,None)

def gpu_stats():
    if shutil.which('nvidia-smi'):
        try:
            r=subprocess.run(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.total,memory.used,temperature.gpu,driver_version','--format=csv,noheader,nounits'],capture_output=True,text=True,check=False,timeout=3)
            p=[x.strip() for x in r.stdout.split(',')]
            if r.returncode==0 and len(p)>=6:
                num=lambda x: float(x) if x not in {'[Not Supported]','N/A',''} else None
                return GPUStats(p[0],'NVIDIA',num(p[1]),int(float(p[2])*1024*1024) if p[2].replace('.','',1).isdigit() else None,int(float(p[3])*1024*1024) if p[3].replace('.','',1).isdigit() else None,num(p[4]),p[5])
        except (OSError, subprocess.SubprocessError, ValueError): pass
    return GPUStats(None,None,None,None,None,None,None)

def pc_status():
    return {'os': platform.platform(), 'cpu': asdict(cpu_stats()), 'memory': asdict(memory_stats()), 'gpu': asdict(gpu_stats())}
