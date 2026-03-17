# SI 201 HW4 (Library Checkout System)
# Your name: Bisher Habbab
# Your student id: 17094759
# Your email: habbab@umich.edu
# Who or what you worked with on this homework (including generative AI like ChatGPT):
# If you worked with generative AI also add a statement for how you used it.

# Did your use of GenAI on this assignment align with your goals and guidelines in your Gen AI contract? If not, why? Yes
#
# --- ARGUMENTS & EXPECTED RETURN VALUES PROVIDED --- #
# --- SEE INSTRUCTIONS FOR FULL DETAILS ON METHOD IMPLEMENTATION --- #

from bs4 import BeautifulSoup
import re
import os
import csv
import unittest
import requests  # kept for extra credit parity


# IMPORTANT NOTE:
"""
If you are getting "encoding errors" while trying to open, read, or write from a file, add the following argument to any of your open() functions:
    encoding="utf-8-sig"
"""


def load_listing_results(html_path) -> list[tuple]:
    """
    Load file data from html_path and parse through it to find listing titles and listing ids.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples containing (listing_title, listing_id)
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    with open(html_path, encoding="utf-8-sig") as f:
        soup = BeautifulSoup(f, "html.parser")

    results = []
    title_tags = soup.find_all(attrs={"data-testid": "listing-card-title"})
    for tag in title_tags:
        title = tag.get_text(strip=True)
        id_attr = tag.get("id", "")
        id_match = re.search(r"title_(\d+)", id_attr)
        if id_match:
            listing_id = id_match.group(1)
            results.append((title, listing_id))
    return results
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def get_listing_details(listing_id) -> dict:
    """
    Parse through listing_<id>.html to extract listing details.

    Args:
        listing_id (str): The listing id of the Airbnb listing

    Returns:
        dict: Nested dictionary in the format:
        {
            "<listing_id>": {
                "policy_number": str,
                "host_type": str,
                "host_name": str,
                "room_type": str,
                "location_rating": float
            }
        }
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    file_path = os.path.join("html_files", f"listing_{listing_id}.html")
    with open(file_path, encoding="utf-8-sig") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")

    # Policy number
    pol_match = re.search(
        r"Policy number.*?<span[^>]*>(.*?)</span>", content, re.DOTALL)
    if pol_match:
        raw = pol_match.group(1).strip().replace("\ufeff", "")
        if raw.lower() == "pending":
            policy_number = "Pending"
        elif raw.lower() == "exempt":
            policy_number = "Exempt"
        else:
            policy_number = raw
    else:
        policy_number = "Pending"

    # Host type
    host_type = "Superhost" if "Superhost" in content else "regular"

    # Host name
    host_match = re.search(r"Hosted by ([^<]+)</h2>", content)
    host_name = host_match.group(1).strip() if host_match else ""

    # Room type - based on first h2 subtitle
    h2_tag = soup.find("h2")
    subtitle = h2_tag.get_text(strip=True) if h2_tag else ""
    if "Private" in subtitle:
        room_type = "Private Room"
    elif "Shared" in subtitle:
        room_type = "Shared Room"
    else:
        room_type = "Entire Room"

    # Location rating
    rating = 0.0
    for div in soup.find_all("div", class_="_y1ba89"):
        if div.get_text(strip=True) == "Location":
            nxt = div.find_next_sibling()
            if nxt:
                al_tag = nxt.find(
                    attrs={"aria-label": re.compile(r"[\d.]+ out of")})
                if al_tag:
                    m = re.search(r"([\d.]+) out of",
                                  al_tag.get("aria-label", ""))
                    if m:
                        rating = float(m.group(1))
            break

    return {
        listing_id: {
            "policy_number": policy_number,
            "host_type": host_type,
            "host_name": host_name,
            "room_type": room_type,
            "location_rating": rating
        }
    }
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def create_listing_database(html_path) -> list[tuple]:
    """
    Use prior functions to gather all necessary information and create a database of listings.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples. Each tuple contains:
        (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    listings = load_listing_results(html_path)
    database = []
    for listing_title, listing_id in listings:
        details = get_listing_details(listing_id)
        info = details[listing_id]
        database.append((
            listing_title,
            listing_id,
            info["policy_number"],
            info["host_type"],
            info["host_name"],
            info["room_type"],
            info["location_rating"]
        ))
    return database
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def output_csv(data, filename) -> None:
    """
    Write data to a CSV file with the provided filename.

    Sort by Location Rating (descending).

    Args:
        data (list[tuple]): A list of tuples containing listing information
        filename (str): The name of the CSV file to be created and saved to

    Returns:
        None
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    sorted_data = sorted(data, key=lambda x: x[6], reverse=True)
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Listing Title", "Listing ID", "Policy Number",
                         "Host Type", "Host Name", "Room Type", "Location Rating"])
        for row in sorted_data:
            writer.writerow(row)
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def avg_location_rating_by_room_type(data) -> dict:
    """
    Calculate the average location_rating for each room_type.

    Excludes rows where location_rating == 0.0 (meaning the rating
    could not be found in the HTML).

    Args:
        data (list[tuple]): The list returned by create_listing_database()

    Returns:
        dict: {room_type: average_location_rating}
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    totals = {}
    counts = {}
    for row in data:
        room_type = row[5]
        location_rating = row[6]
        if location_rating == 0.0:
            continue
        if room_type not in totals:
            totals[room_type] = 0.0
            counts[room_type] = 0
        totals[room_type] += location_rating
        counts[room_type] += 1

    averages = {}
    for room_type in totals:
        averages[room_type] = round(totals[room_type] / counts[room_type], 1)
    return averages
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def validate_policy_numbers(data) -> list[str]:
    """
    Validate policy_number format for each listing in data.
    Ignore "Pending" and "Exempt" listings.

    Args:
        data (list[tuple]): A list of tuples returned by create_listing_database()

    Returns:
        list[str]: A list of listing_id values whose policy numbers do NOT match the valid format
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    valid_pattern = re.compile(r"^(20\d{2}-00\d{4}STR|STR-000\d{4})$")
    invalid = []
    for row in data:
        listing_id = row[1]
        policy_number = row[2]
        if policy_number in ("Pending", "Exempt"):
            continue
        if not valid_pattern.match(policy_number):
            invalid.append(listing_id)
    return invalidd
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


