import requests
import json
from .prompt import REFINE_PROMPT
from typing import List, Optional
from .utils import detect_0
from langchain.tools.base import StructuredTool
from pydantic import BaseModel, Field
from langchain_core.language_models.llms import LLM as LangchainLLM
import pandas as pd
import os
from openai import OpenAI
from .selenium_fetcher import get_html_with_selenium

_TOOL_LANGCHAIN_LLM: Optional[LangchainLLM] = None


class Query(BaseModel):
    query: str = Field()
    content: str = Field()


class Detect(BaseModel):
    url: List[str] = Field()


def load_openai_api_key():
    """Read OpenAI API Key from src/openai.txt file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_key_file = os.path.join(script_dir, "openai.txt")

    try:
        with open(api_key_file, "r", encoding="utf-8") as f:
            api_key = f.read().strip()
        if not api_key:
            raise ValueError("API key file is empty")
        return api_key
    except FileNotFoundError:
        print(f"API key file not found: {api_key_file}")
        return None
    except Exception as e:
        print(f"Error reading API key file: {e}")
        return None


def configure_tool_llm_instance(llm_instance: LangchainLLM):
    global _TOOL_LANGCHAIN_LLM
    _TOOL_LANGCHAIN_LLM = llm_instance


def get_llm_response_for_tool(prompt_content: str) -> str:
    if _TOOL_LANGCHAIN_LLM is None:
        raise RuntimeError(
            "Tool LLM (Langchain instance) not configured. "
            "Call tools.configure_tool_llm_instance(llm_instance) first."
        )

    response = _TOOL_LANGCHAIN_LLM.invoke(prompt_content)

    if hasattr(response, "content"):
        return response.content
    return str(response)


def content_refinement_tool(query: str, content: str) -> str:
    q_prompt = REFINE_PROMPT.format(url=query, content=content)
    refined_content = get_llm_response_for_tool(q_prompt)
    return refined_content


def url_detector_0(url: List[str]) -> List[int]:
    print(f"URL Detector received: {url}")
    classification = detect_0(url)
    return classification


def _normalize_url_for_matching(url_string: str) -> str:
    if not isinstance(url_string, str):
        return ""
    temp_url = url_string.lower().strip()
    if temp_url.startswith("http://"):
        temp_url = "https://" + temp_url[len("http://") :]
    elif not temp_url.startswith("https://") and temp_url:
        temp_url = "https://" + temp_url
    return temp_url.rstrip("/")


# Change the csv file path to the path of the csv file
_CSV_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "template.csv")
)
_CSV_DATA = None


def _load_csv_data():
    global _CSV_DATA
    if _CSV_DATA is None:
        try:
            _CSV_DATA = pd.read_csv(_CSV_FILE_PATH)
            if "url" in _CSV_DATA.columns:
                _CSV_DATA["normalized_csv_url"] = _CSV_DATA["url"].apply(
                    _normalize_url_for_matching
                )
            else:
                print(f"Warning: 'url' column not found in CSV: {_CSV_FILE_PATH}")
                _CSV_DATA = pd.DataFrame()
            print(
                f"Successfully loaded and preprocessed CSV data from: {_CSV_FILE_PATH}"
            )
        except FileNotFoundError:
            print(f"Error: CSV file not found at {_CSV_FILE_PATH}")
            _CSV_DATA = pd.DataFrame()
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            _CSV_DATA = pd.DataFrame()
    return _CSV_DATA


# For comparison, we save the results of the two detectors (PhishLLM and HtmlLLM) in a CSV file, and an XGBoost model is run as shown in 'url_detector_0'.
def url_detector_1(url: List[str]) -> List[int]:
    print(f"URL Detector (1 - CSV 'phish_prediction') received: {url}")
    csv_data = _load_csv_data()
    results = []

    if csv_data.empty or "normalized_csv_url" not in csv_data.columns:
        print(
            "Warning: CSV data is empty or 'normalized_csv_url' column is missing. Defaulting all to malicious."
        )
        return [1] * len(url)

    for input_url_item in url:
        normalized_input_url = _normalize_url_for_matching(input_url_item)
        match = csv_data[csv_data["normalized_csv_url"] == normalized_input_url]

        if not match.empty:
            phish_prediction = str(match.iloc[0].get("phish_prediction", "")).lower()
            if phish_prediction == "benign":
                results.append(0)
            else:
                results.append(1)
        else:
            results.append(1)

    print(f"URL Detector (1 - CSV 'phish_prediction') results: {results}")
    return results


# For comparison, we save the results of the two detectors (PhishLLM and HtmlLLM) in a CSV file, and an XGBoost model is run as shown in 'url_detector_0'.
def url_detector_2(url: List[str]) -> List[int]:
    print(f"URL Detector (2 - CSV 'malicious') received: {url}")
    csv_data = _load_csv_data()
    results = []

    if csv_data.empty or "normalized_csv_url" not in csv_data.columns:
        print(
            "Warning: CSV data is empty or 'normalized_csv_url' column is missing. Defaulting all to malicious."
        )
        return [1] * len(url)

    for input_url_item in url:
        normalized_input_url = _normalize_url_for_matching(input_url_item)
        match = csv_data[csv_data["normalized_csv_url"] == normalized_input_url]

        if not match.empty:
            malicious_value = str(match.iloc[0].get("malicious", "")).lower()
            if malicious_value == "false":
                results.append(0)
            else:
                results.append(1)
        else:
            results.append(1)

    print(f"URL Detector (2 - CSV 'malicious') results: {results}")
    return results


# The HtmlLLM detector code:
# PhishLLM: https://github.com/code-philia/PhishLLM
def is_malicious(html_content, url, llm_model, proxies=None, timeout=15):
    api_key = load_openai_api_key()
    if not api_key:
        print("Failed to read OpenAI API key")
        return None

    client = OpenAI(
        base_url="https://api.openai.com/v1",
        api_key=api_key,
    )

    user_content = f"HTML (first 10000 chars):\n{html_content[:10000]}\n\n"  # you could change this for token saving
    user_content += f"URL: {url}\n\n"
    user_content += "Instructions:\n"
    user_content += "1.  **Primary Focus: Brand Impersonation & Phishing.**\n"
    user_content += f"    * Carefully compare the given URL ({url}) with official domains of any mentioned or implied brands.\n"
    user_content += "    * HIGHLY SUSPICIOUS if a known brand appears on generic/free hosting platforms (e.g., `brand-name.github.io`, `s3-bucket-name.s3.amazonaws.com/brand/`, `*.netlify.app`, `*.vercel.app`, etc.) especially for logins, updates, or downloads. Example: `trezor-official.github.io` is likely malicious if asking for secrets.\n"
    user_content += "    * Look for typosquatting (e.g., 'g00gle.com' for 'google.com', 'trez0r.com' for 'trezor.io', etc.).\n"
    user_content += (
        "    * Check if forms submit data to a different or suspicious domain.\n\n"
    )

    user_content += "2.  **Software Downloads:** Deem malicious if not from the official vendor, a major app store, or a reputable software archive, OR if the download URL itself is clearly unofficial or deceptive.\n\n"

    user_content += "3.  **Deceptive Spam:** Consider if the page's primary purpose is one of the following:\n"
    user_content += "    * Aggressively pushing misleading advertisements or redirecting to ad-heavy, low-value sites.\n"
    user_content += "    * Low-quality, auto-generated, or keyword-stuffed content primarily for SEO manipulation (content farm) with little genuine user value.\n"
    user_content += "    * Promoting scams, dubious products/services with outrageous or unverifiable claims.\n"
    user_content += "    * This is distinct from legitimate sites with standard advertising or marketing content. The intent must be clearly deceptive or the user value extremely low.\n\n"

    user_content += "4.  **General URL Red Flags:** Analyze for misleading subdomains (e.g., 'login.google.com.security-alert.com'), excessive length, or heavy obfuscation designed to deceive, that aren't already covered by brand impersonation (point 1).\n\n"

    user_content += "5.  **Context & Avoiding False Positives (Crucial):**\n"
    user_content += "    * **Re-confirm:** The checks for Brand Impersonation (1), Malicious Downloads (2), and Deceptive Spam (3) should be the primary drivers for a 'True' classification.\n"
    user_content += "    * DO NOT classify as malicious: Well-known search engines (Google, Baidu, etc.), popular forums/communities (Reddit, StackOverflow, 52pojie, v2ex, etc.), wikis (Wikipedia, etc.), official brand support/documentation pages, or legitimate crypto/gaming item trading sites UNLESS they *directly and clearly* meet the criteria in points 1, 2, or 3 (e.g., a forum page *itself* hosting a phishing form with a deceptive URL, or a page that is *undeniably* deceptive spam as defined in point 3).\n"
    user_content += "    * The URL is the most critical piece of evidence, especially if HTML is limited.\n\n"
    user_content += "Is this webpage malicious based on all the above?"

    prompt = [
        {
            "role": "system",
            "content": "You are a security expert AI. Your task is to determine if a webpage is malicious. Malicious includes: phishing, malware distribution, **deceptive Spam (e.g., content farms, aggressive/misleading ad pages, scam promotions)**, and deceptive brand impersonation. A page is NOT malicious *solely* because it's a forum, wiki, search engine, official site, or discusses sensitive topics (e.g., security, crypto), unless it *directly* exhibits clear evidence of one of the aforementioned malicious types (e.g., a fake login on a deceptive URL, clear malware, or is primarily a deceptive/low-value spam page) on the *specific page and URL provided*. Brand impersonation on generic hosting (like `*.github.io`, `*.gitbook.io`, `s3.amazonaws.com/..., etc.`) for sensitive actions (logins, downloads) is a strong red flag. Respond ONLY with 'True' (malicious) or 'False' (non-malicious). No explanation.",
        },
        {"role": "user", "content": user_content},
    ]

    try:
        response = client.chat.completions.create(
            model=llm_model,
            messages=prompt,
            temperature=0.1,
            max_tokens=10,
            timeout=timeout,
        )
        result = response.choices[0].message.content.strip()
        # Ensure the result is only True or False
        if "True" in result:
            return True
        else:
            return False
    except Exception as e:
        return None  # Return None on error to indicate no determination was made


# This detector is an example showing how to integrate a new URL detector into our agent framework.
def url_detector_4(url: List[str], timeout=30, fetch_method="requests") -> List[int]:
    print(f"URL Detector (4) received: {url} (Using fetch method: {fetch_method})")

    final_results = [None] * len(url)
    tasks_to_process = []
    llm_model = "gpt-4.1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    # Stage 1: Get HTML content
    for idx, u in enumerate(url):
        html_content = None
        if fetch_method == "selenium":
            html_content = get_html_with_selenium(u, total_timeout=timeout)
        else:  # default 'requests'
            try:
                response = requests.get(
                    u,
                    timeout=(timeout / 2),
                    headers=headers,
                    allow_redirects=True,
                    verify=True,
                    stream=False,
                )
                response.raise_for_status()
                html_content = response.text
            except requests.Timeout:
                print(f"REQUESTS: Timeout when fetching URL {u}")
            except requests.ConnectionError:
                print(f"REQUESTS: Connection error when fetching URL {u}")
            except requests.HTTPError as e:
                print(f"REQUESTS: HTTP error {e.response.status_code} for URL {u}: {e}")
            except requests.RequestException as e:
                print(f"REQUESTS: Failed to fetch content for URL {u}: {e}")

        if html_content is not None:
            tasks_to_process.append({"idx": idx, "url": u, "html": html_content})
        else:
            final_results[idx] = -1

    # Stage 2: Process successfully fetched pages with the LLM.
    llm_timeout = timeout / 2 if fetch_method == "requests" else 15
    for task in tasks_to_process:
        idx = task["idx"]
        is_mal = is_malicious(
            html_content=task["html"],
            url=task["url"],
            llm_model=llm_model,
            timeout=llm_timeout,
        )

        if is_mal is True:
            final_results[idx] = 1
        elif is_mal is False:
            final_results[idx] = 0
        else:
            final_results[idx] = -1

    final_results = [res if res is not None else -1 for res in final_results]

    print(f"URL Detector (4 - LLM-based) results: {final_results}")
    return final_results


def return_tools():
    # Remove the comment from one of the following lines to select a detector:
    # current_url_detector_function = url_detector_0  # XGBoost
    # current_url_detector_function = url_detector_1       # PhishLLM (batch)
    current_url_detector_function = url_detector_2  # HtmlLLM (batch)
    # current_url_detector_function = url_detector_4       # HtmlLLM single query example
    tools = [
        StructuredTool(
            name="content_refinement_tool",
            func=content_refinement_tool,
            description="""This tool takes a query and content string as input. It uses a predefined refinement prompt to analyze and improve the content for safety, clarity, and reliability. 
            The tool ensures that any potentially harmful or misleading elements in the content are identified and corrected. 
            It interacts with a backend API or service to perform the refinement.
            Input:
                query (str): The URL or identifier of the context in which the content was retrieved. This helps provide context for refinement.
                content (str): The primary content to be refined, typically returned from an AI search query.
            Output:
                refined_content (str): The output of refinement, which consists of CoT steps and the final output.
            """,
            args_schema=Query,
        ),
        StructuredTool(
            name="url_detector",
            func=current_url_detector_function,
            description="""
            This tool accepts a list of URLs and evaluates their safety using a detector. 
            It classifies each URL into two categories: malicious and benign. The tool helps identify malicious URLs, including phishing, malware, scams, or other unreliable sources, ensuring a reliable and safe evaluation of referenced links.
            Input:
                url (List[str]): A list of URLs (strings) that need to be classified for safety. These URLs typically come from the references of an AI search result. Even though somtimes we only detect 1 url, you should **always** pass a list input 
            Output:
                classification (List[int]): A list of integers corresponding to the classification of each input URL. The output uses a predefined encoding, where:
                    0 indicates the URL is benign.
                    1 indicates the URL is malicious.
                    -1 indicates the URL 30s timeout during testing.
            """,
            args_schema=Detect,
        ),
    ]
    return tools
