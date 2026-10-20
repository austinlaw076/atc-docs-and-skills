"""Deterministic protocol fixture. No model or research judgement is involved."""


def run(packet):
    e = packet['envelope']
    result = {k: e[k] for k in ('request_id', 'task_id', 'contract_hash', 'input_hash')}
    if e['role'] == 'worker':
        sid = next(iter(e['sources']))
        source = e['sources'][sid]
        line = next(i for i, text in enumerate(source['lines'], 1) if text.strip())
        quote = source['lines'][line - 1]
        result.update(claims=[{'id': 'C1', 'text': 'The pinned source contains this exact line: ' + quote,
            'requirement_refs': [e['task_id']], 'evidence': [{'source_id': sid,
            'source_sha256': source['sha256'], 'start_line': line, 'end_line': line, 'quote': quote}]}],
            limitations=['Deterministic fixture; not real model research or independent semantic review.'])
    else:
        checks = []
        for claim in e['artifact']['claims']:
            supported = bool(claim['evidence'])
            for evidence in claim['evidence']:
                source = e['sources'].get(evidence['source_id'], {})
                start, end = evidence['start_line'], evidence['end_line']
                expected = '\n'.join(source.get('lines', [])[start - 1:end])
                supported = supported and (evidence['quote'] == expected and
                    evidence['source_sha256'] == source.get('sha256') and
                    claim['text'] == 'The pinned source contains this exact line: ' + expected)
            checks.append({'claim_id': claim['id'], 'supported': bool(supported),
                'reason': 'Deterministic fixture checks literal containment only, not model judgement.'})
        satisfied = bool(checks) and all(c['supported'] for c in checks) and any(
            'fixture' in text for text in e['artifact']['limitations'])
        result.update(artifact_hash=e['artifact_hash'], verdict='accept' if satisfied else 'reject',
            acceptance_satisfied=satisfied, checks=checks,
            criteria=[{'criterion_id': c['id'], 'satisfied': satisfied,
                'claim_refs': [claim['id'] for claim in e['artifact']['claims']] if satisfied else [],
                'reason': 'Controlled fixture requires literal containment and explicit fixture provenance.'}
                for c in e['order']['criteria']], summary='Mechanical fixture review only; no model involved.')
    return result
