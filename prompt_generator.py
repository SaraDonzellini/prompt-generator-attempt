# region Copyright

'''Mad Prompt Generator'''
#========================#

""" This is a simple Python script that generates a number of random prompts. The script prompts the user for different style of combinations (random, combinatorial or both), the length desired and then generates a number of prompts decided before in a .txt file. If the user decides to create more prompts, the script will create another file .txt, numbering them in order. """

""" ## Features

- Generates random prompts based on a given dictionary.
- Supports combinatorial generation of prompts.
- Outputs prompts to a .txt file.
- Allows for multiple runs, numbering output files sequentially. """

""" ## Installation

To use this script, you need to have Python 
It needs a .json "dictionary", three files (themes) are provided. If the user wants can import a customized one. """

""" ## Requirements

- Python 3.x """

""" ## Usage

1. Clone the repository or download the script. """


# Copyright (C) <2025>  Sara Donzellini
# email: sara.donzie@gmail.com
# github: https://github.com/saradonzellini

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.





# region Program
# version 0.1.0

import json
import os
import random
import itertools
import argparse
import sys
import subprocess
from typing import List, Dict
import re


# --- Utility ---
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


def load_parts(filename: str, path: list = None) -> Dict[str, List[str]]:
    """Carica una sottostruttura del JSON e appiattisce eventuali sottocategorie ricorsivamente."""
    def flatten_dict(d):
        flat = {}
        for k, v in d.items():
            if isinstance(v, list) and v:
                flat[k] = v
            elif isinstance(v, dict):
                # Unisci tutte le sottoliste in una sola lista sotto la chiave principale
                merged = []
                for subv in v.values():
                    if isinstance(subv, list):
                        merged.extend(subv)
                if merged:
                    flat[k] = merged
                # Mantieni anche le chiavi secondarie come prima (opzionale)
                for subk, subv in v.items():
                    if isinstance(subv, list) and subv:
                        flat[f"{k}_{subk}"] = subv
        return flat

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        if path:
            for key in path:
                data = data[key]
        flat_parts = flatten_dict(data)
        # DEBUG: stampa le chiavi per capire cosa c'è
        # if __name__ == "__main__":
            # print("DEBUG: chiavi parts:", list(flat_parts.keys()))
            
        if not flat_parts:
            raise ValueError("Nessuna lista valida trovata nel JSON.")
        return flat_parts
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"ERRORE: {e}", file=sys.stderr)
        return {}
    
def get_next_output_filename(base: str = "invoke_prompts", outdir: str = "") -> str:
    """
    Restituisce il prossimo nome file disponibile in formato invoke_prompts_001.txt, _002.txt, ecc.
    Se outdir è specificato, salva nella cartella indicata.
    """
    i = 1
    while True:
        fname = f"{base}_{i:03d}.txt"
        fullpath = os.path.join(outdir, fname) if outdir else fname
        if not os.path.exists(fullpath):
            return fullpath
        i += 1

def write_prompts(prompts: List[str], filename: str):
    try:
        outdir = os.path.dirname(filename)
        if outdir and not os.path.exists(outdir):
            os.makedirs(outdir)
            
        with open(filename, "w", encoding="utf-8") as f:
            for p in prompts:
                # Applica correzioni finali
                corrected = apply_grammar_rules(p)
                if p == prompts[-1]:
                    f.write(f"{corrected}")
                else:
                    f.write(f"{corrected}" + "\n_\n")
        print(f"✅ Generati {len(prompts)} prompt in {filename}")
    except Exception as e:
        print(f"ERRORE durante scrittura file: {e}", file=sys.stderr)

# --- Generazione prompt ---

def generate_random(parts: Dict[str, List[str]], n: int) -> List[str]:
    """
    Genera n prompt random, ciascuno lungo tra 10 e 20 parole, scegliendo parole casuali dalle categorie disponibili.
    """
    prompts = []
    keys = list(parts.keys())
    for _ in range(n):
        length = random.randint(10, 20)
        prompt = " ".join(random.choice(parts[random.choice(keys)]) for _ in range(length))
        prompts.append(prompt)
    return prompts

