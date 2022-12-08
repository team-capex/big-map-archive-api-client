# BIG-MAP Archive REST API Examples

Following are examples of how to programmatically
- create and publish records to BIG-MAP Archive (https://archive.big-map.eu/).

Note that the API documentation can be found at https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records.

## Fulfill requirements

You need Python and the `requests` library:

```
pip install requests
```

## Obtain a token

You need a personal API access token. If you do not have one yet, follow this link after a successful login: https://archive.big-map.eu/account/settings/applications/tokens/new/.

Next, edit [``create_and_publish_records.py``](create_and_publish_records.py) and add the token:

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

## Run the "create_and_publish_records" script

Running the script creates and publishes 2 records on the archive from the 2 folders mentioned above. Note that, while the files `record_metadata.json` are used for filling in the metadata section of the upload forms, the other files are simply attached to the records.

You can run the upload script using the `python` command:

```
python create_and_publish_records.py
```

If the execution terminates successfully, you should be able to access the newly-published records from your web browser: https://archive.big-map.eu/search.

Running the script also generates a file named `records_links.json` in the `records` folder. This file stores URLs for the newly-created records. It can be used to act on these records via the API (e.g., to update a record).

Please let us know if you have any questions or comments at [big-map-archive@materialscloud.org](big-map-archive@materialscloud.org).



## Not clear
- In the metadata, the `version` is specified, however, the `version` should be generated automatically when one upload and generate a new version.
- What is the `publication_date`? Is it the time the record get published? This should be generated automatically.

## Todo
- Show a full example (template) for all possible keys, e.g. How to add reference? How to choose the lincense?

- How to update a record?

## Improvement
- We can create a python package to do this. Upload to Pypi, thus the user can easily install it.
- Support cli.
