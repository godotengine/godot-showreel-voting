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


## Requirements

For this project I'm trying [uv](https://docs.astral.sh/uv/),a python project manager. The idea is that this tool should replace the need for virtualenvironments and package managers with a a single one.

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

## License

The code for this webapp is provided under the [MIT license](LICENSE.txt).