def generate_combinatorial(parts: Dict[str, List[str]]) -> List[str]:
    combos = itertools.product(*(parts[k] for k in parts))
    return [" ".join(c) for c in combos]

def create_both_prompts(args, parts):
    result = []
    half = args.num_prompts // 2
    result.extend(generate_random(parts, half))
    # Per la metà restante, usa ordine standard custom
    default_order = ["art", "noun", "conj", "art", "adj", "verb", "adv", "adj", "conj", "adj"]
    custom_order = args.custom_order.split(",") if args.custom_order else default_order
    custom_order = [part.strip() for part in custom_order if part.strip()] or use_every_category(args)
    return result
# --- Argparse ---

def parse_args():
    parser = argparse.ArgumentParser(description="Generatore di prompt combinatori, casuali o custom da file JSON.")
    parser.add_argument("-i", "--input", default="prompt_parts.json", help="File JSON di input")
    parser.add_argument("-o", "--output", default="invoke_prompts.txt", help="File di output")
    parser.add_argument("-m", "--mode", choices=["ran", "comb", "both"], default="ran", help="Modalità di generazione")
    parser.add_argument("-n", "--num-prompts", type=int, default=10, help="Numero di prompt da generare")
    parser.add_argument("-c", "--comma", type=str, help="Virgola")
    parser.add_argument("-art", "--articles", type=str, help="Articoli da usare nei prompt")
    parser.add_argument("-adj", "--adjectives", type=str, help="Aggettivi da usare nei prompt")
    parser.add_argument("-noun", "--nouns", type=str, help="Sostantivi da usare nei prompt")
    parser.add_argument("-prep", "--prepositions", type=str, help="Preposizioni da usare nei prompt")
    parser.add_argument("-pron", "--pronouns", type=str, help="Pronomi da usare nei prompt")
    parser.add_argument("-conj", "--conjunctions", type=str, help="Congiunzioni da usare nei prompt")
    parser.add_argument("-verb", "--verbs", type=str, help="Verbi da usare nei prompt")
    parser.add_argument("-adv", "--adverbs", type=str, help="Avverbi da usare nei prompt")
    parser.add_argument("-sty", "--styles", type=str, help="Stili da usare nei prompt")
    parser.add_argument("-light", "--dramatic-lighting", type=str, help="Illuminazione drammatica da usare nei prompt")
    parser.add_argument("-tones", "--color-tones", type=str, help="Toni di colore da usare nei prompt")
    # Rimosso --custom-order perché la modalità custom non è più supportata
    parser.add_argument("--long", "--long-forms", action="store_true", help="Usa forme lunghe dei prompt")
    parser.add_argument("--short", "--short-forms", action="store_true", help="Usa forme corte dei prompt")

    return parser.parse_args()

# --- NUOVE FUNZIONI PER GRAMMATICA ---
def generate_grammatical_phrase(parts: Dict[str, List[str]], template: str) -> str:
    """
    Genera una frase basata su un template grammaticale, scegliendo singolare o plurale coerente.
    Sostituisce tutti i placeholder {Categoria} con una parola casuale dalla categoria corrispondente.
    Se una categoria non esiste, rimuove il placeholder.
    """
    # Scegli una volta se usare singolare o plurale per tutto il prompt (per coerenza)
    use_plural = random.choice([True, False])

    def get_word(category):
        # Gestione Nouns/Verbs generici
        if category == "Nouns":
            key = "Nouns_plural" if use_plural else "Nouns_singular"
        elif category == "Verbs":
            key = "Verbs_plural" if use_plural else "Verbs_singular"
        else:
            key = category
        # Se la categoria esiste, restituisci una parola casuale
        if key in parts and isinstance(parts[key], list) and parts[key]:
            return random.choice(parts[key])
        # Prova a trovare la versione base (es: Nouns_singular -> Nouns)
        base_cat = re.sub(r'_(singular|plural)$', '', key)
        if base_cat in parts and isinstance(parts[base_cat], list) and parts[base_cat]:
            return random.choice(parts[base_cat])
        # Se non trovato, rimuovi il placeholder
        print(f"⚠️ Categoria '{category}' non trovata o vuota!")
        return ""

    # Sostituisci tutti i placeholder nel template
    phrase = template
    while True:
        match = re.search(r"\{(\w+)\}", phrase)
        if not match:
            break
        category = match[1]
        word = get_word(category)
        phrase = phrase.replace(match[0], word, 1)
    # Rimuovi eventuali doppie spaziature dovute a placeholder vuoti
    phrase = re.sub(r'\s+', ' ', phrase).strip()
    return phrase

