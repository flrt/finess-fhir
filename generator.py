import logging
import pandas
import os.path
import re
import io
import codecs
import sys
import pprint
from pyproj import Proj, transform

from fhir.resources.organization import Organization
from fhir.resources.address import Address
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.location import Location

FINESS_KEYS = [
    "structureet",
    "nofinesset",
    "nofinessej",
    "rs",
    "rslongue",
    "complrs",
    "compldistrib",
    "numvoie",
    "typvoie",
    "voie",
    "compvoie",
    "lieuditbp",
    "commune",
    "departement",
    "libdepartement",
    "ligneacheminement",
    "telephone",
    "telecopie",
    "categetab",
    "libcategetab",
    "categagretab",
    "libcategagretab",
    "siret",
    "codeape",
    "codemft",
    "libmft",
    "codesph",
    "libsph",
    "dateouv",
    "dateautor",
    "datemaj",
    "numuai",
]
GEOFINESS_KEYS = [
    "geolocalisation",
    "nofinesset",
    "coordxet",
    "coordyet",
    "sourcecoordet",
    "datemaj",
]

pp = pprint.PrettyPrinter()


# https://www.data.gouv.fr/fr/datasets/finess-extraction-du-fichier-des-etablissements/

class Etab:
    def __init__(self):
        self.logger = logging.getLogger()
        self.df_finess = []
        self.df_finess_geo = None
        self.finess_geo = {}

    def load_data(self, etalab_filename):
        """
            lecture fichiers finess
        :param etalab_filename: Fichier des finess
        :return: -

        """

        self.logger.info(f"Loading data from {etalab_filename}")
        with codecs.open(etalab_filename, "r", "iso-8859-1") as fin:
            for line in fin:
                if line.startswith("structureet"):
                    self.df_finess.append(dict(zip(FINESS_KEYS, line.split(';'))))
                if line.startswith("geolocalisation"):
                    parts = line.split(';')
                    self.finess_geo[parts[1]] = (parts[2], parts[3])

        self.logger.info(f'Finess : {len(self.df_finess)}')
        self.logger.info(f'Geo : {len(self.finess_geo)}')

    def load_data_pandas(self, etalab_filename):
        """
            lecture fichiers finess
        :param etalab_filename: Fichier des finess
        :return: -

        """

        self.logger.info(f"Loading data from {etalab_filename}")

        # lecture fichier etalab
        finess = io.StringIO()
        finess.write(f"{';'.join(GEOFINESS_KEYS)}\n")
        finess_geo = io.StringIO()
        finess_geo.write(f"{';'.join(GEOFINESS_KEYS)}\n")

        with codecs.open(etalab_filename, "r", "iso-8859-1") as fin:
            for line in fin:
                if line.startswith("structureet"):
                    finess.write(line)
                if line.startswith("geolocalisation"):
                    finess_geo.write(line)

        self.logger.info(finess.tell())
        finess.seek(0)
        finess_geo.seek(0)

        self.df_finess = pandas.read_csv(
            finess,
            delimiter=";",
            names=FINESS_KEYS,
            header=0,
            index_col=False,
            dtype=str,
        )
        self.df_finess_geo = pandas.read_csv(
            finess_geo,
            delimiter=";",
            names=GEOFINESS_KEYS,
            header=0,
            index_col=False,
        )

    @staticmethod
    def convert_coordinates(xin, yin, proj):
        if proj == "LAMBERT_93":
            in_proj = Proj(init="epsg:2154")
            out_proj = Proj(init="epsg:4326")
            xout, yout = transform(in_proj, out_proj, xin, yin)
        else:
            xout, yout = xin, yin
        return xout, yout

    def generate_pandas(self, ndoutput):
        self.logger.info(len(self.df_finess))

        with open(ndoutput, "w") as fout:
            # Timone : self.df_finess[self.df_finess.nofinesset == '130783293']
            for index, row in self.df_finess.iterrows():
                eg_id = "%s-%s" % (str(row.nofinesset).strip(), index)
                self.logger.info(f"Etab geo {eg_id} - {row.libcategetab} [{row.rs}]")
                self.logger.info(f"date     {row.datemaj}")

                line_vals = []
                if str(row.numvoie) != "nan":
                    line_vals.append(str(row.numvoie))
                if row.typvoie:
                    line_vals.append(str(row.typvoie))
                if str(row.compvoie) != "nan":
                    line_vals.append(str(row.compvoie))
                if row.voie:
                    line_vals.append(str(row.voie))

                eg_id = f"{str(row.nofinessej).strip()}-{str(row.nofinesset).strip()}"
                data = {
                    "id": eg_id,
                    "extension": [
                        dict(
                            url="http://hl7.org/fhir/StructureDefinition/organization-period",
                            valuePeriod={"start": row.dateouv}
                        )],
                    "identifier": [dict(
                        use="official",
                        type={"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                          "code": "FINEG",
                                          "display": "FINESS d'entité géographique"}]},
                        system="urn:oid:1.2.250.1.71.4.2.2",
                        value=row.nofinesset)
                    ],
                    "type": [
                        dict(
                            coding=[
                                dict(
                                    system="http://hl7.org/fhir/organization-type",
                                    code="prov",
                                    display="Healthcare Provider"
                                ),
                                dict(
                                    system="http://terminology.hl7.org/CodeSystem/v2-3307",
                                    code="GEOGRAPHICAL-ENTITY",
                                    display="Entité géographique"
                                ),
                                dict(
                                    system="https://mos.esante.gouv.fr/NOS/TRE_R75-InseeNAFrev2Niveau5/FHIR/TRE-R75-InseeNAFrev2Niveau5",
                                    code=row.codeape,
                                    display="Code APE"
                                ),
                                dict(
                                    system="http://finess.sante.gouv.fr/valuesets/CAT_ETAB",
                                    code=row.categetab,
                                    display=row.libcategetab
                                ),
                                dict(
                                    system="http://finess.sante.gouv.fr/valuesets/CAT_AGR_ETAB",
                                    code=row.categagretab,
                                    display=row.libcategagretab
                                ),
                                dict(
                                    system="http://finess.sante.gouv.fr/valuesets/SPH",
                                    code=row.codesph,
                                    display=row.libsph
                                )
                            ]
                        )],
                    "active": True,
                    "text": dict(
                        status="generated",
                        div=f"""<div xmlns=\"http://www.w3.org/1999/xhtml\">Entité Géographique - finess {row.nofinesset}</div>"""),
                    "name": str(row.rs),
                    "meta": {"lastUpdated": f"{row.datemaj}T00:00:00Z"},
                    "address": [dict(use="work", type="postal", country="France", line=[" ".join(line_vals)])]
                }

                if str(row.siret) != "nan":
                    data["identifier"].append(
                        dict(
                            use="official",
                            system="http://sirene.fr",
                            value=row.siret
                        )
                    )

                res = re.match(r"(\d+)\s(.*)", row.ligneacheminement)
                if res:
                    postal_code, city = res.groups()
                    data["address"][0]["postalCode"] = postal_code
                    data["address"][0]["city"] = city

                if str(row.telephone) != "nan":
                    data["telecom"] = [dict(system="phone", value=row.telephone, use="work")]

                org = Organization(**data)

                # Localisation GPS
                location_data = {"id": "%s-loc" % eg_id}
                geo = self.df_finess_geo[
                    self.df_finess_geo.nofinesset == row.nofinesset
                    ]
                # if geo.sourcecoordet.str.contains("LAMBERT_93").bool():
                if "LAMBERT_93" in str(geo.sourcecoordet):
                    x, y = self.convert_coordinates(
                        float(geo.coordxet), float(geo.coordyet), "LAMBERT_93"
                    )
                else:
                    self.logger.warning(f"GEO WARN : |{str(geo.sourcecoordet)}|")
                    x, y = float(geo.coordxet), float(geo.coordyet)

                location_data["position"] = dict(longitude=x, latitude=y)
                location_data["managingOrganization"] = dict(reference=f"Organization/{eg_id}")

                loc = Location(**location_data)

                fout.write(f"{org.json()}\n")
                fout.write(f"{loc.json()}\n")

    def generate(self, ndoutputdir, start=None, end=None):
        self.logger.info(f"Generate {len(self.df_finess)} records")
        istart = int(start) if start else 0
        iend = int(end) if end else len(self.df_finess)

        ndoutput = os.path.join(ndoutputdir, f"etab{istart}-{iend}.ndjson")

        with open(ndoutput, "w") as fout:
            # Timone : self.df_finess[self.df_finess.nofinesset == '130783293']
            for row in self.df_finess[istart:iend]:
                eg_id = f"{str(row['nofinessej']).strip()}-{str(row['nofinesset']).strip()}"
                self.logger.info(f"Etab geo {eg_id} - [{row['rs']}]")
                addr_lines = []
                line_vals = []
                if len(row['numvoie']) > 0:
                    line_vals.append(str(row['numvoie']))
                if len(row['typvoie']) > 0:
                    line_vals.append(str(row['typvoie']))
                if len(row['compvoie']) > 0:
                    line_vals.append(str(row['compvoie']))
                if len(row['voie']) > 0:
                    line_vals.append(str(row['voie']))
                if len(line_vals) > 0:
                    addr_lines.append(" ".join(line_vals))

                if len(row['lieuditbp']) > 0:
                    addr_lines.append(row["lieuditbp"])

                data = {
                    "id": eg_id,
                    "extension": [
                        dict(
                            url="http://hl7.org/fhir/StructureDefinition/organization-period",
                            valuePeriod={"start": row['dateouv']}
                        )],
                    "identifier": [dict(
                        use="official",
                        type=dict(coding=[dict(system="http://terminology.hl7.org/CodeSystem/v2-0203",
                                               code="FINEG",
                                               display="FINESS d'entité géographique")]),
                        system="urn:oid:1.2.250.1.71.4.2.2",
                        value=row['nofinesset'])
                    ],
                    "type": [
                        dict(
                            coding=[
                                dict(
                                    system="http://hl7.org/fhir/organization-type",
                                    code="prov",
                                    display="Healthcare Provider"
                                ),
                                dict(
                                    system="http://terminology.hl7.org/CodeSystem/v2-3307",
                                    code="GEOGRAPHICAL-ENTITY",
                                    display="Entité géographique"
                                ),
                                dict(
                                    system="http://finess.sante.gouv.fr/valuesets/CAT_ETAB",
                                    code=row['categetab'],
                                    display=row['libcategetab']
                                ),
                                dict(
                                    system="http://finess.sante.gouv.fr/valuesets/CAT_AGR_ETAB",
                                    code=row['categagretab'],
                                    display=row['libcategagretab']
                                )
                            ]
                        )],
                    "active": True,
                    "text": dict(
                        status="generated",
                        div=f"""<div xmlns=\"http://www.w3.org/1999/xhtml\">Entité Géographique - finess {row['nofinesset']}</div>"""),
                    "name": str(row['rs']),
                    "meta": dict(lastUpdated=f"{row['datemaj']}T00:00:00Z"),
                    "address": [dict(use="work", type="postal", country="France", line=addr_lines)]
                }

                if len(row['codeape']) > 0:
                    data["type"][0]["coding"].append(
                        dict(
                            system="https://mos.esante.gouv.fr/NOS/TRE_R75-InseeNAFrev2Niveau5/FHIR/TRE-R75-InseeNAFrev2Niveau5",
                            code=row['codeape'],
                            display="Code APE"
                        ))
                if len(row['codesph']) > 0:
                    data["type"][0]["coding"].append(
                        dict(
                            system="http://finess.sante.gouv.fr/valuesets/SPH",
                            code=row['codesph'],
                            display=row['libsph']
                        ))

                if str(row['siret']) != "":
                    data["identifier"].append(
                        dict(
                            use="official",
                            system="http://sirene.fr",
                            value=row['siret']
                        )
                    )

                res = re.match(r"(\d+)\s(.*)", row['ligneacheminement'])
                if res:
                    postal_code, city = res.groups()
                    data["address"][0]["postalCode"] = postal_code
                    data["address"][0]["city"] = city

                if str(row['telephone']) != "":
                    data["telecom"] = [dict(system="phone", value=row['telephone'], use="work")]

                try:
                    org = Organization(**data)
                except Exception as e:
                    self.logger.error("Error in data -> FHIR")
                    self.logger.error(pp.pformat(data))
                    self.logger.error(e)
                    sys.exit(1)

                fout.write(f"{org.json()}\n")

                # if geo.sourcecoordet.str.contains("LAMBERT_93").bool():
                coordxet, coordyet = self.finess_geo[row['nofinesset']]
                try:
                    # Localisation GPS
                    location_data = {"id": "%s-loc" % eg_id}
                    x, y = self.convert_coordinates(
                        float(coordxet), float(coordyet), "LAMBERT_93"
                    )
                    location_data["position"] = dict(longitude=x, latitude=y)
                    location_data["managingOrganization"] = dict(reference=f"Organization/{eg_id}")

                    loc = Location(**location_data)
                    fout.write(f"{loc.json()}\n")

                except ValueError as e:
                    self.logger.error(f"Error geo data  {row['nofinesset']}|{coordxet}|{coordyet}|")
                    self.logger.error(str(e))
