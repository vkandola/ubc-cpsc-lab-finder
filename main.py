#!/usr/bin/env python

"""
Author: Vishav Kandola
Source hosted @ https://www.github.com/vkandola/ubc-cpsc-lab-finder
Script output viewable @ www.vkandola.me/projects/lab-checker/output.txt

Some potential future improvements:
- Add parallelism to https requests (mindful of not spamming requests..)
- Add proper handling of bookings that occur on multiple days with different end times

Notes about this script:
- Will likely break if the style sheets, URLs or or DOM structure changes changes
- Is conservative in the time estimates, e.g. a 10-11AM lab doesn't end at 10:50AM although that is likely the case
"""

import re

import requests
from bs4 import BeautifulSoup

# URLs
base_url = "https://www.cs.ubc.ca"
calendar_url = base_url + "/students/undergrad/services/lab-availability"

# Compiled Regex
normal_time = re.compile("([1-9]|1[012]):([0-5][0-9])([ap])m")

# Some strings
free_slot_name = "Open"
booked_slot_name = "Booked"

# Some configurable flags
labs_end_ten_minutes_early = False
minimum_gap_between_labs = 10 # in minutes

# HTML Parser helpers, broken up into pages
def get_all_lab_rooms():
    """
    Fetches all the visible lab rooms and returns a name -> url dict.
    """
    soup = BeautifulSoup(requests.get(calendar_url).text, 'html.parser')

    lab_calendars_html = soup.select(".content > .inline-block-right > ul")[1]
    lab_rooms = dict([(link.text, base_url + link['href']) for link in lab_calendars_html.select("a")])

    return lab_rooms


def get_booking_end(name, url, start):
    """
    Fetches the lab room booking's end date.

    Assumes a lab booking has the same end time throughout the week, which may not be true.
    """
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    end_date_12hr = soup.select(".date-display-end")[0].text.lower()
    if name == 'ACM contest':
        return 24*60
    groups = normal_time.match(end_date_12hr).groups()

    hour = int(groups[0])
    if hour == 12:
        hour -= 12
    if groups[2] == 'p':
        hour += 12
    minute = int(groups[1])

    return hour * 60 + minute - (10 if labs_end_ten_minutes_early else 0)


def get_bookings_for_lab(lab, url):
    """
    Fetches all the bookings for a lab room and returns a list of (name, start, end) tuples.
    """
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    today = soup.select(".today")[0]
    booking_rows = zip(today.select("a"), today.select("span"))
    today_slots = [(link.text, time_to_minutes(time.text), base_url + link['href']) for link, time in booking_rows]

    # Do an additional fetch for the end times, since they aren't explicitly listed on the lab calendar page.
    today_slots = [(name, start, get_booking_end(name, url, start)) for name, start, url in today_slots]

    # The bookings are already sorted by their start time for us.
    return today_slots


def time_to_minutes(time):
    time_split = time.split(':')
    return int(int(time_split[0]) * 60 + int(time_split[1]))


def minute_to_time(minutes):
    hour = minutes // 60
    minute = minutes % 60
    return ("0" if hour < 10 else "") + str(hour) + ":" + ("0" if minute < 10 else "") + str(minute)


def add_free_slots(b):
    """
    Takes the bookings and adds pseudo bookings for the free time slots, returning the resulting list of (name, start)
    tuples.

    Assumes (1) Labs are open 24 hours, which is generally true except for the occasional fire, flood or maintenance
                    that occurs
            (2) That lab bookings don't overlap
            (3) That a X to Y time lab is strictly free at time Y, not Y - 10 minutes (to be nice to late running labs),
                    note that this is configurable via global variable labs_end_ten_minutes_early
            (4) Labs are never cancelled, which may not be true during the class's midterm week or holidays
    """

    start_minute = 0
    end_minute = 24 * 60

    bookings = []

    cur_minute = start_minute

    while cur_minute <= end_minute:
        if len(b) == 0:
            bookings.append((free_slot_name, cur_minute, end_minute))
            break

        booking_name, booking_start, booking_bend = b[0]

        if cur_minute < booking_start and booking_start - cur_minute > minimum_gap_between_labs:
            bookings.append((free_slot_name, cur_minute, booking_start))
        bookings.append(b.pop(0))
        cur_minute = booking_bend

    return bookings


def run():
    labs = get_all_lab_rooms()
    lab_reservations = dict([(x, get_bookings_for_lab(x, url)) for x, url in labs.items()])
    for lab, bookings in lab_reservations.items():
        free_slots = add_free_slots(bookings)
        print("%s:" % lab)
        for name, start, end in free_slots:
            displayed_name = name if name == free_slot_name else booked_slot_name
            print("%10s %5s to %5s" % (displayed_name, minute_to_time(start), minute_to_time(end)))


if __name__ == '__main__':
    run()
