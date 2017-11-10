# UBC CPSC Lab Availability Finder

A script that reports for each CPSC lab room, the times the lab is booked and free.

# How to run

A pre-run requirement, you need to install the `bs4` and `requests` packages, and use `python 3`. A `requirements.txt` file is is setup so all you need to do is navigate from your shell to the repository root and execute `pip install -r requirements.txt`.

Running is simple as executing the python file with `python main.py` and observing the results. I reccomend not to run the script directly but rather have a cron job that mails the results to you daily.

# Disclaimer

This script scrapes the publicly visible booking pages, and is at best very finicky.
