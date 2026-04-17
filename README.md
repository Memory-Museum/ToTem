# ToTEM

ToTEM is a Flask app that allows users at Berea College to upload stories and images, which are then accessible via unique URLs and QR codes. This is a simple application for a project, and is not meant to be duplicated without adding security measures, or a different database to handle concurrency. It serves as a digital storytelling platform where items can be linked to digital information through the generated QR codes.

## Tech Stack
- **Backend Framework**: [Flask](https://flask.palletsprojects.com/) (Python)
- **Database**: [TinyDB](https://tinydb.readthredocs.io/) (Lightweight document-oriented database)
- **QR Code Generation**: [Flask-QRcode](https://pypi.org/project/Flask-QRcode/)
- **Frontend**: HTML5, CSS, JavaScript
- **Package Manager**: [uv](https://github.com/astral-sh/uv)


### Prerequisites
- Python 3.12+
- `uv` installed (Installation guide: https://docs.astral.sh/uv/getting-started/installation/)


  **Sync dependencies**:
    This command will create a virtual environment and install all locked dependencies.
    ```bash
    uv sync
    ```

### Running the Application
To start the Flask development server:

```bash
uv run python app.py
```


### Managing Dependencies with `uv`

- **Add a new package**:
    ```bash
    uv add <package-name>
    ```

- **Remove a package**:
    ```bash
    uv remove <package-name>
    ```

- **Update packages**:
    ```bash
    uv lock --upgrade
    ```

## Hosting on server

Currently set up to port 5001. Server's firewall needs to allow incoming traffic to this port.

Students will need to be on the same wifi network.