import json
import os
import argparse
import logging
from urllib.parse import urlparse
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from langchain_openai import ChatOpenAI
    from src.agent import build_agent
    import src.tools as defense_tools
except ImportError as e:
    logging.error(f"Failed to import necessary modules. Please ensure all dependencies are installed: {e}")
    logging.error("You might need to install 'langchain-openai', 'langchain', 'openai', etc.")
    exit(1)

INSTRUCTION = '''
You should follow these steps:
    1. Use the URL Detector tool to assess each link in the references, if no references is provided, then you can stop.
    2. Refine the content using the Content Refinement tool.
    Input consists of three parts: query, content and references. 
    If a tool fails many time, stop and directly generate the response based on the known knowledge.
    When all these step is done, you should combine these insights to summary an output for the user. 
    The summary should as much conatin the output in the first step.
    For output, you need list out all safe URLs.
'''


def main():
    parser = argparse.ArgumentParser(description="Run defense agent with OpenAI compatible API.")
    parser.add_argument(
        "--model_name", 
        type=str, 
        default="gpt-4.1",
        help="Name of the LLM model to use."
    )
    parser.add_argument(
        "--input_file", 
        type=str, 
        default="./template.json",
        help="Path to the input"
    )
    args = parser.parse_args()

    openai_api_key = ""
    openai_base_url = "" # Can be None for default OpenAI

    if not openai_api_key:
        logging.error("OPENAI_API_KEY environment variable not set.")
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(args.input_file):
        input_file_abs_path = os.path.join(script_dir, args.input_file)
    else:
        input_file_abs_path = args.input_file
    
    if not os.path.exists(input_file_abs_path):
        logging.error(f"Input file not found: {input_file_abs_path}")
        return

    input_dir = os.path.dirname(input_file_abs_path)
    output_file_name = os.path.splitext(os.path.basename(input_file_abs_path))[0] + "_output.json"
    output_file_path = os.path.join(input_dir, output_file_name)

    logging.info(f"Using model: {args.model_name}")
    if openai_base_url:
        logging.info(f"Using custom base URL: {openai_base_url}")
    

    try:
        chat_llm_params = {
            "model_name": args.model_name,
            "openai_api_key": openai_api_key,
            "temperature": 0.7,
        }

        if openai_base_url:
            chat_llm_params["openai_api_base"] = openai_base_url

        chat_llm = ChatOpenAI(**chat_llm_params)
    except Exception as e:
        logging.error(f"Failed to initialize ChatOpenAI LLM: {e}")
        return

    defense_tools.configure_tool_llm_instance(chat_llm)


    try:
        agent = build_agent(chat_llm)
    except Exception as e:
        logging.error(f"Failed to build agent: {e}")
        return

    try:
        with open(input_file_abs_path, 'r', encoding='utf-8') as f:
            content_data = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load or parse input file {input_file_abs_path}: {e}")
        return

    processed_querys_data = []
    for item in content_data:
        query_text = item.get('Query', '')
        output_text = item.get('content', {}).get('output', '')
        resource_list = item.get('content', {}).get('resource', [])

        q_str = f"**Query**: {query_text}\n-------\n **Content: **{output_text}\n-------\n **Reference**{str(resource_list)}"
        processed_querys_data.append({
            "original_item": item,
            "constructed_q": q_str
        })

    responses = []
    logging.info(f"Starting processing for {len(processed_querys_data)} items...")
    for i, data_item in enumerate(processed_querys_data):
        q = data_item["constructed_q"]
        original_query_text = data_item["original_item"]["Query"]
        logging.info(f"Processing item {i+1}/{len(processed_querys_data)}: Query - '{original_query_text[:100]}...'")
        
        try:
            response = agent.invoke({
                "input": INSTRUCTION + q
            })
            responses.append({
                "input_query_details": data_item["original_item"],
                "agent_response": response
            })
            logging.info(f"Successfully processed item for Query: '{original_query_text[:50]}...'")
        except Exception as e:
            logging.error(f"Error processing item for Query '{original_query_text[:50]}...': {e}", exc_info=True)
            responses.append({
                "input_query_details": data_item["original_item"],
                "agent_response": {"error": str(e), "details": "Check logs for more information."}
            })

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(responses, f, ensure_ascii=False, indent=4)
        logging.info(f"Processing complete. Output saved to {output_file_path}")
    except Exception as e:
        logging.error(f"Failed to save output file {output_file_path}: {e}")

if __name__ == '__main__':
    main()