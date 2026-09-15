"""État V6 sans capture. --hardware ajoute les mesures GPU disponibles."""
import argparse
import json
from core.vision.health import capability_report, hardware_report, format_report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--hardware', action='store_true')
    args = parser.parse_args(argv)
    report = capability_report()
    if args.hardware:
        report['hardware'] = hardware_report()
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_report(report))
    if args.hardware and not args.json:
        print(report['hardware'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
