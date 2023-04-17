<h1 align="center">Amazon author check</h1>
<h4 align="center">A fully automated tool for scraping the Amazon author page and sending alers when new books are available</h4>

![](images/Running_script.png)


# Features

- Support for Pushover notifications
- Support for single and all authors
- Support for custom author list
- Support for custom author folder

---

# Description

A simple All-In-One python script to scrape information from the Amazon author pages and comparing this to known local data. 

# Setup
This script is usable form your local system or with the use of a docker container.
## Download
Clone the git repo to local
```bash
git clone https://github.com/jopbakker/amazonbooks_python.git
```

## Local installation
Using this local version requires python 3.x to be installed on your system. Python can be installed from the [Python website](https://www.python.org/downloads/).
```
$ pip3 install -r docker/requirements.txt
```

## Docker installation
In order yo use this docker container you must first install docker from the [Docker website](https://docs.docker.com/get-docker/) or with you package manager.
```shell
cd amazonbooks_python/docker
sudo docker build -t amazonbooks:latest .
```

# Usage

```
python.exe .\amazonbooks.py -h
usage: amazonbooks.py [-h] [-a CHECK_AUTHOR] [-aL AUTHOR_LIST] [--author-file-folder AUTHOR_FILES_FOLDER] [--log-level LOG_LEVEL] [--test TEST_RUN] [-Pu USER_TOKEN] [-Pa API_TOKEN]

optional arguments:
  -h, --help            show this help message and exit
  -a CHECK_AUTHOR, --author CHECK_AUTHOR
                        Custom author check - [Default: all]
  -aL AUTHOR_LIST, --author-list AUTHOR_LIST
                        Custom filename for the csv file containing authors and urls - [Default: authors.csv]
  --author-file-folder AUTHOR_FILES_FOLDER
                        Custom authors file location - [Default: authors]
  --log-level LOG_LEVEL
                        Set the level of logs to show (Options: DEBUG, INFO, WARNING, ERROR, CRITICAL) - [Default: INFO]
  --test TEST_RUN       Set this to 'True' to run the script without sending the pushover message or saving the author files - [Default: False]

  -Pu USER_TOKEN, --pushover-user-token USER_TOKEN
                        Pushover user token
  -Pa API_TOKEN, --pushover-api-token API_TOKEN
                        Pushover API token
```
## Looking up all authors (default)
**Native**
```shell
python3 amazonbooks.py -Pu "<Pushover user key>" -Pa "<Pushover API key>"
```

**Docker**
```shell
docker run --rm -it -v ${PWD}:/app amazonbooks -Pu "<Pushover user key>" -Pa "<Pushover API key>"
```

## Looking up a single author
**Native**
```shell
python3 amazonbooks.py -a Brandon_Sanderson -Pu "<Pushover user key>" -Pa "<Pushover API key>"
```

**Docker**
```shell
docker run --rm -it -v ${PWD}:/app amazonbooks -a Brandon_Sanderson -Pu "<Pushover user key>" -Pa "<Pushover API key>"
```

# License
The project is licensed under MIT License.