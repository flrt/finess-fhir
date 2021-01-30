Fichier Finess en FHIR
===

Ce programme génère 1 fichier au format ndjson de ressources FHIR correspondant aux établissements du fichier finess

# Génération

A partir de l'extraction téléchargeable depuis data.gouv.fr, ici `etalab-cs1100507-stock-20210108-0427.csv` il est possible de produire tout ou partie des établissements.

Exemple en produisant 99999 établissements (lignes 300001 à 40000)


```
$ python3.8 main.py --finessfile=files/etalab-cs1100507-stock-20210108-0427.csv --outputdir=out --start=30001 --end=40000
$ wc -l out/etab30001-40000.ndjson
19998 out/etab30001-40000.ndjson

```

Chaque établissement est représenté par 

- une ressource Organization
- une ressource Location (faisant référence à son Organization).



# Generation totale

```
(venv) fred@spiff:~/dev/github/finess-fhir$ for f in out/*; do wc -l $f; done
20000 out/etab0-10000.ndjson
19998 out/etab10001-20000.ndjson
19998 out/etab20001-30000.ndjson
19998 out/etab30001-40000.ndjson
19997 out/etab40001-50000.ndjson
19998 out/etab50001-60000.ndjson
19995 out/etab60001-70000.ndjson
19993 out/etab70001-80000.ndjson
19998 out/etab80001-90000.ndjson
10682 out/etab90001-95541.ndjson
```

# License
[MIT](LICENSE) 
