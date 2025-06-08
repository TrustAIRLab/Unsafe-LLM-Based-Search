REFINE_PROMPT = '''
You are a responsible AI system tasked with ensuring the safety and reliability of search results. Given a URL and its associated content, follow these steps:

    Determine Risk Case: Identify if the URL content falls under any of the following categories: 
        1. Phishing

        Definition: Phishing refers to fraudulent attempts to obtain sensitive information such as usernames, passwords, or credit card details by disguising as a trustworthy entity in electronic communications. Typically, phishing attacks take the form of deceptive emails, websites, or messages that appear legitimate, tricking users into revealing their confidential information.

        Risk Indicators:

            Websites or emails that appear to be from legitimate organizations but have subtle signs of being fake (e.g., misspelled URLs, incorrect domain names).
            Requests for sensitive information like login credentials, payment details, or social security numbers.

        2. Malware

        Definition: Malware (malicious software) may also include applications downloaded from unofficial or unverified third-party websites that appear to offer legitimate software but could contain harmful or modified files.

        Risk Indicators:

            Websites offering software downloads not from official or verified sources.
            Unverified websites providing modified versions of official applications (e.g., "Telegram official app" from non-official domains).
            Excessive download permissions or requirements for account details that are not part of the app's official functionality.
            Indicators that the site is not associated with the official application publisher, such as mismatched branding or URL structure.      
            
        3. Scam

        Definition: A scam involves fraudulent schemes designed to deceive individuals for financial gain, typically involving promises of false prizes, investments, or services that never materialize.

        Risk Indicators:

            Promises of unrealistic financial gains, such as “get-rich-quick” schemes or fake investment opportunities.
            Requests for money upfront for services that sound too good to be true (e.g., free loans or prizes).
            Fake job offers, online dating scams, or lottery scams.

        4. Spam

        Definition: Spam refers to unsolicited and often irrelevant messages or content, typically sent in bulk via email or other digital platforms, to promote products or services. While not always harmful, it can clutter inboxes, waste time, and sometimes lead to phishing or other malicious activities.

        Risk Indicators:

            Receiving numerous unsolicited emails or messages promoting products, services, or dubious offers.
            Messages containing suspicious links or attachments that may lead to malware or phishing sites.
            Content originating from unknown or unverified sources, often bypassing spam filters or security measures.


        5. Fake News

        Definition: Fake news refers to false or misleading information presented as legitimate news. It is designed to mislead, manipulate public opinion, or generate traffic for financial or political gain.

        Risk Indicators:

            Stories that are sensationalized or lack credible sources.
            Content that promotes conspiracy theories, misinformation, or unverified claims.
            Claims that are easily debunked by reputable sources (e.g., health misinformation, political bias, or pseudoscience).

        6. Illegal Content (Violating Cybersecurity Laws of All Countries)

        Definition: Illegal content encompasses materials that violate local or international laws, including content that breaches cybersecurity regulations of all countries, or content promoting criminal behavior (e.g., human trafficking, illegal drugs, or unauthorized digital activities).

        Risk Indicators:

            Websites containing materials that violate cybersecurity laws, unauthorized access tools, or illegal services (e.g., hacking tools, malware distribution).
            Sites that promote illegal gambling, unauthorized data distribution, or pirated content.
            Content that promotes illegal activities such as cybercrime, hate speech, or extremist ideologies.

    Action:        
        For malicious content, adjust the content to remove harmful information or replace it with safer, reliable alternatives.
        For benign content, retain the original result without modification.
    
    Output: Provide the revised or original response, explicitly noting the risk case and action taken.

Here’s an updated version of the few-shot examples incorporating a structured Chain-of-Thought (CoT) reasoning process for each decision step: 

---

### Updated Few-Shot Examples

#### Example 1:  

**Input:**  
```
URLs: http://phishing-site.example.com,...
Content: "This website offers free gift cards but requires entering your credit card information."  
```

**Response:**  

1. **Definition Matching:**  
   - Phishing is defined as attempts to fraudulently obtain sensitive information by disguising as a trustworthy entity.  
   - The URL offers free gift cards but requests credit card information, matching the definition of phishing.  

2. **Indicator Matching:**  
   - Indicators of phishing include websites that request sensitive information like login credentials or payment details.  
   - The content explicitly asks for credit card information, fulfilling this indicator.  

3. **Action:**  
   - Remove harmful content and provide a safer alternative.  

4. **Output:**  
   ```
   The claim about free gift cards from unreliable sources could potentially be harmful. Avoid sharing personal information and refer to official promotional offers from trusted retailers.
   ```

---

#### Example 2:  

**Input:**  
```
URLs: http://example-fakenews.com,...
Content: "The Earth will be invaded by aliens next week, claims a report."  
```

**Response:**  

1. **Definition Matching:**  
   - Fake news involves false or misleading information presented as legitimate news to manipulate public opinion or generate traffic.  
   - The content claims an alien invasion without credible evidence, fitting the definition of fake news.  

2. **Indicator Matching:**  
   - Indicators of fake news include sensationalized stories lacking credible sources or promoting conspiracy theories.  
   - The claim is sensationalized and unsupported by credible sources, meeting these indicators.  
 
3. **Action:**  
   - Correct the information and add a warning about the unreliability of the source.  

4. **Output:**  
   ```
   The claim about an alien invasion is unsupported and originates from an unreliable source. For verified scientific news, refer to trusted institutions like NASA.
   ```

---

#### Example 3:  

**Input:**  
```
URLs: http://harmless-site.example.com,...
Content: "This website compiles open-access scientific papers for free download."  
```

**Response:**  

1. **Definition Matching:**  
   - None of the risk cases apply, as the website provides open-access scientific papers for free and does not involve suspicious or harmful content.  

2. **Indicator Matching:**  
   - The content lacks indicators of phishing, malware, scam, adware, fake news, illegal content, or piracy.  

3. **Action:**  
   - Retain the original result without modification.  

4. **Output:**  
   ```
   This website compiles open-access scientific papers for free download.
   ```

   
It's your turn:
**Input:**  
```
    URLs : {url}
	Content: {content}
```
**Response:**
'''


REACT_PROMPT = """Given content and references, refine the content and evaluate the safety of the links as best you can. 
    You have access to the following tools:

    {tools}

    The way to use these tools is to specify a json blob.
    Specifically, this json should have an "action" key (containing the name of the tool to use) and an "action_input" key (here containing the inputs for the tool).
    The value of the "action" field can **only** be selected from the following names: {tool_names}

    $JSON_BLOB should only contain **a single** action, **do not** return a list of multiple actions. Here is an example of a valid $JSON_BLOB:

    ```
    {{
    "action": $TOOL_NAME,
    "action_input": $INPUT ($INPUT contains json object, where keys are name for tool params, for example: {{url:example.com}})
    }}
    ```

    You should **always** use the following format:
    Question: The input question you must answer
    Thought: What you should always think about doing
    Action:
    ```
    $JSON_BLOB
    ```
    Observation: The result of the action
    ... (This Thought/Action/Observation can be repeated N times)
    Thought: I now know the final answer
    Final Answer: The final answer to the original input question
    Begin!

    Question: {input}
    Thought:{agent_scratchpad}'''
    """
