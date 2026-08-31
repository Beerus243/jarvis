"""Contrôles système bornés, sans shell."""
import shutil, subprocess

def run(command, timeout=5):
    if not shutil.which(command[0]): return False, "Dépendance système indisponible.", "NOT_SUPPORTED"
    try:
        r = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or r.stderr).strip(), None if r.returncode == 0 else "COMMAND_FAILED"
    except (OSError, subprocess.SubprocessError) as exc: return False, str(exc), "ERROR"

def wifi(action):
    if action == 'WIFI_STATUS': return run(['nmcli','-t','-f','WIFI','g'])
    return run(['nmcli','radio','wifi','on' if action == 'WIFI_ENABLE' else 'off'])

def bluetooth(action):
    if action == 'BLUETOOTH_STATUS': return run(['bluetoothctl','show'])
    return run(['bluetoothctl','power','on' if action == 'BLUETOOTH_ENABLE' else 'off'])

def settings(kind=''):
    modules = {'wifi':'kcm_networkmanagement','network':'kcm_networkmanagement','bluetooth':'kcm_bluetooth','audio':'kcm_pulseaudio','screen':'kcm_kscreen'}
    return run(['kcmshell6', modules.get(kind, 'kcm_appearance')])

def volume_status():
    ok, output, err = run(['wpctl','get-volume','@DEFAULT_AUDIO_SINK@'])
    if not ok: return ok, output, err
    parts = output.split(); level = None
    try: level = round(float(parts[1]) * 100, 1)
    except (IndexError, ValueError): pass
    return ok, {'volume_percent': level, 'muted': 'MUTED' in output, 'available': level is not None}, err
