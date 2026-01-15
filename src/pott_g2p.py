
import json
import re
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from dataclasses import dataclass

try:
    from src.romanization import split_syllable_church
    from src.rule_induction import PhoneticFeatures, INITIAL_FEATURES, FINAL_FEATURES
except ImportError:
    # Fallback for standalone usage
    pass

# ==============================================================================
# Pott (Church Romanization) to IPA Conversion Rules
# Based on "Key to the Pronunciation" in preliminary.typ
# ==============================================================================

# IPA Symbols
IPA_HIGH_LEVEL = "˥"  # 55
IPA_LOW_DEPRESSOR = "̤" # Breath/slack voice indicator

# Initials Mapping
# Longest match first
INITIALS_MAP = {
    # Aspirated (High)
    "tsh": "tsʰ",
    "kwh": "kʷʰ",
    "ph": "pʰ",
    "th": "tʰ",
    "ch": "tɕʰ", 
    "kh": "kʰ",
    "hy": "ɕ",  # "ti" in Portia
    "hw": "hw", # ?
    "h": "h",
    "f": "f",
    
    # Unaspirated (High)
    "'v": "f",  # "High pitched ... 'v", distinct from low "v". Likely [f] or [v] (high tone). Mapping to f for now given 'f' is listed as aspirate.
    "kw": "kʷ",
    "ky": "tɕ",
    "ts": "ts",
    "ny": "ɲ",
    "ng": "ŋ",
    "p": "p",
    "m": "m",
    "t": "t",
    "l": "l",
    "n": "n",
    "k": "k",
    "w": "w",
    
    # Voiced/Sad (Low)
    # These usually trigger lower register pitch
    "dz": "dz",
    "gw": "ɡʷ",
    "ng": "ŋ", # Can be low
    "ny": "ɲ", # Can be low
    "b": "b",
    "m": "m",
    "v": "v",
    "d": "d",
    "z": "z",
    "l": "l",
    "j": "dʑ",
    "g": "ɡ",
    "r": "z", # "approx final r or l" - usually [z] or [ʐ] in Shanghai
    
    # Others
    "sh": "ɕ", # Assuming standard mapping if used
    "s": "s",
    "y": "j", # "i" in dahlia
    
    # Null initial
    "": "",
}

# Finals Mapping
# Longest match first
FINALS_MAP = {
    # Glottal stops (Ru sheng)
    "iak": "iaʔ",
    "iah": "iaʔ",
    "oeh": "øʔ", # or ø
    "auh": "ɔʔ",
    "ak": "aʔ", # "a" in what (Book says ah=at, ak=what). 'what' is [ɒ] or [ɔ]. 'at' is [æ]. 
    "ah": "aʔ", # "a in at"
    "eh": "əʔ", # "e in let" -> [ɛ]? Usually 'eh' is [əʔ] or [ɛʔ].
    "ih": "iʔ",
    "ok": "oʔ",
    "oh": "oʔ",
    "uh": "uʔ", # or oʔ
    
    # Nasals
    "aung": "ɑ̃", # "ng in song" + a? "a in far". [ɑ̃]?
    "oong": "uŋ", # "oo"+"ng". Book: "o" in bone. [oŋ].
    "iang": "iɑ̃",
    "ung": "oŋ",
    "ang": "ɑ̃", # "a in far".
    "oen": "ø̃",
    "ien": "iən",
    "en": "ən",
    "an": "ɛ", # "a in and".
    "in": "in",
    
    # Vowels
    "ieu": "iø",
    "iau": "iɔ",
    "oo": "u", # "oo in too"
    "oe": "ø", # German ö
    "eu": "ø", # French eu
    "ui": "y", # "ui in fruit" (French?) or [u]? Shanghai 'ui' -> [y] often.
    "au": "ɔ", # "au in August"
    "ua": "uo", 
    "ue": "y",
    "uo": "uo",
    "ia": "ia", # "short i as in it" -> [I]? + a. [ia].
    "ie": "i", # "short i as in it"? Book says "ie ... we have short sound of i". 
    "io": "io",
    "iu": "y", 
    "ai": "e", # Not in book list?
    "ei": "e",
    "oi": "ø",
    "a": "ɑ", # "a in far"
    "e": "e", # "e in prey"
    "o": "o", # "o in so"
    "i": "i",
    "u": "ʊ", # "oo in foot"
    
    # Syllabic consonants
    "m": "m̩",
    "ng": "ŋ̍",
    "r": "z̩",
    "z": "z̩", # "ts, tsh, s, dz, m, ng, r" are syllabic
}

# Special cases for 'i' (After dental sibilants, 'i' becomes apical [z̩] or [ɿ])
APICAL_INITIALS = {"ts", "tsh", "s", "z", "dz"}

