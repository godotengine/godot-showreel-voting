# Godot showreel rating website

This repository hosts the Godot Showreel webapp. It is a video submission and
voting platform meant to help contributors selecting the best videos to
showcase Godot engine projects.


## Current state

The following functionality is implemented:
* Cast a vote:
    
    Videos participating in the showreel are shown in a random order, a user can cast a positive or negative vote or skip the specific video
> **_Note:_** If a video is skipped it will not be in the pool of possible videos for the immediate next request. The `skipped` state is not persisted

* Edit a vote:
    
    Users are able to browse through their vote history. If they so desire they are able to update their vote.

* Delete a vote:

    Users can delete a vote they have cast. When a vote is deleted, it is complete erase from the database. Which will result in the video showing again in the showreel vote system

* Admin view

    There is an admin view that displays the current state of the votes, ordered by number of positive votes descending.
    In this panel there is a button to download a `.csv` file with the results. The file contains the following information:

     * Author 
     * Follow-me link 
     * Game
     * Video link
     * Download link
     * Contact email
     * Store Link
     * Positive votes
     * Negative votes
     * staff
     * fund_member


## Requirements

For this project I'm trying [uv](https://docs.astral.sh/uv/),a python project manager. The idea is that this tool should replace the need for virtualenvironments and package managers with a a single one.

Configuration is fetched from a config file located in `./instance/config.py`. [An example configuration](instance/example-config.py) is provided with everything setup for local development.

### Quickstart

Install `uv`: https://docs.astral.sh/uv/#installation


* To run the project:

        uv run flask --app main run --debug

* To add dependencies:

        uv add [package-name]

* To add dev dependencies

        uv add --dev [package-name]

* To install dependencies into an environment

        uv sync
        

> **_NOTE:_**  If `uv sync` did not work try `uv pip install -r pyproject.toml`.

### DB setup
* To create a new migration

        uv run flask --app main db migrate 

* To apply/initialize database

        uv run flask --app main db upgrade

* To load sample data

        uv run flask --app main create-sample-data 

* To load data from a `.csv` file

        uv run flask --app main load-data-from-csv [CSV_FILE_PATH]

> **_NOTE:_**  Prior to this last command it's necessary to run the `create-sample-data` one, as it creates the showreel and user that will be used.

## License

The code for this webapp is provided under the [MIT license](LICENSE.txt).
