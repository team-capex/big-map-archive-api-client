# big-map-archive-api-examples

## Overview

This repository provides client scripts that are written in Python to interact with the BIG-MAP Archive's API. 

Three scripts are currently available:
- a script `create_record.py` to create a record on BIG-MAP Archive, with the option to publish it (i.e., to share it with all users)
- a script `retrieve_record.py` to retrieve the metadata of one or more published records
- a script `update_record.py` to update a published record, with the options to create and publish a new version.

## Quick access

1. [Installation](#Installation)
2. [Secrets](#Secrets)
3. [Configuration files](#Configuration)
4. [Input files](#Input files)
5. [Execution](#Execution)
6. [Roadmap](#Roadmap)
7. [Support](#Support)
8. [Issue](#Issue)

## Installation

Proceed as follows to install the scripts:

1. Clone the [GitHub repository](https://github.com/materialscloud-org/big-map-archive-api-examples/).
2. Create and activate a virtual environment named `big-map-archive-api-examples`.
3. Install dependencies from `requirements.txt`.
4. Create a file named `secrets.env` at the project's root and fill it in with secrets.

## Secrets

A template for the file `secrets.env` is provided below:

```bash
# SECURITY WARNING: keep the content of this file secret!
# Do not commit it to a source code repository

# Personal access token for the archive (to create a new token, navigate to 'Applications' > 'Personal access tokens')
MAIN_ARCHIVE_TOKEN='<valid_token_for_main>'
DEMO_ARCHIVE_TOKEN='<valid_token_for_demo>'
```

Replace `<valid_token_for_main>` by a personal access token for the main repository. Do the same for the demo repository.

## Configuration

Users are invited to configure the scripts by assigning valid values of their choosing to keys in `config.ini`.

Note that `config.ini` contains multiple sections:
- a general section named `[general]`, which applies to all scripts
- a section per script, which applies to a single script only; 
for instance, the section `[create_record]` applies to the script `create_record.py`. 

## Input files

The scripts `create_record` and `update_record` creates a record and updates a published record respectively.

For both scripts, two types of input files can be provided in the `input` folder:
- a single metadata file `metadata.json`, which specifies the title of the desired record, its authors, etc
- one or more data files of any format and of total size smaller than 100 GB; these files will be uploaded to BIG-MAP Archive and linked to the record.

A template for `metadata.json` is as follows:

```json
{
  "creators": [
    {
      "affiliations": [
        {
          "name": "Theory and Simulation of Materials (THEOS), École Polytechnique Fédérale de Lausanne, CH-1015 Lausanne, Switzerland"
        }
      ],
      "person_or_org": {
        "family_name": "Liot",
        "given_name": "Francois",
        "name": "Liot, Francois",
        "type": "personal"
      }
    },
    {
      "affiliations": [
        {
          "name": "Theory and Simulation of Materials (THEOS), École Polytechnique Fédérale de Lausanne, CH-1015 Lausanne, Switzerland"
        },
        {
          "name": "Center for Catalysis Theory (Cattheory), Department of Physics, Technical University of Denmark (DTU), 2800 Kongens Lyngby, Denmark"
        }
      ],
      "person_or_org": {
        "family_name": "Von Big-Map",
        "given_name": "Emma",
        "name": "Von Big-Map, Emma",
        "type": "personal"
      }
    }
  ],
  "description": "<p>Accurate first-principles predictions of the structural, electronic, magnetic, and electrochemical properties of cathode materials can be key in the design of novel efficient Li-ion batteries...</p>",
  "publisher": "BIG-MAP Archive",
  "related_identifiers": [
    {
      "identifier": "10.1000/182",
      "relation_type": {
        "id": "references",
        "title": {
          "en": "References"
        }
      },
      "scheme": "doi"
    }
  ],
  "resource_type": {
    "id": "dataset",
    "title": {
      "en": "Dataset"
    }
  },
  "rights": [
    {
      "description": {
        "en": "The BIG-MAP Archive License allows re-distribution and re-use of work within the BIG-MAP community."
      },
      "id": "bm-1.0",
      "props": {
        "scheme": "spdx",
        "url": "https://www.big-map.eu/"
      },
      "title": {
        "en": "BIG-MAP Archive License"
      }
    }
  ],
  "subjects": [
    {
      "subject": "Li-ion batteries"
    },
    {
      "subject": "DFT+U+V"
    }
  ],
  "title": "Inter-site Hubbard interactions in Li-ion cathode rods"
}
```

Feel free to adapt the template to your desired record:
- the resource type (corresponding to the key `resource_type` in the template)
- the title (`title`)
- the list of authors (`creators`)
- the description (`description`)
- the list of licenses (`rights`)
- the list of keywords (`subjects`)
- the list of references (`related_identifiers`).

Visit the [upload form](https://archive.big-map.eu/uploads/new) to find out 
what options are available for the resource type, a license, and a reference scheme.

An example of input files is provided:
- in `input/example/create_record` for the script `create_record.py`
- in `input/example/update_record` for the script `update_record.py`.

## Execution

You can run the scripts using the `python` command:

```
python create_record.py
```
```
python retrieve_record.py
```
```
python update_record.py
```

## Roadmap

Further work may include:
- renaming the repository `big-map-archive-api-client`
- creating a Python package, which users would be able to install in their virtual environment
- adopting a more object-oriented programming approach by declaring a class `BMA`
- defining commands, which users would be able to call from a Linux terminal.

## Support

If you have any comments or questions, please send your emails to big-map-archive@materialscloud.org.

## Issues

If you find a bug, please create an issue directly into [GitHub](https://github.com/materialscloud-org/big-map-archive-api-examples/issues). If possible, give enough details so that the BIG-MAP Archive team is able to reproduce the encountered problem. Thank you!

## Acknowledgements

This project has received funding from the European Union’s [Horizon 2020 research and innovation programme](https://ec.europa.eu/programmes/horizon2020/en) under grant agreement [No 957189](https://cordis.europa.eu/project/id/957189). The project is part of BATTERY 2030+, the large-scale European research initiative for inventing the sustainable batteries of the future.



