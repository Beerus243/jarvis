"""Fixtures artificielles ; --provider autorise leur analyse. Aucun écran capturé."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time

from core.vision.capture import VisionError
from core.vision.evidence import read_image
from core.vision.providers import get_client, switch_provider, metrics
from core.vision.changes import fingerprint, meaningful_change

EXPECTED = 'BUILD FAILED\nModuleNotFoundError: demo'


def fixture(directory, *, blank=False):
    directory = Path(directory)
    text = directory / 'reference.txt'
    text.write_text(EXPECTED)
    output = directory / ('blank.jpg' if blank else 'error.jpg')
    filters = [] if blank else ['-vf', f'drawtext=textfile={text}:fontcolor=black:fontsize=40:x=40:y=100']
    subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi',
        '-i', 'color=c=white:s=960x540', *filters, '-frames:v', '1', '-q:v', '2', '-threads', '1', str(output)],
        capture_output=True, check=True, timeout=10)
    return output


def character_error_rate(expected, observed):
    expected, observed = ' '.join(expected.split()), ' '.join(observed.split())
    previous = list(range(len(observed) + 1))
    for i, a in enumerate(expected, 1):
        current = [i]
        for j, b in enumerate(observed, 1):
            current.append(min(current[-1]+1, previous[j]+1, previous[j-1]+(a != b)))
        previous = current
    return previous[-1] / max(1, len(expected))


def benchmark(provider=None):
    report = {'synthetic_only': True, 'provider': provider, 'cases': []}
    with tempfile.TemporaryDirectory(prefix='jarvis-v6-fixtures-') as directory:
        error = fixture(directory)
        blank = fixture(directory, blank=True)
        started = time.monotonic()
        before, after = fingerprint(blank.read_bytes()), fingerprint(error.read_bytes())
        report['pixel_filter'] = {'decoded': before is not None and after is not None,
            'error_detected': meaningful_change(before, after), 'seconds': round(time.monotonic()-started,3)}
        if provider:
            switch_provider(provider)
            client = get_client()
            for name, path in [('error',error), ('blank',blank)]:
                started = time.monotonic()
                reading = read_image(client, path.read_bytes())
                observed = '\n'.join(e['text'] for e in reading['elements'])
                report['cases'].append({'name':name, 'seconds':round(time.monotonic()-started,3),
                    'expected':EXPECTED if name=='error' else '', 'observed':observed,
                    'character_error_rate':character_error_rate(EXPECTED,observed) if name=='error' else None,
                    'invented_text_on_blank':bool(observed) if name=='blank' else None,
                    'reading':reading})
            report['metrics']=metrics()
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['groq','local'])
    parser.add_argument('--report', type=Path)
    args=parser.parse_args(argv)
    try:
        report=benchmark(args.provider)
    except (VisionError, OSError, subprocess.SubprocessError) as error:
        print(f'Benchmark indisponible : {error}')
        return 2
    rendered=json.dumps(report,ensure_ascii=False,indent=2)
    if args.report:
        args.report.write_text(rendered+'\n')
    print(rendered)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
