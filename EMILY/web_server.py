import os
import sys
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from agent import *
from converter_agent import second_graph
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from datetime import datetime

base_msg = (
    f"Today's date is {datetime.now().strftime('%Y-%m-%d')}. "
    "You are an intelligent assistant that helps with tasks. Pay Attention to the last HumanMessage when generating output."
)

extended_msg = (
    "If the user wants to schedule a task for you to do at a specific time, "
    "respond with your regular output **followed by** an additional line that begins with:\n\n"
    "extended_msg: <crontab schedule>\n\n"
    "The <crontab schedule> should be in standard crontab format:\n"
    "```\n"
    "<minute> <hour> <day_of_month> <month> <day_of_week>\n"
    "```\n"
    "For example, to schedule a task every day at 3:30 PM, return:\n"
    "```\n"
    "extended_msg: 30 15 * * *\n"
    "```\n"
)
arcade_scheduled_tool_execution_message = (
    "If the user wants to schedule a task for you to do at a specific time"
    "respond with your regular output followed by an additional line that begins with:\n"
    "extended_msg: <arcade schedule>"
    "The <arcade schedule> should be in ISO 8601 format:\n"
    "YYYY-MM-DDTHH:MM:SS"
)

sys_msg = base_msg + arcade_scheduled_tool_execution_message
inputs = {
    "messages": [SystemMessage(content=sys_msg)],
}

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests
# Add the current directory to Python path to import agent modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def extract_latest_ai_response(result):
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            return msg
    return None

def parse_content(content: str) -> str:
    """
    Skips all auth prints and only returns AI Output
    Returns a single string
    """
    r = content.split("\n")
    return r[-1]

def parse_scheduled_instr(string: str):
    a = string.split("\n")
    last = a[-1]
    ret = last[14:]
    return ret

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/submit-hint', methods=['POST'])
def submit_hint():
    """Handle form submission and pass hint to agent"""
    try:
        # Get the hint from the form
        hint = request.form.get('hint')
        
        if not hint:
            return jsonify({'error': 'No hint provided'}), 400
        
        # Create inputs for the agent with the user's hint
        inputs["messages"].append(HumanMessage(content=f"{hint}"))

        config = {
            "configurable": {
                "user_id": "default_user"
            }
        }
        
        # Run the agent with the hint
        result = graph.invoke(inputs, config=config)

        converter_agent_response = second_graph.invoke(inputs, config=config)
        # Extract the AI response
        final_message = extract_latest_ai_response(result)
        response_content = None
        if final_message:
            response_content = final_message.content
        else:
            response_content = "No response generated from the agent."


        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                print(msg.tool_calls)



                ### Scheduled tool execs ###
        if "extended_msg" in response_content:
            instructions_for_arcade_schedule = parse_scheduled_instr(response_content)
            API_KEY = arcade_api_key
            user_id = 'default_user'
            TOOL_NAME = None
            run_at = instructions_for_arcade_schedule
            PAYLOAD = {
                None: None
            }

        #print(extract_latest_ai_response(converter_agent_response).content)

        # Return the response
        return jsonify({
            'success': True,
            'hint': hint,
            'response': response_content
        })
        
    except Exception as e:
        if str(e).startswith("Expected dict, got Please"): # handling auth_error
            url_to_print = str(e)[len("Expected dict, got Please authorize the application in your browser:"):]
            return jsonify({
                'success': True, 
                'response': ('Please go to this link to authorize the app: ' + url_to_print)
            })
        #print("\n\n\n" + str(flask_auth_url) + "\n\n\n")
        return jsonify({'success': False, 'error': f'Error processing hint: {str(e)}'}), 500


@app.route('/daily_output.txt', methods=['GET'])
def get_daily_output():
    try:
        with open("/Users/isarashid/Desktop/Arcade_Ambient_Agents/hint-agt/templates/daily_output.txt", "r") as f:
            content = f.read()
        return jsonify({
            'success': True,
            'output': parse_content(content)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/auth-url')
def auth_url():
    url = flask_auth_url or ""
    return jsonify(auth_url=url)

if __name__ == '__main__':
    app.run(debug=True) #, host='0.0.0.0', port=5000