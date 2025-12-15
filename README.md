# GOA File Distribution

Automates distribution of files (and optional archival copies) from a central input folder to multiple network destinations according to JSON configuration.

Key points
- Monitors a central inputs folder and moves files to their configured destination(s).
- Supports date-based destination replacement tokens (YYYY, YY, MM, DD).
- Supports single-string `destination` (existing behavior) and list `destination` for primary + archival copies (new feature).

New: list-style destinations
--------------------------------
You can now configure a `destination` as either a string (existing behavior) or a list of strings. When a list is used, the first element is treated as the primary destination (the file is moved or the output is written there). Any additional elements are treated as secondary destinations — the code will create a copy of the file into those locations for archival or backup purposes.

Example JSON snippet (new list-destination):

```json
{
	"example_use_case": {
		"inputs": {
			"name": "Example_*.pdf",
			"destination": [
				"\\\\NT2KWB972SRV03\\SHAREDATA\\Primary\\Example\\YYYY\\MM YYYY\\",
				"\\\\ARCHIVE_SERVER\\SHARE\\Example\\Archives\\YYYY\\MM YYYY\\"
			]
		}
	}
}
```

Behavior
- Primary (first) destination: the original file is moved here (or extracted here for zip outputs).
- Secondary destinations: copies of the original file (or generated output file) are written here using `shutil.copy2` to preserve timestamps.

Notes and recommendations
- Directory creation on network shares is best-effort. If the script cannot create a remote directory because of permission/network issues, it will log a warning and continue.
- For zipped outputs the implementation copies the original zip to secondary destinations (archive). If you prefer copying the extracted folder contents instead, let me know and I can change the semantics.

Running the project
--------------------
- Install dependencies: `pip install -r requirements.txt`
- Run manually: `python main.py` (there's a `--dry-run` flag in the refactored `main.py` to preview behavior without moving files).

Testing
-------
I added a small pytest test to validate the list-destination behavior and dry-run-friendly operations. Run tests with:

```sh
pip install -r requirements.txt
pytest -q
```

If you'd like, I can also add a CLI example and a sample JSON configuration file dedicated to testing.
