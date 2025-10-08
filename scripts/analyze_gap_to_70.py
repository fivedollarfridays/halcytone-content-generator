#!/usr/bin/env python3
"""Analyze which modules are closest to 70% coverage."""

import json
import os

# Load coverage data
with open('coverage.json') as f:
    data = json.load(f)

files = data['files']

# Filter modules in 50-69% range
good_modules = {
    k: v for k, v in files.items()
    if 50 <= v['summary']['percent_covered'] < 70
}

print("=" * 100)
print("MODULES IN 50-69% RANGE - CANDIDATES FOR 70% TARGET")
print("=" * 100)
print()
print(f"{'Module':<50} {'Current':<10} {'Statements':<15} {'Need for 70%'}")
print("-" * 100)

total_needed = 0

for path, info in sorted(good_modules.items(), key=lambda x: -x[1]['summary']['percent_covered']):
    filename = os.path.basename(path)
    total = info['summary']['num_statements']
    covered = info['summary']['covered_lines']
    pct = info['summary']['percent_covered']
    needed_for_70 = int(total * 0.7) - covered

    total_needed += max(0, needed_for_70)

    print(f"{filename:<50} {pct:5.1f}%     {covered:4}/{total:4} stmts     {needed_for_70:3} statements")

print("-" * 100)
print(f"Total statements needed to get all 50-69% modules to 70%: {total_needed}")
print()

# Calculate current overall coverage
overall_total = data['totals']['num_statements']
overall_covered = data['totals']['covered_lines']
overall_pct = data['totals']['percent_covered']

print(f"Current Overall Coverage: {overall_pct:.1f}% ({overall_covered}/{overall_total} statements)")
print(f"Target: 70% = {int(overall_total * 0.7)} statements")
print(f"Gap to 70%: {int(overall_total * 0.7) - overall_covered} statements needed")
print()

# Show quick wins (modules needing <10 statements to reach 70%)
print("=" * 100)
print("QUICK WINS (< 10 statements needed)")
print("=" * 100)
quick_wins = [(k, v) for k, v in good_modules.items() if int(v['summary']['num_statements'] * 0.7) - v['summary']['covered_lines'] < 10]
for path, info in sorted(quick_wins, key=lambda x: int(x[1]['summary']['num_statements'] * 0.7) - x[1]['summary']['covered_lines']):
    filename = os.path.basename(path)
    total = info['summary']['num_statements']
    covered = info['summary']['covered_lines']
    pct = info['summary']['percent_covered']
    needed = int(total * 0.7) - covered
    print(f"  • {filename}: {pct:.1f}% → 70% = {needed} statements needed")
