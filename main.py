from bs4 import BeautifulSoup
import csv
import fire
import requests

# default behavior
K_INPUT_CSV = "input.csv"
K_OUTPUT_CSV = "output.csv"
K_MAX_RETRIES = 3
K_VERBOSE = True


def scrape_url(soup: BeautifulSoup):
    company_name_selector = "div.space-y-3 > div > h1"
    company_tagline_selector = (
        "div.space-y-3 > div.prose.hidden.max-w-full.font-extralight.md\:block > div"
    )
    abstract_selector = "section:nth-child(3) > div > p"
    jobs_selector = "nav > div:nth-child(2) > span"
    year_founded_selector = "a:nth-child(1) > div > div > span"
    status_selector = "a:nth-child(2) > div > div > div.align-center.flex.flex-row.flex-wrap.gap-x-2.gap-y-2 > div > div"

    name_el = soup.select_one(company_name_selector)
    tagline_el = soup.select_one(company_tagline_selector)
    abstract_el = soup.select_one(abstract_selector)
    year_el = soup.select_one(year_founded_selector)
    jobs_el = soup.select_one(jobs_selector)
    status_el = soup.select_one(status_selector)

    output = {
        "name": name_el.text.strip() if name_el else "",
        "tagline": tagline_el.text.strip() if tagline_el else "",
        "abstract": abstract_el.text.strip() if abstract_el else "",
        "year": year_el.text.strip() if year_el else "",
        "founded": "",
        "jobs": jobs_el.text.strip() if jobs_el else "",
        "status": status_el.text.strip() if status_el else "",
        "location": "",
        "team_size": "",
    }

    # extract extra information from the table element
    table_el = soup.select_one("div:nth-child(2) > div > div.space-y-0\.5")
    if table_el:
        for row in table_el.find_all("div", class_="flex flex-row justify-between"):
            key = row.find_all("span")[0].text.strip().rstrip(":")
            value = row.find_all("span")[1].text.strip()
            if key == "Founded":
                output["founded"] = value
            elif key == "Location":
                output["location"] = value
            elif key == "Team Size":
                output["team_size"] = value

    return output


def scrape_all_urls(urls: list[str], k_max_retries: int, k_verbose: bool = False):
    dataset = []
    for url in urls:
        for _ in range(k_max_retries):
            response = requests.get(url)
            if response.status_code == 200:
                break
        else:
            if k_verbose:
                print(f"Failed to fetch {url}")
            continue
        soup = BeautifulSoup(response.text, "html.parser")

        for _ in range(k_max_retries):
            output = scrape_url(soup=soup)
            if output:
                break
        else:
            if k_verbose:
                print(f"Failed to scrape {url}")
            continue
        output["url"] = url
        if k_verbose:
            print(f"Successfully scraped: {url}")
        dataset.append(output)

    return dataset


def load_urls_from_csv(file_name: str) -> list[str]:
    with open(file_name, "r", newline="") as csvfile:
        reader = csv.reader(csvfile)

        urls: list[str] = [row[0] for row in reader if row[0] != ""]
    return urls


def save_to_csv(file_name: str, data: list[dict]):
    with open(file_name, "w", newline="") as csvfile:
        headers = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def main(
    input_csv=K_INPUT_CSV,
    output_csv=K_OUTPUT_CSV,
    max_retries=K_MAX_RETRIES,
    verbose=K_VERBOSE,
):
    """Scrape YC startup information from a csv list of URLs.

    Args:
        input_csv (str): Input csv file containing a list of URLs.
        output_csv (str): Output csv file to save the scraped data.
        max_retries (int): Maximum number of retries for fetching and scraping a URL.
        verbose (bool): Whether to print verbose output.

    Example with Fire:
        python3 main.py
        python3 main.py --input_csv sample_input.csv --output_csv your_output.csv --verbose False
    """
    urls = load_urls_from_csv(file_name=input_csv)
    dataset = scrape_all_urls(urls=urls, k_max_retries=max_retries, k_verbose=verbose)
    save_to_csv(file_name=output_csv, data=dataset)


if __name__ == "__main__":
    fire.Fire(main)
