import ollama
import re 
import time
import json

response_array = []
success_count = 0
failure_count = 0

# extract the tool call from the response
def extract_tool_call(text):
    import io
    from contextlib import redirect_stdout

    pattern = r"```tool_code\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        code = match.group(1).strip()
        if function_name is None:
            return False # No function name expected, but code was found
        if function_name in code:
            return True
        else:
            return False
    else:
        return None

system_instructions = """
    Your name is ADA (Advanced Design Assistant) you are a helpful AI assistant.  You are an expert in All STEM Fields providing concise and accurate information. When asked to perform a task, respond with the code to perform that task wrapped in ```tool_code```.  If the task does not require a function call, provide a direct answer without using ```tool_code```.  Always respond in a helpful and informative manner."

    You speak with a british accent and address people as Sir.
"""

instruction_prompt_with_function_calling = '''At each turn, if you decide to invoke any of the function(s), it should be wrapped with ```tool_code```. If you decide to call a function the response should only have the function wrapped in tool code nothing more. The python methods described below are imported and available, you can only use defined methods also only call methods when you are sure they need to be called. The generated code should be readable and efficient. The response to a method will be wrapped in ```tool_output``` use it generate a helpful, friendly response. For example if the tool output says ```tool_output camera on```. You should say something like "The Camera is on".

For regular prompts do not call any functions or wrap the response in ```tool_code```.

The following Python methods are available:

```python
def camera.open() -> None:
    """Open the camera"""

def system.info() -> None:
    """ Gathers and prints system information including CPU, RAM, and GPU details. """

def timer.set(time_str):
    """
    Counts down from a specified time in HH:MM:SS format.

    Args:
        time_str (str): The time to count down from in HH:MM:SS format.
    """
def project.create_folder(folder_name):
    """
    Creates a project folder and a text file to store chat history.

    Args:
        folder_name (str): The name of the project folder to create.
    """

```

User: {user_message}
'''

def test(prompt, should_call_function, function_name):
    global success_count
    global failure_count
    messages = [{"role": "system", "content": system_instructions}, {"role": "user", "content": instruction_prompt_with_function_calling.format(user_message=prompt)}]
    response = ollama.chat(model="llama3.2", messages=messages)
    #print(response['message']['content'])
    returned_value = extract_tool_call(response['message']['content'], function_name)

    if should_call_function == False:
        if returned_value == None:
            result = "Passed"
        else:
            result = "Failed"
    else:
        if returned_value == True:
            result = "Passed"
        else:
            result = "Failed"
    print(result)
    if result == "Passed":
        success_count += 1
    else:
        failure_count += 1
    
    data = (prompt, result, response['message']['content'])
    response_array.append(data)   

prompts_and_expectations = [
    ("Hello, how are you?", False, None),  # Should NOT call a function
    ("set 10 second timer", True, "timer.set"),  # Should call timer.set()
    ("Difference between DC and AC", False, None),  # Should NOT call a function
    ("Show me System Info", True, "system.info"),  # Should call system.info()
    ("Briefly explain gravity", False, None),  # Should NOT call a function
    ("can you open the camera", True, "camera.open"),  # Should call camera.open()
    ("Give me a short explanation of the internet", False, None),  # Should NOT call a function
    ("set me a timer for 1 minute", True, "timer.set"),  # Should call timer.set()
    ("What is the chemical symbol for water?", False, None),  # Should NOT call a function
    ("open the camera", True, "camera.open"),  # Should call camera.open()
    ("What is a synonym for happy?", False, None),  # Should NOT call a function
    ("set me 33 second timer", True, "timer.set"),  # Should call timer.set()
    ("What is the largest planet in our solar system?", False, None),  # Should NOT call a function
    ("open camera", True, "camera.open"),  # Should call camera.open()
    ("How many continents are there?", False, None),  # Should NOT call a function
    ("Start a 10 hour timer", True, "timer.set"),  # Should call timer.set()
    ("What is the opposite of up?", False, None),  # Should NOT call a function
    ("Turn on the Camera", True, "camera.open"),  # Should call camera.open()
    ("What is the speed of light in a vacuum?", False, None),  # Should NOT call a function
    ("Timer for 10 minutes and 10 seconds", True, "timer.set"),  # Should call timer.set()
    ("Who painted the Mona Lisa?", False, None),  # Should NOT call a function
    ("Start the Camera", True, "camera.open"),  # Should call camera.open()
    ("Thank you very much.", False, None),  # Should NOT call a function
    ("Create new web shooter project", True, "project.create_folder"),  # Should call project.create_folder()
    ("Please and thank you.", False, None),  # Should NOT call a function
    ("Give me system info", True, "system.info"),  # Should call system.info()
    ("No, thank you.", False, None),  # Should NOT call a function
    ("Create new project called Iron Man", True, "project.create_folder"),  # Should call project.create_folder()
    ("Where do Lions live", False, None),  # Should NOT call a function
    ("Show me GPU information", True, "system.info"),  # Should call system.info()
    ("What ocean is larger the atlantic or pacific", False, None), #Should NOT call a function
    ("Make a new project folder name robot arm", True, "project.create_folder"), #Should call project.create_folder()
    ("What is the largest country in the world", False, None), #Should NOT call a function
    ("How much RAM am I using", True, "system.info"), #Should call system.info()
    ("Briefly explain AI", False, None), #Should NOT call a function
    ("Start a new project called robot car", True, "project.create_folder"), #Should call project.create_folder()
    ("Give me CPU Info", True, "system.info"), #Should call system.info()
    ("What is a brushless motor?", False, None), #Should NOT call a function
    ("Make me a new project folder called AI assistant", True, "project.create_folder"), #Should call project.create_folder()
    ("Goodnight!", False, None), #Should NOT call a function
]
start_time = time.time()

for prompt, should_call_function, function_name in prompts_and_expectations:
    test(prompt, should_call_function, function_name)

end_time = time.time()
execution_time = end_time - start_time

print(f"Execution time: {execution_time} seconds")
print(f"Success rate: {success_count / (success_count + failure_count) * 100}%")

log_filename = "response_log.json"
with open(log_filename, "w") as f:
    json.dump(
        [{"prompt": item[0], "result": item[1], "model_response": item[2]} for item in response_array], f, indent=4
    )

print(f"\nLog file '{log_filename}' created successfully.")