"""Prépare et lance les essais physiques Windows, sans inventer leur résultat.
Télécharge les agents officiels uniquement lorsqu'ils manquent, puis lance
ppilot5, notre application Ivy et sra5. Le résultat des essais est observé par
l'utilisateur (microphone, haut-parleurs et tracés).
"""

import argparse
import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
AGENTS = {
    "sra5": (
        "outils/sra5",
        "sra5.exe",
        "https://raw.githubusercontent.com/truillet/upssitech/master/SRI/5A/IHM/TP/Code/sra5.zip",
    ),
    "ppilot5": (
        "outils/ppilot5_3.3",
        "ppilot5.exe",
        "https://raw.githubusercontent.com/truillet/ivy/master/agents/ppilot5_3.3.zip",
    ),
}


def find_executable(folder, name):
    matches = sorted(
        p
        for p in folder.rglob("*")
        if p.is_file() and p.name.casefold() == name.casefold()
    )
    if len(matches) > 1:
        raise RuntimeError(
            f"Plusieurs {name} dans {folder}. Conserver une seule installation."
        )
    return matches[0] if matches else None


def extract_archive(archive, destination):
    """Refuse les chemins sortant du dossier et les liens symboliques."""
    root = destination.resolve()
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            target = (root / info.filename.replace("\\", "/")).resolve()
            if not target.is_relative_to(root) or stat.S_ISLNK(
                info.external_attr >> 16
            ):
                raise RuntimeError(
                    "Chemin non autorisé dans l’archive : " + info.filename
                )
        package.extractall(root)


def ensure_agent(folder, name, url, download):
    executable = find_executable(folder, name)
    if executable:
        return executable
    if not download:
        raise RuntimeError(
            f"{name} absent : dézipper le logiciel du cours dans {folder}."
        )
    print("Téléchargement depuis le dépôt officiel :", url, flush=True)
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fusion-agent-") as temporary:
        archive = Path(temporary) / "agent.zip"
        with urllib.request.urlopen(url, timeout=45) as response:
            archive.write_bytes(response.read())
        extract_archive(archive, folder)
    executable = find_executable(folder, name)
    if not executable:
        raise RuntimeError(
            f"{name} introuvable dans l’archive. Vérifier le téléchargement du cours."
        )
    return executable


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bus", default="127.255.255.255:2010")
    parser.add_argument("--sans-telechargement", action="store_true")
    parser.add_argument(
        "--verifier",
        action="store_true",
        help="Vérifier Python/Ivy et trouver les agents sans les lancer ni les télécharger",
    )
    args = parser.parse_args()
    if os.name != "nt":
        print("Les agents sra5 et ppilot5 doivent être lancés sur Windows.")
        return 1
    if importlib.util.find_spec("ivy") is None:
        print("Installer Ivy avec le même Python :")
        print(f'"{sys.executable}" -m pip install -r "{ROOT / "requirements.txt"}"')
        return 1
    grammar = ROOT / "src/simulateur_vocal/grammar.grxml"
    entrypoint = ROOT / "src/main.py"
    if not grammar.is_file() or not entrypoint.is_file():
        print(
            "Sources ou grammaire absentes. Récupérer le dépôt avec git pull --ff-only."
        )
        return 1
    try:
        paths = {}
        for key, (directory, name, url) in AGENTS.items():
            paths[key] = ensure_agent(
                ROOT / directory,
                name,
                url,
                not args.sans_telechargement and not args.verifier,
            )
            print(key + " : " + str(paths[key]))
        if args.verifier:
            print("Fichiers et dépendance trouvés; aucun essai physique effectué.")
            return 0
        print("Vérifier le microphone Windows et la disponibilité de SAPI français.")
        print(
            "Fermer les anciennes instances des agents et de la palette avant ce lancement."
        )
        print("Fermer la palette terminera les agents lancés par ce script.")
        children = []
        try:
            synth = subprocess.Popen(
                [str(paths["ppilot5"]), "-b", args.bus],
                cwd=paths["ppilot5"].parent,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            children.append(synth)
            application = subprocess.Popen(
                [sys.executable, str(entrypoint), "--ivy", "--bus", args.bus],
                cwd=ROOT,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            children.append(application)
            # Laisse les abonnements Ivy se découvrir avant de démarrer le micro.
            time.sleep(2)
            for process, name in [(synth, "ppilot5"), (application, "moteur")]:
                if process.poll() is not None:
                    raise RuntimeError(
                        name + " s’est arrêté. Lire sa fenêtre de lancement."
                    )
            speech = subprocess.Popen(
                [str(paths["sra5"]), "-b", args.bus, "-p", "off", "-g", str(grammar)],
                cwd=paths["sra5"].parent,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            children.append(speech)
            print("Agents démarrés. Suivre docs/essais_materiels.md.", flush=True)
            while application.poll() is None:
                if speech.poll() is not None or synth.poll() is not None:
                    raise RuntimeError(
                        "Un agent vocal s’est arrêté. Consulter sa fenêtre (SAPI, langue ou DLL)."
                    )
                time.sleep(0.25)
            return application.returncode
        finally:
            # Arrête seulement les processus créés par ce script.
            for process in reversed(children):
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
    except (RuntimeError, OSError, zipfile.BadZipFile) as exc:
        print("Lancement impossible :", exc)
        return 1
    except KeyboardInterrupt:
        print("Lancement arrêté.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
