from flask import Flask, render_template_string, session, jsonify, request

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Questions that need to be answered by the user
questions = [
    "Do you want to use the context? (Yes/No)",
    "Do you want to enable additional intelligence? (Yes/No)",
    "Do you want to generate additional Acceptance Criteria? (Yes/No)"
]


@app.route('/')
def index():
    # Reset session at the start
    session['current_index'] = 0
    session['responses'] = []
    session['log'] = []
    return render_template_string("""  
        <html>  
        <head>  
            <title>Interactive Test Case Generator</title>  
            <style>  
                #log {  
                    height: 300px;  
                    border: 1px solid black;  
                    padding: 5px;  
                    overflow-y: scroll;  
                    background-color: black;  
                    color: lime;  
                    font-family: monospace;  
                }  
                button {  
                    margin: 5px;  
                }  
            </style>  
        </head>  
        <body>  
            <h1>Manual Test Generator</h1>  
            <div id="log"></div>  
            <button onclick="startProcess()">Start Processing</button>  
            <script>  
                function startProcess() {  
                    fetch('/next_question')  
                    .then(response => response.json())  
                    .then(data => {  
                        if (!data.done) {  
                            updateLog(data.question);  
                        } else {  
                            updateLog("Processing complete.");  
                            setTimeout(function() { window.location.href = '/results'; }, 2000);  
                        }  
                    });  
                }  

                function sendAnswer(answer) {  
                    fetch('/answer', {  
                        method: 'POST',  
                        headers: {'Content-Type': 'application/json'},  
                        body: JSON.stringify({'answer': answer})  
                    })  
                    .then(response => response.json())  
                    .then(data => {  
                        if (!data.done) {  
                            updateLog(data.question);  
                        } else {  
                            updateLog("Processing complete.");  
                            setTimeout(function() { window.location.href = '/results'; }, 2000);  
                        }  
                    });  
                }  

                function updateLog(message) {  
                    if (message) {  
                        var logDiv = document.getElementById('log');  
                        logDiv.innerHTML += '<p>' + message + '</p>' +  
                                            '<button onclick="sendAnswer(\'yes\')">Yes</button>' +  
                                            '<button onclick="sendAnswer(\'no\')">No</button>';  
                        logDiv.scrollTop = logDiv.scrollHeight; // Auto-scroll to the bottom  
                    }  
                }  
            </script>  
        </body>  
        </html>  
    """)


@app.route('/next_question')
def next_question():
    index = session.get('current_index', 0)
    if index < len(questions):
        return jsonify({'question': questions[index]})
    else:
        return jsonify({'done': True})


@app.route('/answer', methods=['POST'])
def answer():
    data = request.get_json()
    answer = data['answer']
    responses = session.get('responses', [])
    responses.append(answer)
    session['responses'] = responses

    log = session.get('log', [])
    log.append(f"Q: {questions[session['current_index']]} A: {answer}")
    session['log'] = log

    current_index = session.get('current_index', 0)
    session['current_index'] = current_index + 1

    return next_question()


@app.route('/results')
def results():
    responses = session.get('responses', [])
    log = session.get('log', [])
    return render_template_string("""  
        <html>  
        <head>  
            <title>Results</title>  
        </head>  
        <body>  
            <h1>Results of Your Responses</h1>  
            <div>  
                <h2>Log of Questions and Answers:</h2>  
                <ul>  
                    {% for entry in log %}  
                    <li>{{ entry }}</li>  
                    {% endfor %}  
                </ul>  
            </div>  
            <div>  
                <h2>Summary of Your Answers:</h2>  
                <ul>  
                    {% for question, answer in zip(questions, responses) %}  
                    <li>{{ question }} - <strong>{{ answer }}</strong></li>  
                    {% endfor %}  
                </ul>  
            </div>  
            <a href="/">Start Over</a>  
        </body>  
        </html>  
   """, questions=questions, responses=responses, log=log)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
