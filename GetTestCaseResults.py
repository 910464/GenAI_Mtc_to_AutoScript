import datetime
import os

from Src.Constants import DBConstants
from Src.DAOLayer.MongoReadWrite import mongoReadWrite
from Src.EncryptionLayer.Decryption import FileDecryptor
from Src.LLMLayer.LLM import LLM

def getTC(query, context, input_param):

    isPositive = input_param['isPositive']
    isNegative = input_param['isNegative']
    isTestData = input_param['isTestData']
    isAdditionalAC = input_param['isAdditionalAC']
    isLLM = input_param['isLLM']
    ac_generated = ''

    mongo_obj = mongoReadWrite()
    file_decryptor = FileDecryptor()
    model = LLM()
    instruction = """-> Test Case MUST be in the below format. STRICTLY FOLLOW THIS FORMAT ONLY. (Based on the test case scenario, give Positive Test Case:/Negative Test Case header)
                        Positive Test Case:/Negative Test Case:
                             Test Case ID: ID
                             Test Case Description: Test case description
                             Test Steps: 
                             Step 1:- ...
                             Step 2:- ...
                             Step 3:- ...
                             Expected Result:-
                             1:- Expected result for step 1
                             2:- Expected result for step 2
                             3:- Expected result for step 3


            """
    private_key = mongo_obj.read_filecontent_from_gridfs(DBConstants.KEY_FILES_COLLECTION, "private_key.pem")
    encryption_key = mongo_obj.read_filecontent_from_gridfs(DBConstants.KEY_FILES_COLLECTION,
                                                            "encryption_key.bin")

    AC_PROMPT = """
            Act as an Test Engineer Expert. I am giving you some UserStory. UserStory contains UserStoryDescription. It might also contain acceptance Criteria.

            Based on the understanding of above User story Generate a new Acceptance Criteria.
            input: {UserStory}
            Acceptance Criteria:
            """

    if isLLM == False:
        instruction += '-> Don\'t use your own intelligence while generating the output. STRICTLY stick to the format\n'

    if isAdditionalAC:
        ac_generated = model.send_request(input_param, AC_PROMPT,["UserStory"], {"UserStory": query})
        query += '\n'
        query += ac_generated

    if isTestData:
        instruction += """-> To Generate Test Data for each Test Case and add it at the end of each Test Case."""
    else:
        instruction += '-> Don\'t generate any Test Data for any Test Case.\n'

    if not (isPositive is False and isNegative is False):
        if isPositive:
            instruction += '-> To Generate all possible positive Test Case for the given UserStory\n'
        else:
            instruction += '-> Don\'t generate positive Test Case for the given UserStory\n'

        if isNegative:
            instruction += '-> To Generate all possible negative Test Case for the given UserStory\n'
        else:
            instruction += '-> Don\'t generate negative Test Case for the given UserStory\n'

    TC_PROMPT = """
            I want you to act as an Test Engineer Expert. I am giving you some UserStory - Test Cases scenario pairs.
            UserStory contains User Story Description and acceptance Criteria. Test Cases is according to the UserStory.
            Let's understand each pair one by one.
            UserStory-Test Cases pairs: 
            {context}

            Based on the understanding of above User story and Test Cases.
            Generate ONLY one Test Case covering end to end the whole UserStory.
            Also Ensure to follow the below instructions strictly:
            Test Case MUST be in the below format. STRICTLY FOLLOW THIS FORMAT ONLY. (Based on the test case scenario, give Positive Test Case:/Negative Test Case header)
                 Test Case ID: ID
                 Test Case Description: Test case description
                 Test Steps: 
                 Step 1:- ...
                 Step 2:- ...
                 Step 3:- ...
            input: {UserStory}
            Test Cases:
            """

    output = model.send_request(input_param, TC_PROMPT, ["context", "UserStory"], {"context": context, "UserStory": query})

    output_dir = r"../CoreLogicLayer/TestPlanning/SharedResources/result_logs"
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory: {e}")

    # Combine the prefix, timestamp, and file extension to create the filename
    currtime = datetime.datetime.now()
    currtime = currtime.strftime("%Y-%m-%d-%H-%M-%S-%f")[:-3]
    output_path = f"{output_dir}/tcs_{currtime}.txt"

    with open(output_path, "a", encoding="utf-8") as file:
        file.write(output + "\n\n\n\n")
    print("Test Case generated")
    return [output, ac_generated]


