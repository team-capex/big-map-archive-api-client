# big-map-archive-api-client

## Overview

This repository provides methods to interact with the BIG-MAP Archive's API.

## FINALES server's database back-ups

Comments about entries, titles, service accounts per "campaign":
    - There should be a single entry in the archive per campaign;
    - An entry may have multiple versions, with one version created each time a back-up of the FINALES database occurs;
    - A title should be given to each version of an entry but should remain unchanged across all versions of the same entry;
    - A title should vary from one entry to another and should be unique to a campaign;
    - A single service account (e.g., jane.doe+FINALES_1@xxx.xx) should be used for doing back-ups of a campaign; it becomes the owner of the entry and the linked data files;
    - A single service account can be used for multiple campaigns.

## Support

If you have any comments or questions, please send your emails to big-map-archive@materialscloud.org.

## Issue

If you find a bug, please create an issue directly into [GitHub](https://github.com/materialscloud-org/big-map-archive-api-client/issues). If possible, give enough details so that the BIG-MAP Archive team is able to reproduce the encountered problem. Thank you!

## Acknowledgements

This project has received funding from the European Union’s [Horizon 2020 research and innovation programme](https://ec.europa.eu/programmes/horizon2020/en) under grant agreement [No 957189](https://cordis.europa.eu/project/id/957189). The project is part of BATTERY 2030+, the large-scale European research initiative for inventing the sustainable batteries of the future.