def apply_grammar_rules(phrase: str) -> str:
    """Applica correzioni grammaticali automatiche"""
    # Accordi articolo-sostantivo
    phrase = re.sub(r"\ba ([aeiouAEIOUaeiou])", r"an \1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\ban ([^aeiouAEIOU])", r"a \1", phrase)
    
    # Accordi verbo-soggetto
    phrase = re.sub(r"\b(he|she|it|this|that) (are|have)\b", r"\1 \2s", phrase)
    phrase = re.sub(r"\b(they|we|you|these|those) (is|has)\b", r"\1 are", phrase)
    
    # Forme verbali contraffe
    # phrase = phrase.replace(" is ", "'s ").replace(" are ", "'re ")
    
    return phrase
# --- Main ---

def use_every_category(args):
    # Se non specificato, usa tutte le categorie almeno una volta in ordine standard
    result = []
    if args.articles:
        result.append("art")
    if args.adjectives:
        result.append("adj")
    if args.pronouns:
        result.append("pron")
    if args.nouns:
        result.append("noun")
    if args.prepositions:
        result.append("prep")
    if args.adverbs:
        result.append("adv")
    if args.verbs:
        result.append("verb")
    if args.conjunctions:
        result.append("conj")
    if args.styles:
        result.append("sty")
    if args.dramatic_lighting:
        result.append("light")
    if args.color_tones:
        result.append("tones")
        
    if not result:
        result = ["pron", "noun", "conj", "art", "adj", "verb", "adv", "adj", "conj", "adj", ";", "sty", "light", "tones"]

    return result

def main(args=None):
    if args is None:
        args = parse_args()
    
    # Controllo aggiuntivo per prevenire errori
    if not hasattr(args, 'custom_order'):
        args.custom_order = None
    if not hasattr(args, 'short'):
        args.short = False
    if not hasattr(args, 'long'):
        args.long = False

    # Carica tutte le parti dal JSON
    parts = {}
    for path in [
        ["prompt_dictionary", "Dictionary"],
        ["prompt_dictionary", "Situations"]
    ]:
        subparts = load_parts(args.input, path=path)
        parts.update(subparts)

    # print("DEBUG: chiavi parts:", list(parts.keys()))

    # Fallback: se mancano Nouns_singular/plural o Verbs_singular/plural, cerca di crearli
    if "Nouns_singular" not in parts and "Nouns" in parts:
        parts["Nouns_singular"] = parts["Nouns"]
    if "Nouns_plural" not in parts and "Nouns" in parts:
        parts["Nouns_plural"] = parts["Nouns"]
    if "Verbs_singular" not in parts and "Verbs" in parts:
        parts["Verbs_singular"] = parts["Verbs"]
    if "Verbs_plural" not in parts and "Verbs" in parts:
        parts["Verbs_plural"] = parts["Verbs"]
    
    # Alias automatici per Nouns e Verbs (unione di singolare e plurale)
    if "Nouns_singular" in parts and "Nouns_plural" in parts:
        parts["Nouns"] = parts["Nouns_singular"] + parts["Nouns_plural"]
    if "Verbs_singular" in parts and "Verbs_plural" in parts:
        parts["Verbs"] = parts["Verbs_singular"] + parts["Verbs_plural"]
    # Aggiungi le categorie specificate dagli argomenti


    # --- Custom prompt order parsing ---
    if args.mode in ("ran", "comb", "both"):
        prompts = generate_with_patterns(args, parts)
    else:
        # fallback: random
        prompts = generate_random(parts, args.num_prompts)
    write_prompts(prompts, args.output)

