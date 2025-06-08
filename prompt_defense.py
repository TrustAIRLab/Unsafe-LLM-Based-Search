import json
import os
import sys
import time # Potentially for adding delays between API calls if needed
from openai import OpenAI

client = OpenAI(
    base_url="",
    api_key="",
)

try:
    from src.prompt import REFINE_PROMPT
except ImportError:
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, base_path)
    try:
        from defense.src.prompt import REFINE_PROMPT
    except ImportError as e:
        print(f"sys.path: {sys.path}")
        print(f"ImportError: {e}")
        sys.exit(1)


def get_llm_response(prompt_text):
    try:
        chat_completion = client.chat.completions.create(
            model="openai/gpt-4.1",
            messages=[
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
        )
        response_content = chat_completion.choices[0].message.content
        return response_content.strip() if response_content else ""
    except Exception as e:
        print(f"调用 OpenAI API 时出错: {e}")
        return f"API_ERROR: {str(e)}"


def process_json_file(input_json_path, output_json_path, prompt_template):
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The input file was not found at the specified path {input_json_path}")
        return
    except json.JSONDecodeError:
        print(f"Unable to decode JSON from {input_json_path}")
        return

    processed_data = []
    total_items = len(data)
    for index, item in enumerate(data):
        print(f"Processing {index + 1}/{total_items} (LLM: {item.get('LLM', 'N/A')}, Query: {item.get('Query', 'N/A')[:50]}...).")
        new_item = item.copy()
        
        if 'content' in new_item and isinstance(new_item['content'], dict):
            content_text = new_item['content'].get('output', '')
            resource_urls_list = new_item['content'].get('resource', [])

            all_urls_str = json.dumps(resource_urls_list) 
            
            current_content = str(content_text) if content_text is not None else ""

            filled_prompt = prompt_template.replace("{url}", all_urls_str)
            filled_prompt = filled_prompt.replace("{content}", current_content)

            llm_response = get_llm_response(filled_prompt)
            
            new_item['prompt_defense_output'] = llm_response

            # time.sleep(1) 
        else:
            new_item['prompt_defense_output'] = "SKIPPED: No valid 'content' dictionary found."
            
        processed_data.append(new_item)
        print(f"All {index + 1}/{total_items} done.")

    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=4)
        print(f"Successful, Output: {output_json_path}")
    except IOError:
        print(f"Unable to write to the output file {output_json_path}.")

if __name__ == '__main__':
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_script_dir, 'template.json')
    output_file = os.path.join(current_script_dir, 'template_output_prompt.json')

    if 'REFINE_PROMPT' not in globals():
        print("Error: Can not find REFINE_PROMPT ")
        sys.exit(1)
    
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Using openai/gpt-4.1")
    print(f"Temperature: 0.7")
    print("Start...")

    process_json_file(input_file, output_file, REFINE_PROMPT)
    
    print("All done")
