# BIG-MAP Archive REST API Examples

Following are examples of how to programmatically 
- upload records to BIG-MAP Archive
- retrieve the content of uploaded json files.

In these examples, we use the website hosted on
https://dev1-big-map-archive.materialscloud.org.

Note that this work was inspired by https://github.com/inveniosoftware/docs-invenio-rdm-restapi-example.

## Fulfill requirements

You need Python and the `requests` library:

```
pip install requests
```

## Obtain a token

You need to obtain an access token, by creating one here:

- https://dev1-big-map-archive.materialscloud.org/account/settings/applications/tokens/new/

Next, edit [``upload_records.py``](upload_records.py) and [``retrieve_scientific_data.py``](retrieve_scientific_data.py), and add the token:

```python
url = "https://dev1-big-map-archive.materialscloud.org/"
token = "<replace by a personal token>"
```

## Inspect input files

We created 3 folders:
- `records/0`
- `records/1`
- `records/2`.

Each folder may correspond to a record in the archive. It contains various files, including:
- `record_metadata.json`: a JSON file that contains metadata about the record (title, authors...)
- `scientific_data.json`: a JSON file that contains metadata and data about scientific experiments/simulations.

## Run the "upload" script

From the 3 folders mentioned above, running the "upload" script creates 3 draft records in the archive, which you can access from:
- https://dev1-big-map-archive.materialscloud.org/uploads

Note that the file `record_metadata.json` is used to create the record. The other files are simply attached to the record.

You can run the upload script using the `python` command:

```
python upload_records.py
```

A file named `records_links.json` is generated. It stores URLs for the record and its attached files.

## Run the "retrieve" script

You can retrieve the content of the 3 `scientific_data.json` files that are stored in the archive as follows:
```
python retrieve_scientific_data.py
```

The script uses `records_links.json` as input and produces `records_scientific_data.json`. The content of this file can be compared with those of:
- `records/0/scientific_data.json` 
- `records/1/scientific_data.json`
- `records/2/scientific_data.json`.

Please let us know if you have any questions or comments at [big-map-archive@materialscloud.org](big-map-archive@materialscloud.org).