def generate_with_patterns(args, parts):
    # Carica i patterns
    patterns_short = load_patterns(args.input, "Patterns_short")
    patterns_long = load_patterns(args.input, "Patterns_long")

    prompts = []
    use_short = getattr(args, "short", False)
    use_long = getattr(args, "long", False)

    if (use_short and use_long) or (not use_short and not use_long):
        half = args.num_prompts // 2
        if not patterns_short and not patterns_long:
            raise ValueError("❌ Nessun pattern corto o lungo trovato nel file JSON. Controlla il file e riprova.")
        if patterns_short:
            for _ in range(half):
                short = random.choice(patterns_short)
                prompt = generate_grammatical_phrase(parts, short)
                prompts.append(apply_grammar_rules(prompt))
        if patterns_long:
            for _ in range(args.num_prompts - half):
                long = random.choice(patterns_long)
                prompt = generate_grammatical_phrase(parts, long)
                prompts.append(apply_grammar_rules(prompt))
    elif use_short and patterns_short:
        for _ in range(args.num_prompts):
            short = random.choice(patterns_short)
            prompt = generate_grammatical_phrase(parts, short)
            prompts.append(apply_grammar_rules(prompt))
    elif use_long and patterns_long:
        for _ in range(args.num_prompts):
            long = random.choice(patterns_long)
            prompt = generate_grammatical_phrase(parts, long)
            prompts.append(apply_grammar_rules(prompt))
    elif use_long:
        raise ValueError("❌ Nessun pattern lungo trovato nel file JSON. Controlla il file e riprova.")
    else:
        raise ValueError("❌ Nessun pattern corto trovato nel file JSON. Controlla il file e riprova.")
    return prompts