# EXTRA CREDIT
def google_scholar_searcher(query):
    """
    EXTRA CREDIT

    Args:
        query (str): The search query to be used on Google Scholar
    Returns:
        List of titles on the first page (list)
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    url = f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    titles = []
    for tag in soup.find_all("h3", class_="gs_rt"):
        text = tag.get_text(strip=True)
        titles.append(text)
    return titles
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


class TestCases(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.search_results_path = os.path.join(
            self.base_dir, "html_files", "search_results.html")

        self.listings = load_listing_results(self.search_results_path)
        self.detailed_data = create_listing_database(self.search_results_path)

    def test_load_listing_results(self):
        # Check that the number of listings extracted is 18.
        self.assertEqual(len(self.listings), 18)
        # Check that the FIRST (title, id) tuple is ("Loft in Mission District", "1944564").
        self.assertEqual(self.listings[0],
                         ("Loft in Mission District", "1944564"))

    def test_get_listing_details(self):
        html_list = ["467507", "1550913", "1944564", "4614763", "6092596"]

        # Call get_listing_details() on each listing id and save results in a list.
        results = [get_listing_details(lid) for lid in html_list]

        # 1) Check that listing 467507 has the correct policy number "STR-0005349".
        self.assertEqual(results[0]["467507"]["policy_number"], "STR-0005349")

        # 2) Check that listing 1944564 has the correct host type "Superhost" and room type "Entire Room".
        self.assertEqual(results[2]["1944564"]["host_type"], "Superhost")
        self.assertEqual(results[2]["1944564"]["room_type"], "Entire Room")

        # 3) Check that listing 1944564 has the correct location rating 4.9.
        self.assertEqual(results[2]["1944564"]["location_rating"], 4.9)

    def test_create_listing_database(self):
        # Check that each tuple in detailed_data has exactly 7 elements.
        for row in self.detailed_data:
            self.assertEqual(len(row), 7)

        # Spot-check the LAST tuple.
        self.assertEqual(self.detailed_data[-1], (
            "Guest suite in Mission District", "467507", "STR-0005349",
            "Superhost", "Jennifer", "Entire Room", 4.8
        ))

    def test_output_csv(self):
        out_path = os.path.join(self.base_dir, "test.csv")

        # Call output_csv() to write the detailed_data to a CSV file.
        output_csv(self.detailed_data, out_path)

        # Read the CSV back in and store rows in a list.
        with open(out_path, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check that the first data row (index 1, after header) matches expected.
        self.assertEqual(rows[1], ["Guesthouse in San Francisco", "49591060",
                                   "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"])

        os.remove(out_path)

    def test_avg_location_rating_by_room_type(self):
        # Call avg_location_rating_by_room_type() and save the output.
        result = avg_location_rating_by_room_type(self.detailed_data)

        # Check that the average for "Private Room" is 4.9.
        self.assertEqual(result["Private Room"], 4.9)

    def test_validate_policy_numbers(self):
        # Call validate_policy_numbers() on detailed_data.
        invalid_listings = validate_policy_numbers(self.detailed_data)

        # Check that the list contains exactly "16204265" for this dataset.
        self.assertEqual(invalid_listings, ["16204265"])


def main():
    detailed_data = create_listing_database(
        os.path.join("html_files", "search_results.html"))
    output_csv(detailed_data, "airbnb_dataset.csv")


if __name__ == "__main__":
    main()
    unittest.main(verbosity=2)
