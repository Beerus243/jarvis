from __future__ import annotations
import os, shutil
from pathlib import Path

class JavaEnvironmentResolver:
    def resolve(self) -> dict:
        java=shutil.which('java'); javac=shutil.which('javac')
        candidates=[]
        if os.getenv('JAVA_HOME'): candidates.append(Path(os.environ['JAVA_HOME']))
        candidates += list(Path('/usr/lib/jvm').glob('*')) if Path('/usr/lib/jvm').is_dir() else []
        found=next((p/'bin/javac' for p in candidates if (p/'bin/javac').exists()),None)
        return {'java': java, 'javac': javac or (str(found) if found else None),
                'java_home': os.getenv('JAVA_HOME'),
                'status': 'CONFIGURED' if java and javac else 'MISCONFIGURED' if java else 'MISSING'}

class AndroidEnvironmentResolver:
    def resolve(self) -> dict:
        roots=[os.getenv(k) for k in ('ANDROID_SDK_ROOT','ANDROID_HOME') if os.getenv(k)]
        roots += [str(Path.home()/'Android/Sdk'),str(Path.home()/'Android/sdk')]
        sdk=next((Path(p) for p in roots if Path(p).is_dir()),None)
        adb=shutil.which('adb') or (str(sdk/'platform-tools/adb') if sdk and (sdk/'platform-tools/adb').exists() else None)
        return {'sdk': str(sdk) if sdk else None, 'adb': adb,
                'status': 'CONFIGURED' if sdk and shutil.which('adb') else 'MISCONFIGURED' if sdk else 'MISSING'}

class FlutterEnvironmentResolver:
    def resolve(self) -> dict:
        flutter=shutil.which('flutter'); dart=shutil.which('dart')
        return {'flutter': flutter, 'dart': dart,
                'status': 'CONFIGURED' if flutter and dart else 'MISCONFIGURED' if flutter else 'MISSING'}