def load_patterns(filename, key):
    """
    Carica una lista di pattern (corti o lunghi) dal file JSON.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Cerca sia a livello root che in "prompt_dictionary"
        result = data.get(key, [])
        if not result and "prompt_dictionary" in data:
            result = data["prompt_dictionary"].get(key, [])
        return result
    except Exception as e:
        print(f"ERRORE nel caricamento dei patterns: {e}", file=sys.stderr)
        return []


# Funzione custom_order_args rimossa perché la modalità custom non è più supportata

def interactive_menu():
    print("🔮=== Prompt Generator un po' pazzo ===🔮")
    print("Benvenuto nel generatore di prompt, che sono in inglese. Metà programma è scritto in italiano ma non farci caso.")
    print("Il generatore ti darà delle modalità da scegliere: Random, Combinatorial e Both(circa metà e metà)\nDopo, ti chiederà quali pattern vuoi usare. Nel file JSON associato sono già presenti dei pattern ovviamente, ma se vuoi aggiungerne, sentiti liber*.\nUn esempio di pattern (corto):\n'The (Adjectives) (Nouns_singular) (Verbs_singular) through (Adjectives) (Nouns_plural), (Verbs_singular) (Adjectives) (Nouns_plural) across the (Adjectives) (Nouns_singular).'\nL'unica differenza è che dovrai usare le parentesi graffe e non le tonde, io non potevo nell'esempio o Python mi picchiava con un mattone.")
    print("Beh, che dire, divertiti. Le opzioni sono abbastanza chiare (spero).")
    print("Auguro divertimento a tutt*,\n la vostra amichevole Strega del Web,\n    WitchRinnie.🔮")
    last_outfile = ""
    outdir = input("Cartella di output (invio per la cartella corrente): ").strip()
    while True:
        # Ciclo per scelta modalità valida o uscita con easter egg
        while True:
            mode = input("Scegli la modalità: ran (random) / comb (combinatorial) / both (random+combinatorial) [default: ran, oppure scrivi 'exit' per uscire]: ") or "ran"
            mode = mode.strip().lower()
            if mode == "exit":
                print("Arrivederci, torna presto!🔮")
                print(f"Ultimo file generato: {last_outfile}")
                sys.exit(0)
            if mode == "nomariaioesco":
                print("Lo sapevo che ci avresti provato.🧙‍♀️")
                input("Premi Invio per continuare oppure scrivi exit, scemott*")
                continue
            if mode in ["scemott*", "scemott"]:
                print("\n(╮°-°)╮┳━━┳ \n( ╯°□°)╯ ┻━━┻\n<(￣ ﹌ ￣)>\n┬─┬ノ( º _ ºノ)")
                print("Non sono una scemott*, ma grazie lo stesso.🧙‍♀️")
                input("Indovina:")
                continue
            if mode in ["ran", "comb", "both"]:
                break
            input("Modalità non valida! Scegli tra: ran, comb, both oppure scrivi 'exit' per uscire.")
            
        num = input("Quanti prompt vuoi generare? [default: 10]: ") or "10"
        infile_input = input("Nome file input; default: [prompt_parts.json]: ") or "prompt_parts.json"
        outfile_input = input("Nome file output (invio per auto-nome): ")

        if not os.path.exists(infile_input):
            print(f"ATTENZIONE: Il file di input '{infile_input}' non esiste!")
            continue
        if infile_input:
            if not infile_input.lower().endswith(".json"):
                infile_input += ".json"
            infile = os.path.join(outdir, infile_input) if outdir else infile_input
        if outfile_input:
            outfile = f"{outfile_input}.txt"
            outfile = os.path.join(outdir, outfile) if outdir else outfile
        else:
            outfile = get_next_output_filename(outdir=outdir)

        last_outfile = outfile

        class FakeArgs:
            pass

        fake_args = FakeArgs()

        # --- ATTRIBUTI OBBLIGATORI ---
        fake_args.mode = mode
        fake_args.num_prompts = int(num)
        fake_args.input = infile
        fake_args.output = outfile
        fake_args.comma = ","

        # --- ATTRIBUTI PER PATTERN ---
        fake_args.short = False
        fake_args.long = False

        # --- ATTRIBUTI PER CATEGORIE (PREVENZIONE ERRORI) ---
        fake_args.articles = None
        fake_args.adjectives = None
        fake_args.nouns = None
        fake_args.prepositions = None
        fake_args.pronouns = None
        fake_args.conjunctions = None
        fake_args.verbs = None
        fake_args.adverbs = None
        fake_args.styles = None
        fake_args.dramatic_lighting = None
        fake_args.color_tones = None
        fake_args.custom_order = None  # IMPORTANTE!

        # Gestione pattern choice SOLO per modalità compatibili
        if mode in ["ran", "comb", "both"]:
            print("Vuoi usare patterns lunghi, corti o entrambi?")
            print("Digita 'l' per lunghi, 's' per corti, 'b' per entrambi [default: b]:")
            pattern_choice = input().strip().lower() or "b"

            if pattern_choice == "l":
                fake_args.long = True
            elif pattern_choice == "s":
                fake_args.short = True
            elif pattern_choice == "b":
                fake_args.short = True
                fake_args.long = True

        # Rimosso blocco gestione CUSTOM ORDER perché la modalità custom non è più supportata


        # SINGOLA CHIAMATA a main
        try:
            main(fake_args)  # Passa l'oggetto fake_args
        except Exception as e:
            print(f"ERRORE durante la generazione: {e}")
        print("...")
        print(f"\nPrompt generati e salvati in: {outfile}")
        print("\nBatch completato. Premi invio per continuare o 'n' per uscire.")
        if not should_continue():
            print(f"Ultimo file generato: {last_outfile}")
            print("Arrivederci, torna presto!🔮")
            break

def should_continue():
    """
    Chiede all'utente se vuole generare un altro batch.
    Ritorna True per continuare, False per uscire.
    """
    again = input("\nVuoi generare un altro batch? (invio per sì, n per no): ")
    return again.strip().lower() != "n"

def run_program():
    """
    Avvia il programma: se non ci sono argomenti, mostra il menu interattivo, altrimenti esegue la generazione.
    Gestisce eventuali errori fatali.
    """
    try:
        if len(sys.argv) == 1:
            interactive_menu()
        else:
            main()
    except Exception as e:
        print(f"ERRORE FATALE: {e}")
        input("Premi invio per uscire...")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        run_program()