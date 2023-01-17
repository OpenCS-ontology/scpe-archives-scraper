# scpe-archives-scraper
Scraper for the Archives of Scalable Computing: Practice and Experience

Gets data from SCPE archives website and aggregating it into .ttl files. Scraper asks the DOI api for additional info about the paper.

The scraper can be run with docker (`./docker_build.sh`, `./docker_run.sh`) or locally (`run.sh`).

## Files
* `docker_build.sh`, `docker_run.sh` - Scripts to build and run the program in a docker container. `docker_run.sh` creates a `target` directory to which the .ttl files will flow. One file for one scraped paper.
* `run.sh` - Scripts to run the program locally. Creates a `target_local` directory to which the .ttl files will flow.
* `ontology_model.gv` - DOT (GraphViz) file describing the ontology.
* `onto.ttl` - Turtle file describing the classes.

## Ontology
1. **`:Paper`**
	* `fabio:hasUrl` - URL of the scraped page in SCPE archives (as URI).
	* `prism:doi` - DOI of the paper.
	* `dcterms:title` - Title.
	* `dcterms:abstract` - Abstract.
	* `dcterms:created` - Creation date of the paper.
	* `prism:volume` - Volume in SCPE journal. Need not to be a number, for example Roman numerals may be used (e.g. "iii").
	* `prism:startingPage` - Starting page in the volume. Need not to be a number.
	* `prism:endingPage` - Ending page in the volume. Need not to be a number.
	* `prism:keyword` - One of the keywords for this paper. Multiple keywords allowed.
	* `frbr:realization` - Blank node of class `fabio:DigitalManifestation` with properties:
		* `dcterms:format` - Always "application/pdf".
		* `fabio:hasURL` - URL to the PDF file for this paper (as URI).
	* `dcterms:creator` - Link to each of the `:Author`s.
2. **`:Author`**
	* `foaf:givenName` - Given name. Can be equal to the whole name of the author (`givenName` + `familyName`) in case the DOI api doesn't mention a particular author.
	* `foaf:familyName` - Family name. The same applies as in case of `givenName`.
	* `dbo:orcidId` - ORCID number of the author.
	* `org:memberOf` - Link to author's `:Affiliation`s.
3. **`:Affiliation`**
	* `skos:prefLabel` - Name of the organization.