def getTC_no_context(query, input_param):

    isPositive = input_param['isPositive']
    isNegative = input_param['isNegative']
    isTestData = input_param['isTestData']
    isAdditionalAC = input_param['isAdditionalAC']
    isLLM = input_param['isLLM']
    ac_generated = ''

    mongo_obj = mongoReadWrite()
    file_decryptor = FileDecryptor()
    model = LLM()
    instruction = """-> Test Case MUST be in the below format. STRICTLY FOLLOW THIS FORMAT ONLY. (Based on the test case scenario, give Positive Test Case:/Negative Test Case header)
                    Positive Test Case:/Negative Test Case:
                         Test Case ID: ID
                         Test Case Description: Test case description
                         Test Steps: 
                         Step 1:- ...
                         Step 2:- ...
                         Step 3:- ...
                         Expected Result:-
                         1:- Expected result for step 1
                         2:- Expected result for step 2
                         3:- Expected result for step 3


        """
    private_key = mongo_obj.read_filecontent_from_gridfs(DBConstants.KEY_FILES_COLLECTION, "private_key.pem")
    encryption_key = mongo_obj.read_filecontent_from_gridfs(DBConstants.KEY_FILES_COLLECTION,
                                                            "encryption_key.bin")

    AC_PROMPT = """
            Act as an Test Engineer Expert. I am giving you some UserStory. UserStory contains UserStoryDescription. It might also contain acceptance Criteria.

            Based on the understanding of above User story Generate a new Acceptance Criteria.
            input: {UserStory}
            Acceptance Criteria:
            """

    if isLLM == False:
        instruction += '-> Don\'t use your own intelligence while generating the output. STRICTLY stick to the format\n'

    if isAdditionalAC:
        ac_generated = model.send_request(input_param, AC_PROMPT,["UserStory"], {"UserStory": query})
        query += '\n'
        query += ac_generated

    if isTestData:
        instruction += """-> To Generate Test Data for each Test Case and add it at the end of each Test Case."""
    else:
        instruction += '-> Don\'t generate any Test Data for any Test Case.\n'

    if not (isPositive is False and isNegative is False):
        if isPositive:
            instruction += '-> To Generate all possible positive Test Case for the given UserStory\n'
        else:
            instruction += '-> Don\'t generate positive Test Case for the given UserStory\n'

        if isNegative:
            instruction += '-> To Generate all possible negative Test Case for the given UserStory\n'
        else:
            instruction += '-> Don\'t generate negative Test Case for the given UserStory\n'

    TC_PROMPT = """
            I want you to act as an Test Engineer Expert. I want you to generate ONLY one manual testcase for the User Story Description and the acceptance criteria I give you.
            Ensure that all the points and the subpoints in the acceptance cirteria is STRICTLY met. STRICTLY Stick to the acceptance criteria.
            Also Ensure to follow the below instructions strictly:
            Test Case MUST be in the below format. STRICTLY FOLLOW THIS FORMAT ONLY. (Based on the test case scenario, give Positive Test Case:/Negative Test Case header)
                 Test Case ID: ID
                 Test Case Description: Test case description
                 Test Steps: 
                 Step 1:- ...
                 Step 2:- ...
                 Step 3:- ...
            input: {UserStory}
            Test Cases:
            """

    output = model.send_request(input_param, TC_PROMPT, ["UserStory"], {"UserStory": query})

    output_dir = r"../CoreLogicLayer/TestPlanning/SharedResources/result_logs"
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory: {e}")

    # Combine the prefix, timestamp, and file extension to create the filename
    currtime = datetime.datetime.now()
    currtime = currtime.strftime("%Y-%m-%d-%H-%M-%S-%f")[:-3]
    output_path = f"{output_dir}/tcs_{currtime}.txt"

    with open(output_path, "a", encoding="utf-8") as file:
        file.write(output + "\n\n\n\n")
    print("Test Case generated")
    return [output, ac_generated]
