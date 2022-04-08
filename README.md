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

If you do not have a personal access token yet, you can create one by following the link below after a successful login:

- https://dev1-big-map-archive.materialscloud.org/account/settings/applications/tokens/new/.

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

Each folder will give a new record in the archive. It contains various files, including:
- `record_metadata.json`: a JSON file that contains metadata about the record (title, authors...)
- `scientific_data.json`: a JSON file that contains metadata and data about scientific experiments/simulations.

## Run the "upload" script

Running the upload script creates 3 draft records in the archive from the 3 folders mentioned above. Note that, while the files `record_metadata.json` are used for filling in "the metadata section of the upload forms", the other files are simply attached to the records.

You can run the upload script using the `python` command:

```
python upload_records.py
```

If the execution terminates successfully, you should be able to access the newly-created draft records from the website by following the link below:
- https://dev1-big-map-archive.materialscloud.org/uploads.

Running the script also generates a file named `records_links.json` in the `records` folder. This file stores URLs for the newly-created records. It can be used to act on these records via the API (e.g., to update a record).

## Run the "retrieve" script

The retrieve script harvests the content of the `scientific_data.json` files that were uploaded to the archive and attached to the draft records specified in `records_links.json`. 

You can run it as follows:

```
python retrieve_scientific_data.py
```

The script uses `records_links.json` as input and produces `records_scientific_data.json`. The content of this file can be compared with those of:
- `records/0/scientific_data.json` 
- `records/1/scientific_data.json`
- `records/2/scientific_data.json`.

Please let us know if you have any questions or comments at [big-map-archive@materialscloud.org](big-map-archive@materialscloud.org).



