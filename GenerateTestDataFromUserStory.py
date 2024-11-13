# import os.path
# import pandas as pd
# import shutil
#
# from Src.CoreLogicLayer.TestPlanning.ManualTestCaseGeneration.src.GetTestCaseResults import getTC, getTC_no_context
# from Src.DAOLayer import MongoReadWrite
# from Src.Constants import DBConstants
# from Src.DAOLayer.ChromaDBConnector import ChromaDBConnector
from Src.LLMLayer.LLM import LLM


def generate(input_param):
    model = LLM()
    template_tc = """
            I want you to act as a Test Engineer Expert. I am giving you an UserStory which is in the following format.
            User Story: Summary of the user story

            User Story Description: Description of the user story

            User Story Acceptance Criteria:
            AC1: First acceptance Criteria
            AC2: Second acceptance Criteria
            AC3: So on...

            You have to Generate ALL Possible Manual Test cases for the given UserStory and acceptance criteria.
            Ensure that each points and sub points in the Acceptance Criteria is covered.
            Ensure that you cover all the edge and boundary test cases.
            Ensure to generate detailed test step for each test case.
            Ensure to generate Both Valid and Invalid test case.

            input: {input}
            Manual Test Case:
            """

    template_td = """
            I want you to act as a Test Engineer Expert. I am giving you a few Test Case Scenarios.
            I want you to generate valid, invalid Test Data (including all edge and boundary data conditions) for each of the test case scenario in Tabular Format.
            Note that assertions will not considered as a Test Data, so don't generate test data for it. 
            Generate 5 sets of test data.
            Below is the format of test data: -
            |Variable Name |Test Data          |Valid/Invalid |
            |Email         |john.doe@gmail.com |Valid         |
            |Email         |john.doegmail.com  |Invalid       |
            |Email         |j@gmail.com        |Invalid       |
            User Story: Summary of the user story
            Now, I want you to generate Meaningful Test Data for the following test scenario in Tabular Format only.
            Make sure to retain the original test case scenario.
            {input_tc}
            """

    output_tc = model.send_request(input_param, template_tc, ["input"],
                                   {"input": input_param['file_content']})

    output_td = model.send_request(input_param, template_td, ["input_tc"],
                                   {"input_tc": output_tc})

    return output_td
