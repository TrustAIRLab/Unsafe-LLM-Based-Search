# Unsafe-LLM-Based-Search

Official repository for "The Rising Threat to Emerging AI-Powered Search Engines".

The XGBoost-detector is slightly different in usage compared to the HTML-detector (ours) and the PhishLLM-detector, as it was written before the major revision.

## **Introduction**

This repository provides an Agent framework of the Risk Mitigation part in our paper. The XGBoost-detector and PhishLLM-detector are for comparison. The code for the PhishLLM-detector can be found at: https://github.com/code-philia/PhishLLM

## **Project Structure**

```
agent_defense/
├── src/
│   └──agent.py             # build_agent
│   └──llm.py             # a discarded trail of using some special API call
│   └──prompt.py             # prompt
│   └──tool.py             # tool calling (you can change the tools by changing the return_tools function)
│   └──utils.py             # XGBoost-detector method
│   └──selenium_fetcher.py             # HTML-detector method for getting HTML content
│   └──XGBoostClassifier.pickle.dat             # XGBoost-detector model weight
└── main.py # run the defense (it contains the HTML-detector (ours))
```

## How to Run

### Setup

1. Install all required packages according to your environment.
2. Enter the `openai_api_key` and `openai_base_url` parameters within the `main.py` file.
3. Enter the `base_url` and `api_key` parameters in the `is_malicious` function within the `main.py` file.

### For Batch Comparison

1. Prepare the batch_result.csv in the format below (You need to use the `is_malicious` function to obtain the results and write them to this CSV file for batch comparison):
    
    `phish_prediction` is the result of the PhishLLM-detector, while `malicious` is the result of our method, the HTML-detector.
    
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
    
3. Run
    
    ```bash
    python main.py --input_file your_input.json --model_name your_model_name
    ```
    

### For Single Query
You need to integrate the `is_malicious` function into the `tool.py` file according to your AIPSE’s output format. We provide an example in `tool.py` as the `url_detector_4` function.
