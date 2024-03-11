import csv
from dotenv import load_dotenv
import os
import json
import fire
from pprint import pprint

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import JSONLoader

load_dotenv(".env.local")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
K_TOP = 2


def load_from_csv(file_name: str) -> list[dict]:
    with open(file_name, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]
    return data


def document_loader(file_name: str) -> list:
    with open("output.json", "r") as f:
        data = json.load(f)

    loader = JSONLoader(
        file_path=file_name,
        jq_schema=".[] | .tagline",
        text_content=False,
    )

    documents = loader.load()
    for d in documents:
        for c in data:
            if d.page_content == c["tagline"]:
                d.metadata = c

    return documents


def main(
    query: str,
    k_top: int = K_TOP,
):
    documents = document_loader("output.json")
    db = Chroma.from_documents(documents, OpenAIEmbeddings())
    docs = db.similarity_search(query, k_top)

    # terminal color yellow
    print("\033[93m")
    for doc in docs:
        pprint(doc)
        print()
    # terminal color reset
    print("\033[0m")


if __name__ == "__main__":
    fire.Fire(main)
