# big-map-archive-api-client

## Overview

This is a command line client to interact with BIG-MAP Archive data repositories.

## Usage

### Overview

```
$ bma --help
```
```text
Usage: bma [OPTIONS] COMMAND [ARGS]...

  Command line client to interact with a BIG-MAP Archive.

Options:
  --help  Show this message and exit.

Commands:
  finales-db  Copy data from the database of a FINALES server to a...
  record      Manage records on a BIG-MAP Archive.
```

### Create, update, and retrieve records

```bash
$ bma record --help
```

```text
Usage: bma record [OPTIONS] COMMAND [ARGS]...

  Manage records on a BIG-MAP Archive.

Options:
  --help  Show this message and exit.

Commands:
  create   Create a record on a BIG-MAP Archive and optionally publish it.
  get      Get the metadata of a published version of an entry on a...
  get-all  Get the metadata of the latest published version for each...
  update   Update a published version of an archive entry, or create a...
```

```bash
$ bma record create --help
```

```text
Usage: bma record create [OPTIONS]

  Create a record on a BIG-MAP Archive and optionally publish it.

Options:
  --config-file FILE      Path to the YAML file that specifies the domain name
                          and a personal access token for the targeted BIG-MAP
                          Archive. See bma_config.yaml in the GitHub
                          repository.  [required]
  --metadata-file FILE    Path to the YAML file for the record's metadata
                          (title, list of authors, etc). See
                          data/input/example/create_record/metadata.yaml in
                          the GitHub repository.  [required]
  --data-files DIRECTORY  Path to the directory that contains the data files
                          to be uploaded and linked to the record. See
                          data/input/example/create_record/upload in the
                          GitHub repository.  [required]
  --publish               Publish the created record.
  --help                  Show this message and exit.
```

```bash
$ bma record get --help
```

```text
Usage: bma record get [OPTIONS]

  Get the metadata of a published version of an entry on a BIG-MAP Archive and
  save it to a file.

Options:
  --config-file FILE  Path to the YAML file that specifies the domain name and
                      a personal access token for the targeted BIG-MAP
                      Archive. See bma_config.yaml in the GitHub repository.
                      [required]
  --record-id TEXT    Id of the published version of an archive entry (e.g.,
                      "pxrf9-zfh45").  [required]
  --output-file FILE  Path to the JSON file where the obtained record's
                      metadata will be exported to.  [required]
  --help              Show this message and exit.
```

```bash
$ bma record get-all --help
```

```text
Usage: bma record get-all [OPTIONS]

  Get the metadata of the latest published version for each entry on a BIG-MAP
  Archive and save them to a file.

Options:
  --config-file FILE  Path to the YAML file that specifies the domain name and
                      a personal access token for the targeted BIG-MAP
                      Archive. See bma_config.yaml in the GitHub repository.
                      [required]
  --all-versions      Get all published versions for each entry. By default,
                      only the latest published version for each entry is
                      retrieved.
  --output-file FILE  Path to the JSON file where the obtained record's
                      metadata will be exported to.  [required]
  --help              Show this message and exit.
```

```bash
$ bma record update --help
```

```text
Usage: bma record update [OPTIONS]

  Update a published version of an archive entry, or create a new version and
  optionally publish it. When updating a published version, only the metadata
  (title, list of authors, etc) can be modified.

Options:
  --config-file FILE              Path to the YAML file that specifies the
                                  domain name and a personal access token for
                                  the targeted BIG-MAP Archive. See
                                  bma_config.yaml in the GitHub repository.
                                  [required]
  --record-id TEXT                Id of the published version (e.g.,
                                  "pxrf9-zfh45").  [required]
  --update-only                   Update the metadata of the published
                                  version, without creating a new version. By
                                  default, a new version is created.
  --metadata-file FILE            Path to the YAML file that contains the
                                  metadata (title, list of authors, etc) for
                                  updating the published version or creating a
                                  new version. See data/input/example/update_r
                                  ecord/metadata.yaml in the GitHub
                                  repository.  [required]
  --data-files DIRECTORY          Path to the directory that contains the data
                                  files to be linked to the newly created
                                  version. See
                                  data/input/example/update_record/upload in
                                  the GitHub repository.  [required]
  --link-all-files-from-previous  Link all files that are already linked to
                                  the previous version to the new version,
                                  with the exception of files whose content
                                  changed.
  --publish                       Publish the newly created version.
  --help                          Show this message and exit.
```

### Back-up a FINALES database into a BIG-MAP Archive

```bash
$ bma finales-db --help
```

```text
Usage: bma finales-db [OPTIONS] COMMAND [ARGS]...

  Copy data from the database of a FINALES server to a BIG-MAP Archive.

Options:
  --help  Show this message and exit.

Commands:
  back-up  Perform a partial back-up from the database of a FINALES...
```

```bash
$ bma finales-db back-up --help
```

```text
Usage: bma finales-db back-up [OPTIONS]

  Perform a partial back-up from the database of a FINALES server to a BIG-MAP
  Archive. A new entry version is created and published. Its linked files
  include data related to capabilities, requests, and results for requests.

Options:
  --bma-config-file FILE          Path to the YAML file that specifies the
                                  domain name and a personal access token for
                                  the targeted BIG-MAP Archive. See
                                  bma_config.yaml in the GitHub repository.
                                  [required]
  --finales-config-file FILE      Path to the YAML file that specifies the IP
                                  address, the port, and the credentials of a
                                  user account for the targeted FINALES
                                  server. See finales_config.yaml in the
                                  GitHub repository.  [required]
  --record-id TEXT                Id of the published version for the previous
                                  back-up (e.g., "pxrf9-zfh45"). For the first
                                  back-up, leave to the default.
  --metadata-file FILE            Path to the YAML file that contains the
                                  metadata (title, list of authors, etc) for
                                  creating a new version. See data/input/examp
                                  le/create_record/metadata.yaml in the GitHub
                                  repository.  [required]
  --link-all-files-from-previous  Link all files that are already linked to
                                  the previous version to the new version,
                                  with the exception of files whose content
                                  changed.
  --no-publish                    Do not publish the newly created version.
                                  This is discouraged in production. If you
                                  select this option, either publish or delete
                                  the newly created draft, e.g., via the GUI.
  --help                          Show this message and exit.
````

## Support

If you have any comments or questions, please send your emails to big-map-archive@materialscloud.org.

## Issue

If you find a bug, please create an issue directly into [GitHub](https://github.com/materialscloud-org/big-map-archive-api-client/issues). If possible, give enough details so that the BIG-MAP Archive team is able to reproduce the encountered problem. Thank you!

## Acknowledgements

This project has received funding from the European Union’s [Horizon 2020 research and innovation programme](https://ec.europa.eu/programmes/horizon2020/en) under grant agreement [No 957189](https://cordis.europa.eu/project/id/957189). The project is part of BATTERY 2030+, the large-scale European research initiative for inventing the sustainable batteries of the future.