@dataclass
class TransformationRule:
    source: str
    target: str
    count: int
    rule_type: str

class PottToIPA:
    """
    Converter for Pott (Church) Romanization to IPA for Shanghai Dialect.
    Enhanced to use learned phonetic rules for bridging to modern Wugniu Pinyin.
    """
    
    def __init__(self):
        # Sort keys by length descending for greedy matching
        self.sorted_initials = sorted(INITIALS_MAP.keys(), key=len, reverse=True)
        self.sorted_finals = sorted(FINALS_MAP.keys(), key=len, reverse=True)
        
        # Load learned rules
        self.learned_initials: List[TransformationRule] = []
        self.learned_finals: List[TransformationRule] = []
        self._load_learned_rules()

    def _load_learned_rules(self):
        """Load learned rules from .agent/data/phonetic_rules.json"""
        json_path = Path(__file__).parent.parent / ".agent/data/phonetic_rules.json"
        if not json_path.exists():
            return
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for r in data.get('initial_rules', []):
                self.learned_initials.append(TransformationRule(
                    source=r['source'],
                    target=r['target'],
                    count=r['count'],
                    rule_type='initial'
                ))
                
            for r in data.get('final_rules', []):
                self.learned_finals.append(TransformationRule(
                    source=r['source'],
                    target=r['target'],
                    count=r['count'],
                    rule_type='final'
                ))
        except Exception as e:
            print(f"Warning: Failed to load phonetic rules: {e}")

    def parse_syllable(self, text: str) -> Tuple[str, str, str]:
        """
        Parse a syllable into (initial, final, tone_marker)
        """
        text = text.lower().strip(" .?,!")
        
        # Handle initial low tone marker ' (e.g., 'a)
        tone_marker = ""
        if text.startswith("'") and len(text) > 1 and text[1] not in "v": 
             tone_marker = "'"
             text = text[1:]
        
        initial = ""
        final = text
        
        for init in self.sorted_initials:
            if text.startswith(init) and init != "":
                initial = init
                final = text[len(init):]
                break
        
        return initial, final, tone_marker

    def predict_modern_wugniu(self, initial: str, final: str) -> Tuple[str, float]:
        """
        Predict the modern Wugniu spelling based on learned rules.
        Returns (wugniu_syllable, confidence)
        """
        # Find best initial match
        best_init = initial # Default to same if no rule
        init_conf = 0.5
        
        matching_inits = [r for r in self.learned_initials if r.source == initial]
        if matching_inits:
            # Pick most frequent
            best_rule = max(matching_inits, key=lambda x: x.count)
            best_init = best_rule.target
            init_conf = min(1.0, best_rule.count / 50) # Heuristic confidence
            
        # Find best final match
        best_final = final
        final_conf = 0.5
        
        matching_finals = [r for r in self.learned_finals if r.source == final]
        if matching_finals:
            best_rule = max(matching_finals, key=lambda x: x.count)
            best_final = best_rule.target
            final_conf = min(1.0, best_rule.count / 50)
            
        return f"{best_init}{best_final}", (init_conf + final_conf) / 2

    def convert_syllable(self, text: str) -> Tuple[str, str, float]:
        """
        Convert a single syllable.
        Returns (IPA, Wugniu_Prediction, Confidence)
        """
        initial, final, tone_marker = self.parse_syllable(text)
        
        # IPA Conversion
        ipa_initial = INITIALS_MAP.get(initial, initial)
        ipa_final = FINALS_MAP.get(final, final)
        
        if initial in APICAL_INITIALS and ipa_final == "i":
            ipa_final = "z̩"
            
        ipa = f"{ipa_initial}{ipa_final}"
        
        # Wugniu Prediction
        wugniu, conf = self.predict_modern_wugniu(initial, final)
        
        return ipa, wugniu, conf

    def convert_phrase(self, text: str) -> List[Dict]:
        """
        Convert a phrase or sentence.
        Returns detailed list of dicts.
        """
        tokens = re.split(r'([ -])', text)
        result = []
        for token in tokens:
            if token.strip() and token not in "- ":
                ipa, wugniu, conf = self.convert_syllable(token)
                result.append({
                    "original": token,
                    "ipa": ipa,
                    "wugniu": wugniu,
                    "confidence": conf
                })
            elif token.strip(): # Punctuation/Spaces
                result.append({"text": token})
        return result

def test():
    converter = PottToIPA()
    test_cases = [
        "ngoo", "tshang", "nyih", "kuh"
    ]
    
    print("Testing Pott -> IPA conversion with Modern Prediction:")
    for pott in test_cases:
        ipa, wugniu, conf = converter.convert_syllable(pott)
        print(f"{pott:10} -> IPA: {ipa:10} | Modern (Wugniu): {wugniu:10} (Conf: {conf:.2f})")

if __name__ == "__main__":
    test()
