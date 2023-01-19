# scpe-archives-scraper
Scraper for the Archives of Scalable Computing: Practice and Experience

Gets data from SCPE archives website and aggregating it into .ttl files. Scraper asks the DOI api for additional info about the paper.

The scraper can be run with docker (`./docker_build.sh`, `./docker_run.sh`) or locally (`run.sh`).

## Files
* `docker_build.sh`, `docker_run.sh` - Scripts to build and run the program in a docker container. `docker_run.sh` creates a `target` directory to which the `.ttl` files will flow. One file for one scraped paper.
* `run.sh` - Scripts to run the program locally. Creates a `target_local` directory to which the .ttl files will flow.
* `ontology_model.gv` - DOT (GraphViz) file describing the ontology.
* `onto.ttl` - Turtle file describing the classes.

## Vocabulary
### `:Paper`

* `fabio:hasUrl` - URL of the scraped page in SCPE archives (as URI).
* `prism:doi` - DOI of the paper.
* `dcterms:title` - Title.
* `dcterms:abstract` - Abstract.
* `dcterms:created` - Creation date of the paper.
* `prism:volume` - Volume in SCPE journal. Need not be a number, for example Roman numerals may be used (e.g. "iii").
* `prism:startingPage` - Starting page in the volume. Need not be a number.
* `prism:endingPage` - Ending page in the volume. Need not be a number.
* `prism:keyword` - One of the keywords for this paper. Multiple keywords allowed.
* `frbr:realization` - Blank node of class `fabio:DigitalManifestation` with properties:
	* `dcterms:format` - Always "application/pdf".
	* `fabio:hasURL` - URL to the PDF file for this paper (as URI).
* `dcterms:creator` - Link to each of the `:Author`s.

### `:Author`
* `foaf:name` - Name, as given on the scraped page. Most likely to be attributed to the author.
* `foaf:givenName` - Given name. Especially for older SCPE volumes, given name is not attributed to the author.
* `foaf:familyName` - Family name. Especially for older SCPE volumes, family name is not attributed to the author.
* `dbo:orcidId` - ORCID number of the author.
* `org:memberOf` - Link to author's `:Affiliation`s.

### `:Affiliation`
* `skos:prefLabel` - Name of the organization.
