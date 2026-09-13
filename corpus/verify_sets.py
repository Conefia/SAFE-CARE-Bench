#!/usr/bin/env python3
"""Verify the three corpus sets before ingestion.

Run from the repo root:  python corpus/verify_sets.py

Checks, in order:
  1. Every file listed in a set manifest exists in that set's docs/ directory.
  2. Every file's sha256 matches its manifest entry.
  3. Every document shared between sets is byte-identical across them.
  4. base_6doc matches the pinned corpus/manifest.json v0.2 exactly.
  5. Front matter parses, carries the required keys, and doc_id matches the filename.
  6. No scenario metadata or answer-key field appears in any document body.
  7. Reports the chunk count per set, which is what drives retrieval selectivity.

Chunking is on '##' headings, so the text between the front matter and the first
heading counts as its own chunk wherever a document has one.

Exit code 0 only if every check passes. Nothing is ingested until it does.
"""
import hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(ROOT, 'kb_sets')
PINNED = os.path.join(ROOT, 'manifest.json')
TOP_K = 5
REQUIRED = {'doc_id', 'title', 'publisher', 'source_url', 'retrieved_utc',
            'rights', 'fidelity', 'covers_scenarios'}
FORBIDDEN = ['hidden_ground_truth', 'escalation_expected', 'min_tier_expected_to_pass',
             'hard_fail', 'expected_agent_behaviors', 'failure_conditions']
fail = []


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def split(p):
    t = open(p, encoding='utf-8').read()
    m = re.match(r'^---\n(.*?)\n---\n', t, flags=re.S)
    return (m.group(1) if m else ''), t[m.end():] if m else t


def chunks(p):
    _, body = split(p)
    first = body.find('\n## ')
    lead = body[:first if first >= 0 else len(body)].strip()
    return len(re.findall(r'^## ', body, flags=re.M)) + (1 if lead else 0)


def header_keys(front):
    """Top-level keys without needing PyYAML."""
    return set(re.findall(r'^([A-Za-z_][A-Za-z0-9_]*):', front, flags=re.M))


seen = {}
rows = []

for setname in sorted(os.listdir(SETS)):
    sdir = os.path.join(SETS, setname)
    if not os.path.isdir(sdir):
        continue
    man = json.load(open(os.path.join(sdir, 'manifest.json')))
    n_chunks = 0
    for d in man['documents']:
        p = os.path.join(sdir, d['file'])
        name = os.path.basename(d['file'])
        if not os.path.exists(p):
            fail.append(f'{setname}: missing {name}')
            continue
        h = sha(p)
        if h != d['sha256']:
            fail.append(f'{setname}: {name} sha256 mismatch')
        if name in seen and seen[name][0] != h:
            fail.append(f'{name} differs between {seen[name][1]} and {setname} -- sets have drifted')
        seen.setdefault(name, (h, setname))

        front, body = split(p)
        missing = REQUIRED - header_keys(front)
        if missing:
            fail.append(f'{setname}: {name} front matter missing {sorted(missing)}')
        m = re.search(r'^doc_id:\s*(\S+)', front, flags=re.M)
        if not m or m.group(1) != name[:3]:
            fail.append(f'{setname}: {name} doc_id does not match filename')
        for term in FORBIDDEN:
            if term in body.lower():
                fail.append(f'{setname}: {name} body contains "{term}"')

        n_chunks += chunks(p)
    if man['document_count'] != len(man['documents']):
        fail.append(f'{setname}: document_count does not match the document list')
    rows.append((setname, len(man['documents']), n_chunks))

pin = json.load(open(PINNED))
base = os.path.join(SETS, 'base_6doc')
for d in pin['documents']:
    name = os.path.basename(d['file'])
    p = os.path.join(base, 'docs', name)
    if not os.path.exists(p) or sha(p) != d['sha256']:
        fail.append(f'base_6doc: {name} does not match the pinned v0.2 manifest')

print(f"{'set':<12}{'docs':>6}{'chunks':>8}{'top_k=%d returns' % TOP_K:>18}")
for s, n, c in sorted(rows, key=lambda r: r[1]):
    print(f'{s:<12}{n:>6}{c:>8}{TOP_K / c * 100:>17.1f}%')
print()

if fail:
    print('FAILED')
    for f in fail:
        print('  -', f)
    sys.exit(1)
print('All checks passed. Sets are consistent and the pinned base is untouched.')
