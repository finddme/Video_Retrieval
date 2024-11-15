stt_explain_prompt="""
Using the input question and the retrieved video’s STT output, generate a response that explains the retrieval results in relation to the question. 
First, interpret the intent of the question, identifying any specific details or information being sought. 
Next, review the STT output, noting key elements that may directly address the question or provide relevant context. 
Finally, compose a response that explains how the STT content relates to or answers the question, emphasizing details that align with the focus of the question.
**Speech-to-text result**:
{}

This prompt guides you through a structured approach:

1. Interpret the Question’s Intent: Identifies what information or details are being sought.
2. Review the Caption for Key Elements: Focuses on understanding which parts of the caption are relevant.
3. Compose a Response: Directs the creation of a response that connects the caption to the question, highlighting key, question-relevant details.

## Provide the response in clear and concise **Korean**.
"""

caption_explain_prompt="""
Given the question and the retrieved image caption, analyze the relationship between the question and the caption to generate a response. 
First, interpret the question’s intent, identifying specific details it seeks. 
Then, review the caption’s content, noting key elements that may directly address the question or provide relevant context. 
Finally, compose a response that explains how the caption’s content relates to or answers the question, emphasizing the details that align with the question's focus.

**Caption**:
{}

This prompt guides you through a structured approach:

1. Interpret the Question’s Intent: Identify specific details or information the question is seeking.
2. Review the STT Output for Key Elements: Look for parts of the STT output that are relevant to the question.
3. Compose a Response: Create a response that connects the STT output to the question, clearly explaining how it answers or relates to the question’s focus.

## Provide the response in clear and concise **Korean**.
"""

explain_prompt_merged_v1="""
Using the input question and the provided transcription and(or) frame caption from the video, generate a response that describes the video scene in relation to the question.
First, interpret the intent of the question, identifying any specific details or information being sought. 
Then, review the information of the scene, noting key elements that may directly address the question. 
Finally, compose a response that explains how the information of the scene relates to or answers the question, emphasizing the details that align with the question's focus.

1. Interpret the Question’s Intent: Identify any specific details or information the question seeks about the scene.
2. Review the Transcription or Frame Caption for Key Elements: Examine the transcription or caption to highlight parts that address the question or give relevant context to the scene.
3. Compose a Response: Describe the video scene in a way that directly connects it to the question, emphasizing details that align with the question's focus.

**transcription and(or) frame caption**
{}
## Provide the response in clear and concise **Korean**.
"""

stt_summary_system_prompt="You are generating a transcript summary. Create a summary of the provided transcription. Provide the summary in clear and concise **Korean**. Respond in Markdown."
stt_summary_prompt="""The audio transcription is: 
{}

Provide the summary in clear and concise **Korean**.
"""

caption_summary_system_prompt="You are generating a video summary. Please provide a summary of the video. Provide the summary in clear and concise **Korean**. Respond in Markdown."
caption_summary_prompt="""These are the frame captions from the video.: 
{}

Provide the summary in clear and concise **Korean**.
"""

final_summary_system_prompt="You are generating a video summary. Create a summary of the provided video and its transcript. Provide the summary in clear and concise **Korean**. Respond in Markdown"
final_summary_prompt="""These are the frame caption summary from the video: {}

The audio transcription summary is: {}

Provide the summary in clear and concise **Korean**.
"""


relevant_scoring_prompt = """Evaluate whether there is a semantic relevance between the following text and the user question. 
If relevant, respond with 'yes'; if not, respond with 'no'. 
Include only 'yes' or 'no' in the response, with no additional text.

Text: {}
User Question: {}

"""

