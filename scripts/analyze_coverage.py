#!/usr/bin/env python3
"""Analyze test coverage and generate detailed report"""
import json
import sys

def main():
    try:
        with open('coverage.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("ERROR: coverage.json not found. Run tests with coverage first.")
        sys.exit(1)

    files = data['files']
    summary = data['totals']

    print('=' * 80)
    print('OVERALL COVERAGE SUMMARY')
    print('=' * 80)
    print(f'Total Statements: {summary["num_statements"]:,}')
    print(f'Covered: {summary["covered_lines"]:,}')
    print(f'Missing: {summary["missing_lines"]:,}')
    print(f'Coverage: {summary["percent_covered"]:.1f}%')
    print()

    print('=' * 80)
    print('COMPONENTS BY COVERAGE LEVEL')
    print('=' * 80)
    print()

    # Excellent coverage (>70%)
    print('EXCELLENT (>70%):')
    print('-' * 80)
    excellent = [
        (f.replace('src\\halcytone_content_generator\\', '').replace('src/halcytone_content_generator/', ''),
         files[f]['summary']['percent_covered'])
        for f in files
        if files[f]['summary']['percent_covered'] > 70
        and files[f]['summary']['num_statements'] > 10
    ]
    excellent.sort(key=lambda x: x[1], reverse=True)
    for name, cov in excellent[:15]:
        print(f'  {name:50} {cov:>5.1f}%')
    print()

    # Good coverage (50-70%)
    print('GOOD (50-70%):')
    print('-' * 80)
    good = [
        (f.replace('src\\halcytone_content_generator\\', '').replace('src/halcytone_content_generator/', ''),
         files[f]['summary']['percent_covered'])
        for f in files
        if 50 <= files[f]['summary']['percent_covered'] <= 70
        and files[f]['summary']['num_statements'] > 10
    ]
    good.sort(key=lambda x: x[1], reverse=True)
    for name, cov in good[:15]:
        print(f'  {name:50} {cov:>5.1f}%')
    print()

    # Needs improvement (<50%)
    print('NEEDS IMPROVEMENT (<50%):')
    print('-' * 80)
    poor = [
        (f.replace('src\\halcytone_content_generator\\', '').replace('src/halcytone_content_generator/', ''),
         files[f]['summary']['percent_covered'],
         files[f]['summary']['num_statements'])
        for f in files
        if files[f]['summary']['percent_covered'] < 50
        and files[f]['summary']['num_statements'] > 20
    ]
    poor.sort(key=lambda x: x[2], reverse=True)
    for name, cov, stmts in poor[:25]:
        print(f'  {name:50} {cov:>5.1f}% ({stmts:>4} stmts)')
    print()

    # Critical modules (0% coverage with >50 statements)
    print('CRITICAL - NO COVERAGE (0%):')
    print('-' * 80)
    critical = [
        (f.replace('src\\halcytone_content_generator\\', '').replace('src/halcytone_content_generator/', ''),
         files[f]['summary']['num_statements'])
        for f in files
        if files[f]['summary']['percent_covered'] == 0
        and files[f]['summary']['num_statements'] > 20
    ]
    critical.sort(key=lambda x: x[1], reverse=True)
    for name, stmts in critical[:10]:
        print(f'  {name:50} {stmts:>4} stmts')
    print()

if __name__ == '__main__':
    main()
