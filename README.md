# Consuming BIG-MAP Archive's REST API

Below is an example of how to programmatically <b>create and share records</b> on [BIG-MAP Archive](https://archive.big-map.eu/).

## Demo archive

In addition to the main production archive (with daily backups), 
a [demo archive](https://big-map-archive-demo.materialscloud.org/) is available so that you can practice creating and managing records via the application programming interface (API). 
For testing purposes, use the demo archive.

## User accounts

The main archive and the demo archive are independent systems. If you are a registered BIG-MAP member, two accounts (one per archive) should have been created for you by the BIG-MAP Archive team. 

Prior to your first login to an archive, you should reset your password, as explained in the [tutorial](https://github.com/materialscloud-org/big-map-archive/blob/master/user_training/getting_started_with_big-map-archive.md).

## Fulfill requirements

Clone the repository `big-map-archive-api-examples` to your local machine. You need Python and the `requests` library:

```
pip install requests
```

## Obtain a token

You need a personal API access token. If you do not have one yet, click [here](https://big-map-archive-demo.materialscloud.org/account/settings/applications/tokens/new/) after a successful login.

Next, edit [`create_and_share_records.py`](create_and_share_records.py) and add the token:

```python
token = "<replace by a personal token>"
```

## Inspect input files

We created 2 folders:
- `records/0`
- `records/1`.

Each folder will give a new record in the archive. It contains various files, including:
- `record_metadata.json`: a JSON file that contains metadata about the record (title, authors...)
- `scientific_data.json`: a JSON file that contains metadata and data about scientific experiments/simulations.

## Create and share records

Running the script `create_and_share_records.py` creates and shares 2 records on the archive from the 2 folders mentioned above. 
Note that, while the files `record_metadata.json` are used for filling in the metadata section of the upload forms, the other files are simply attached to the records.

You can run the upload script using the `python` command:

```
python create_and_share_records.py
```

If the execution terminates successfully, you should be able to [access the newly-shared records](https://big-map-archive-demo.materialscloud.org/search).

Running the script also generates a file named `records_links.json` in the `records` folder. This file stores URLs for the newly-created records. It can be used to act on these records via the API (e.g., to update a record).

## Documentation for the API

A documentation for the API (including its endpoints for downloading files, searching for records, etc) is available on the [InvenioRDM website](https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records).

## Support

If you have any comments or questions, please send your emails to big-map-archive@materialscloud.org.

## Issues

If you find a bug, please create an issue directly into [GitHub](https://github.com/materialscloud-org/big-map-archive-api-examples/issues). If possible, give enough details so that the BIG-MAP Archive team is able to reproduce the encountered problem. Thank you!

## Acknowledgements

This project has received funding from the European Union’s [Horizon 2020 research and innovation programme](https://ec.europa.eu/programmes/horizon2020/en) under grant agreement [No 957189](https://cordis.europa.eu/project/id/957189). The project is part of BATTERY 2030+, the large-scale European research initiative for inventing the sustainable batteries of the future.



