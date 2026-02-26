from enum import Enum
from typing import List, Dict, Any, Tuple
import numpy as np

class Merge_Type(Enum):
    Words = 1
    Wordcombinations = 2

# Rules for ending concat
valid_apostrophe_endings = {'s', 've', 'm', 't', 'd', 're', 'll', 'clock', 'mon', 'all', 'am'}

def sum_arrays(a: List[float], b: List[float]) -> List[float]:
    return list(np.add(a, b))

def merge_sequence(tokens: List[str], rows: List[List[float]], rules) -> Tuple[List[str], List[List[float]], List[List[Dict[str, Any]]]]:
    out_tokens = []
    out_rows = []
    orig_map = []

    i = 0
    while i < len(tokens):
        did_merge = False

        for rule in rules:
            n = rule['match'](tokens, i)
            if n > 0:
                if rule['name'] == 'prefix##':
                    prev = len(out_tokens) - 1
                    clean, combined_row = rule['merge'](tokens, rows, i)
                    out_tokens[prev] += clean
                    out_rows[prev] = sum_arrays(out_rows[prev], combined_row)
                    orig_map[prev].append({'token': tokens[i], 'attribution': rows[i]})
                else:
                    entries = [{'token': tokens[i + k], 'attribution': rows[i + k]} for k in range(n)]
                    clean, combined_row = rule['merge'](tokens, rows, i)
                    out_tokens.append(clean)
                    out_rows.append(combined_row)
                    orig_map.append(entries)
                    i += n - 1
                did_merge = True
                break

        if not did_merge:
            out_tokens.append(tokens[i])
            out_rows.append(rows[i])
            orig_map.append([{'token': tokens[i], 'attribution': rows[i]}])
        i += 1

    return out_tokens, out_rows, orig_map

# Merge rules
word_merge_rules = [
    {
        'name': 'prefix##',
        'match': lambda tokens, i: 1 if i > 0 and tokens[i].startswith('##') else 0,
        'merge': lambda tokens, rows, i: (tokens[i].lstrip('##'), rows[i])
    },
    {
        'name': 'suffix##',
        'match': lambda tokens, i: 2 if tokens[i].endswith('##') and i + 1 < len(tokens) else 0,
        'merge': lambda tokens, rows, i: (tokens[i].rstrip('##') + tokens[i + 1], sum_arrays(rows[i], rows[i + 1]))
    }
]

extra_merge_rules = [
    {
        'name': "'something-contraction",
        'match': lambda tokens, i: 3 if (
            i + 2 < len(tokens) and
            tokens[i + 1] == "'" and
            tokens[i + 2] in valid_apostrophe_endings
        ) else 0,
        'merge': lambda tokens, rows, i: (
            f"{tokens[i]}'{tokens[i + 2]}",
            sum_arrays(sum_arrays(rows[i], rows[i + 1]), rows[i + 2])
        )
    },
    {
        'name': 'trailing-punctuation',
        'match': lambda tokens, i: 2 if (
            i + 1 < len(tokens) and
            tokens[i].isalnum() and
            tokens[i + 1] in {'.', '!', '?'}
        ) else 0,
        'merge': lambda tokens, rows, i: (
            tokens[i] + tokens[i + 1],
            sum_arrays(rows[i], rows[i + 1])
        )
    }
]

 # Merge subword tokens in tokens_a and tokens_b with their attributions,
 
def rule_based_token_converter(input_data: Dict[str, Any], merge_mode: Merge_Type) -> Dict[str, Any]:
    tokens_a = input_data['tokens_a']
    tokens_b = input_data['tokens_b']
    attributions = input_data['attributions']

    # Copy for processing
    workA = tokens_a[:]
    workB = tokens_b[:]

    rules = []
    if merge_mode == Merge_Type.Words:
        rules = word_merge_rules
    elif merge_mode == Merge_Type.Wordcombinations:
        rules = word_merge_rules + extra_merge_rules

    mergedA, rowsA, mapA = merge_sequence(workA, attributions, rules)

    colsFromA = [[row[j] for row in rowsA] for j in range(len(tokens_b))]

    mergedB, colsB, mapB = merge_sequence(workB, colsFromA, rules)

    finalAttributions = [[col[i] for col in colsB] for i in range(len(rowsA))]

    # keep other fields that may be there
    extras = {
        k: v for k, v in input_data.items()
        if k not in {'tokens_a', 'tokens_b', 'attributions'}
    }

    return {
        'tokens_a': mergedA,
        'tokens_b': mergedB,
        'attributions': finalAttributions,
        'original_map_a': mapA,
        'original_map_b': mapB,
        'original_attributions': attributions,
        **extras
    }
