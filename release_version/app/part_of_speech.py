from typing import Dict, Any, List, Tuple
import spacy

# our attribution data texts are all english
nlp = spacy.load("en_core_web_sm")

def analyze_pos(input_data: Dict[str, Any]) -> Dict[str, Any]:
    def categorize_tokens(tokens: List[str]) -> List[Tuple[str, str]]:
        doc = nlp(" ".join(tokens))
        return [token.pos_ for token in doc]

    if "tokens_a" in input_data:
        input_data["tokens_a_categorized"] = categorize_tokens(input_data["tokens_a"])
    else:
        input_data["tokens_a_categorized"] = []

    if "tokens_b" in input_data:
        input_data["tokens_b_categorized"] = categorize_tokens(input_data["tokens_b"])
    else:
        input_data["tokens_b_categorized"] = []

    if "tokens" in input_data:
        input_data["tokens_categorized"] = categorize_tokens(input_data["tokens"])

    return input_data
