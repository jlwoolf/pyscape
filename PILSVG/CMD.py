
import argparse
import sys
import os
from pathlib import Path
from PILSVG import SVG


def main():
    # defining the parser and its args
    parser = argparse.ArgumentParser("pillow-svg", description="""
Converts svg files to different image formats utilizing pillow and inkscape. By default, pillow-svg will convert
all svg files from the current working directory to the specified image format. For example if the svg file is 
'example.svg', then 'pillow-svg example.svg' will create file 'example.png'.
        """)

    parser.add_argument("--dir", nargs="+", type=str,
                        help="The path(s) of the directories to process.")
    parser.add_argument("--fp", nargs='+', type=str,
                        help="The filepath(s) of the svg(s)")
    parser.add_argument("--dpi", nargs='+', type=int,
                        help="The dpi(s) of the rendered svg(s)")
    parser.add_argument("--size", nargs='+', type=int,
                        help="The size(s) of the rendered svg(s) in pixels.")
    parser.add_argument("--dim", nargs='+', type=int,
                        help="The dimension(s) of the rendered svg(s) in pixels. Use pairs of ints.")
    parser.add_argument("--renderer", nargs='?', default='skia',
                        help="The renderer (skia or inkscape) to use. Defaults to skia.")
    parser.add_argument("--format", nargs='+', type=str,
                        default=['png'], help="The format to export the svg(s) as.")
    parser.add_argument("--out", nargs='?', type=str,
                        help="The output directory. Will output to svg file(s) location if none is provided.")

    error_val = 0

    args = parser.parse_args()

    if args.dir:
        args.dir = [Path(path) for path in args.dir]
    elif args.fp:
        args.dir = []
    else:
        args.dir = [Path(os.getcwd())]

    for dir in args.dir:
        if not dir.resolve().exists():
            print(
                f"ERROR:\tDirectory '{dir}' does not exist.", file=sys.stderr)
            error_val += 1

    if args.out:
        args.out = Path(args.out)
        if not args.out.resolve().exists():
            print(
                f"ERROR:\tOutput directory '{args.out}' does not exist.", file=sys.stderr)

    paths = [file for path in args.dir for file in list(path.glob('*.svg'))]

    if args.fp:
        args.fp = [Path(path) for path in args.fp]

        for fp in args.fp:
            if not fp.resolve().exists():
                print(
                    f"ERROR:\tSVG file '{fp}' does not exist.", file=sys.stderr)
                error_val += 1

        paths.extend(args.fp)

    if args.size:
        sizes = args.size
    else:
        sizes = []

    if args.dim:
        if len(args.dim) % 2 != 0:
            print(
                f"ERROR:\tDimensional values must come in pairs of two. An odd number of values, {len(args.dim)}, was provided.", file=sys.stderr)
            error_val += 1
        else:
            args.dim = [(args.dim[2*i], args.dim[2*i+1])
                        for i in range(len(args.dim) // 2)]

        sizes.extend(args.dim)

    if error_val:
        exit(-1)

    for path in paths:
        if args.out:
            stem = args.out.resolve().joinpath(path.stem)
        else:
            stem = path.resolve().parent.joinpath(path.stem)

        SVG.EXPORT(path, stem, format=args.format, dpi=args.dpi,
                   size=sizes, renderer=args.renderer)

    exit(0)
