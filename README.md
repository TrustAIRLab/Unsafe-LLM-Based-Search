Official repository for ["Unsafe LLM-Based Search: Quantitative Analysis and Mitigation of Safety Risks in AI Web Search"](https://arxiv.org/abs/2502.04951).

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![arXiv](https://img.shields.io/badge/arXiv-2502.04951-b31b1b.svg)](https://arxiv.org/abs/2502.04951)

![Teaser Preview](teaser.png)

## **Introduction**

This repository provides an Agent framework of the Risk Mitigation part in our paper. The XGBoost-detector and PhishLLM-detector are for comparison. The code for the PhishLLM-detector can be found at: https://github.com/code-philia/PhishLLM

## **Project Structure**

```
agent_defense/
├── src/
│   └──agent.py                     # build_agent
│   └──llm.py                       # a discarded trail of using some special API call
│   └──prompt.py                    # prompt
│   └──tools.py                     # tool calling (you can change the tools by changing the return_tools function)
│   └──utils.py                     # XGBoost-detector method
│   └──selenium_fetcher.py          # HtmlLLM-detector method for getting HTML content (optional)
│   └──template.csv                 # template for basic test
│   └──XGBoostClassifier.pickle.dat # XGBoost-detector model weight
├── template.json                   # template for basic test
├── prompt_defense.py               # prompt-based defense code
└── main.py                         # run the defense (it contains the HtmlLLM-detector (ours))
```

## How to Run

### Setup

1. Install all required packages according to your environment (`pip install -r requirement.txt`).
2. Enter the `openai_api_key` and `openai_base_url` parameters within the `main.py` file.
3. Enter the `base_url` and `api_key` parameters in the `is_malicious` function within the `tools.py` file.
4. Enter the `base_url` and `api_key` parameters in the `prompt_defense.py` file.

### For Batch Comparison (Shown in Our Paper)

1. Prepare the batch_result.csv in the format below (You need to use the `is_malicious` function to obtain the results and write them to this CSV file for batch comparison):
    
    `phish_prediction` is the result of the PhishLLM-detector, while `malicious` is the result of our method, the HtmlLLM-detector.
    
    ```
    url,phish_prediction,malicious
    https://example0.com,benign,False
    https://example1.com,benign,True
    ```
    
2. Prepare the input.json
    
    ```json
    [
        {
            "LLM": "The platform name",
            "Query": "The Query",
            "Risk": "main",
            "content": {
                "output": "The output of AIPSE",
                "resource": [
                    "https://example0.com",
                    "https://example1.com"
                ]
            }
        }
    ]
    ```
    
3. BasicTest Run

     We provide all template files. To run a basic test, you can simply run:
    ```bash
    python main.py
    python prompt_defense.py
    ```
     after entering the parameters in the main.py, tools.py, and prompt_defense.py files. 
     
     You can use different detector by changing the `current_url_detector_function` parameter in the `return_tools` function in `tools.py` file. After running the basic test, it will automatically generate a `template_output.json` file for verification.
    

### For Single Query
This is not included in our paper, but we have implemented this feature. You can directly test it by changing the `return_tools` function in `tools.py`.

## Citation
```
@inproceedings{UnsafeSearch2025,
      title={Unsafe LLM-Based Search: Quantitative Analysis and Mitigation of Safety Risks in AI Web Search}, 
      author = {Zeren Luo and Zifan Peng and Yule Liu and Zhen Sun and Mingchen Li and Jingyi Zheng and Xinlei He},
      booktitle = {{34th USENIX Security Symposium (USENIX Security 25)}},
      publisher = {USENIX},
      year = {2025}
}
```