"""Normalize the supplied history and reproduce frozen-protocol Bitcoin research."""
import argparse
from pathlib import Path
from astrocalc.universal.research import run

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,default=Path('data/bitcoin_2010-07-02_2025-07-05.csv'))
parser.add_argument('--output',type=Path,default=Path('reports/bitcoin'))
parser.add_argument('--workspaces',type=Path,default=Path('data/bitcoin-workspaces'))
parser.add_argument('--finish-only',action='store_true',help='Resume comparisons from a completed, matching event cache without recomputing positions/models')
args=parser.parse_args()
run(args.source,args.output,args.workspaces,finish_only=args.finish_only)
