"""Point d'entrée CLI de l'application."""

import argparse
import tkinter as tk
from .application import Application


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ivy", action="store_true")
    parser.add_argument("--bus", default="127.255.255.255:2010")
    args = parser.parse_args()
    root = tk.Tk()
    try:
        Application(root, args.bus if args.ivy else None)
    except ImportError:
        root.destroy()
        raise SystemExit(
            "Installez ivy-python : py -3.15 -m pip install -r requirements.txt"
        )
    root.mainloop()


if __name__ == "__main__":
    main()
