#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""

__author__ = "Frederic Laurent"
__version__ = "1.0"
__copyright__ = "Copyright 2021, Frederic Laurent"
__license__ = "MIT"

import argparse
import generator
import logging
import warnings


def main():
    """
        Programme principal

        - parse les arguments
        - lance les traitements
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--start", help="position de debut")
    parser.add_argument("--end", help="position de fin")
    parser.add_argument("--finessfile", help="Fichier Finess des établissements")
    parser.add_argument(
        "--outputdir",
        help="Repertoire de destination des fichiers générés",
        default="output",
    )
    args = parser.parse_args()

    gen = generator.etab()
    gen.load_data(args.finessfile)
    gen.generate(args.outputdir, args.start, args.end)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    warnings.simplefilter("ignore")
    main()
