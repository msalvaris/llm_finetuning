"""Script to process pdf to generate QA data
"""


import json
import re
from typing import Dict, Generator, List, Pattern, Tuple, Union

import grobid_tei_xml
import requests
from bs4 import BeautifulSoup
from grobid_client.grobid_client import GrobidClient
from rich.progress import track

# Define a list of patterns to replace
patterns = [
        r'\d+e\d+'
]


def post_process(text: str) -> str:
    """
    Post-process the given text by replacing certain characters with other characters.

    Args:
        text (str): The input text to be processed.

    Returns:
        str: The processed text.
    """
    output = text.replace('À', '-')
    output = output.replace('¼', '=')
    output = output.replace('þ', '+')
    output = output.replace('Â', 'x')
    output = output.replace('$', '~')
    output = output.replace('−', '-')
    output = output.replace('–', '-')

    # Replace characters based on the patterns list
    for pattern in patterns:
        output = re.sub(pattern, lambda match: match.group().replace('e', '-'), output)

    return output


def get_xml_nodes_body(soup: object, use_paragraphs: bool = True, verbose: bool = False) -> List[object]:
    """
    Get the XML nodes from the <body> section of the given BeautifulSoup object.

    Args:
        soup (object): The BeautifulSoup object representing the XML document.
        use_paragraphs (bool, optional): Whether to use <p> tags or <s> tags. Defaults to True.
        verbose (bool, optional): Whether to print the list of nodes. Defaults to False.

    Returns:
        List[object]: A list of XML nodes from the <body> section.
    """
    nodes = []
    tag_name = "p" if use_paragraphs else "s"

    for child in soup.TEI.children:
        if child.name == 'text':
            nodes.extend([subsubchild for subchild in child.find_all("body") for subsubchild in subchild.find_all(tag_name)])

    if verbose:
        print(str(nodes))

    return nodes


def make_request(text: str) -> Union[Dict, None]:
    """
    Make a request to an API endpoint for text completions.

    Args:
        text (str): The input text for generating question-answer pairs.

    Returns:
        Union[Dict, None]: The API response as a dictionary, or None if the request failed.
    """
    # The URL for the API endpoint (this example is for text completions)
    url = "http://localhost:7860/v1/chat/completions"

    # The query to generate question-answer pairs from the input text
    query = f"Given the following text create 5 question answer pairs. I don't want the answers to be multiple choice. The answer should appear directly below the question. Question should start with Q: and answer with A: \n\n {text}"

    # Headers to provide your API key for authentication
    headers = {
        "Content-Type": "application/json",
    }

    # The data payload for your request, adjust parameters as needed
    data = {
        "model": "string",
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "tools": [],
        "do_sample": True,
        "temperature": 0,
        "top_p": 0,
        "n": 1,
        "max_tokens": 0,
        "stream": False
    }

    # Make the API request
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Checking if the request was successful
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def _parse(response: Dict, extra_input: str) -> Generator[Dict[str, str], None, None]:
    """
    Parse the response from an API call and yield question-answer pairs in a dictionary format.

    Args:
        response (Dict): The response from the API call.
        extra_input (str): Additional input text.

    Yields:
        Dict[str, str]: A dictionary containing the question, input, and output.
    """
    if response:
        # Extract output from response
        contentstr = response["choices"][0]['message']['content'].strip()

        for qa_pair in contentstr.split("Q:"):
            try:
                # Split the question and answer
                question, answer = qa_pair.split("A:")

                # Yield the question-answer pair in a dictionary format
                yield {
                    "instruction": question.strip(),
                    "input": "",
                    "output": answer.strip()
                }
            except ValueError:
                print("Skipping")

def main():
     # Path to the input PDF file
    input_path = ".data/2403.03507.pdf"
    save_file = ".data/galore_qa.json"

    # Define a configuration dictionary for GROBID client
    config_dict = {
        "grobid_server": "http://localhost:8070",  # URL of GROBID server
        "batch_size": 1000,  # Batch size for processing documents
        "sleep_time": 5,  # Sleep time between requests
        "timeout": 60,  # Timeout for requests
        "coordinates": ["persName", "figure", "ref", "biblStruct", "formula", "s"]  # XML tags to extract coordinates for
    }

    # Save the configuration dictionary to a JSON file
    with open("grobid_config.json", "w", encoding="utf8") as f:
        json.dump(config_dict, f)

    # Create a GROBID client instance with the configuration file
    client = GrobidClient(config_path="./grobid_config.json")

    # Process the PDF file using GROBID client
    _, _, text = client.process_pdf("processFulltextDocument",
                                                input_path,
                                                consolidate_header=True,
                                                consolidate_citations=False,
                                                segment_sentences=False,
                                                tei_coordinates=False,
                                                include_raw_citations=False,
                                                include_raw_affiliations=False,
                                                generateIDs=True)

    # Parse the GROBID output XML
    doc_biblio = grobid_tei_xml.parse_document_xml(text)

    # Initialize a list to store examples
    examples = []

    # Process the abstract and add examples to the list
    response = make_request(doc_biblio.abstract)
    examples.extend(list(_parse(response, doc_biblio.abstract)))

    # Parse the XML content using BeautifulSoup
    soup = BeautifulSoup(text, 'xml')

    # Get the text blocks from the <body> section
    text_blocks_body = get_xml_nodes_body(soup)

    # Initialize a list to store passages
    passages = []

    # Flag to include coordinates or not
    coordinates = False

    # Extract passages from the text blocks and add them to the list
    passages.extend([
        {
            "text": post_process(''.join(text for text in paragraph.find_all(text=True) if
                                         text.parent.name != "ref" or (
                                                 text.parent.name == "ref" and text.parent.attrs[
                                             'type'] != 'bibr'))),
            "section": "<body>",
            "subSection": "<paragraph>",
            "passage_id": str(paragraph_id),
            "coordinates": paragraph['coords'] if coordinates and paragraph.has_attr('coords') else ""
        }
        for paragraph_id, paragraph in enumerate(text_blocks_body)
    ])

    # Process each passage and add examples to the list
    for passage in track(passages, description="Processing passages..."):
        response = make_request(passage["text"])
        examples.extend(list(_parse(response, passage["text"])))

    # Save the examples to a JSON file
    with open(save_file, "w", encoding="utf8") as f:
        json.dump(examples, f, indent=4)



if __name__=="__main__":
    main()
