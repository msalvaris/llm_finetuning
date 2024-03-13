# LLM Finetuning with llama-factory and Grobid

This repository contains code and resources for finetuning large language models (LLMs) using the llama-factory library and the Grobid tool for extracting structured data from scientific publications.

## Overview

The goal of this project is to finetune LLMs like LLaMA, Misteal, etc. on a corpus of scientific publications, with the aim of improving their performance on tasks related to scientific literature, such as summarization, question answering, and information extraction.

The workflow involves the following steps:

1. **Data Collection**: Gather a dataset of scientific publications in PDF format.
2. **Data Preprocessing**: Use Grobid to extract structured data (title, abstract, body text, etc.) from the PDF files.
3. **QA extractiong**: Use a local model to generate QA pairs
4. **Model Finetuning**: Use llama-factory to finetune a base LLM on the preprocessed scientific corpus.

## Requirements

- Python 3.8+
- llama-factory
- Grobid

## Installation

1. Clone this repository:

```
git clone https://github.com/msalvaris/llm_finetuning
cd llm_finetuning
```

2. Install the required Python packages:

```
pip install -r requirements.txt
```

3. Run the Grobid docker container: [https://grobid.readthedocs.io/en/latest/Install-Grobid/](https://grobid.readthedocs.io/en/latest/Install-Grobid/)

```
make run_grobid
```
4. Build and run the llama-factory docker container

```
make build_lfactory
make run_lfactory
```

4. Run the processing script

```
python generate_qa.py
```

4. **Model Finetuning**: Use the llama-factory to finetune a base LLM on the preprocessed pdf.

```
make fine_tune
```

5. **Evaluation**: Evaluate the finetuned model's performance

```
make cli
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have any improvements or bug fixes.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- The llama-factory library: [https://github.com/hiyouga/LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)
- The Grobid tool: [https://github.com/kermitt2/grobid](https://github.com/kermitt2/grobid)