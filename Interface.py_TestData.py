import json

from Src.Constants import DBConstants
from Src.DAOLayer.MongoReadWrite import mongoReadWrite
from datetime import datetime
import time
from Src.CoreLogicLayer.TestPlanning.TestdataGeneration.src.GenerateTestDataFromUserStory import generate
# import pandas as pd
import re
import traceback

mongo_obj = mongoReadWrite()


def generate_test_data_from_user_story(processing_json):
    print('Inside generateFormattedTCS')
    start = time.time()
    # print(processing_json['jobID'])

    processing_json['file_content'] = mongo_obj.read_file_from_gridfs(processing_json['filename']).read()

    # execution_details = {'jobID':processing_json['jobID'],'description': 'Not decided yet', 'useCaseName': processing_json['useCaseName'],
    #                      'generationOption': str(processing_json), 'input': 1, 'output': 'N/A',
    #                      'executedOn': datetime.now().strftime("%dth %b, %Y %H:%M:%S"), 'timeTaken': 0,
    #                      'executedBy': processing_json['executedBy'], 'executionStatus': 'Generating'}

    # if processing_json['isMultipleUserStory']:
    #     execution_details['input'] = len(processing_json['multipleUserStory'])
    #
    # execution_details_df = pd.DataFrame(execution_details, index=[0])
    # mongo_obj.write_data(DBConstants.EXECUTION_SUMMARY_COLLECTION, execution_details_df)
    try:
        output = generate(input_param=processing_json)
        # if processing_json['isSingleUserStory']:
        #     data = []
        #     tcs_df = mongo_obj.read_data_with_filter(DBConstants.TESTCASE_COLLECTION, "userStoryID::eq::" + processing_json['userStoryID'] + "<<>>jobID::eq::" + processing_json['jobID'], 0)
        #     scenarios = re.split(r"Test Case \d+: |TestCase \d: ", tcs_df.iloc[0]['generatedTCS'])[1:]
        #     print(scenarios)
        #     for scenario in scenarios:
        #         lines = scenario.strip().split('\n')
        #         if lines:
        #             scenario_outline = lines[0].strip()
        #             feature = "\n".join(lines[1:])
        #             data.append({
        #                 "TestCases": scenario_outline.strip(),
        #                 "feature": "Test Steps: " + scenario_outline.strip() + "\n" + feature.strip()
        #             })
        #
        #     execution_details['executionStatus'] = 'Completed'
        #     execution_details['output'] = len(data)
        #
        #     execution_details['timeTaken'] = time.time() - start
        #     execution_details_df = pd.DataFrame(execution_details, index=[0])
        #
        #     mongo_obj.update_data_based_on_jobid(DBConstants.EXECUTION_SUMMARY_COLLECTION, execution_details_df, execution_details['jobID'])
        #
        #     return {"message": 'Test Case Generation Successful', "status": 200}
        #
        # else:
        #     multi_us = processing_json['multipleUserStory']
        #     data = []
        #     for userstory_id in multi_us:
        #         tcs_df = mongo_obj.read_data_with_filter(DBConstants.TESTCASE_COLLECTION, "userStoryID::eq::" + userstory_id.split('.')[0] + "<<>>jobID::eq::" + processing_json['jobID'],0)
        #
        #         scenarios = re.split(r"Test Case \d+: |TestCase \d: ", tcs_df.iloc[0]['generatedTCS'])[1:]
        #         print(scenarios)
        #         for scenario in scenarios:
        #             lines = scenario.strip().split('\n')
        #             if lines:
        #                 scenario_outline = lines[0].strip()
        #                 feature = "\n".join(lines[1:])
        #                 data.append({
        #                     "TestCases": scenario_outline.strip(),
        #                     "feature": "Test Steps: " + scenario_outline.strip() + "\n" + feature.strip()
        #                 })
        #
        #     execution_details['executionStatus'] = 'Completed'
        #     execution_details['output'] = len(data)
        #
        #     execution_details['timeTaken'] = time.time() - start
        #     execution_details_df = pd.DataFrame(execution_details, index=[0])
        #
        #     mongo_obj.update_data_based_on_jobid(DBConstants.EXECUTION_SUMMARY_COLLECTION, execution_details_df,
        #                                         execution_details['jobID'])
        # response = {"output":output}
        # mongo_obj.write_json_data("FormattedTC_Files", json.dumps(response))
        return output

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        # execution_details['executionStatus'] = 'Failed' execution_details['timeTaken'] = time.time() - start
        # execution_details_df = pd.DataFrame(execution_details, index=[0]) mongo_obj.update_data_based_on_jobid(
        # DBConstants.EXECUTION_SUMMARY_COLLECTION, execution_details_df, execution_details['jobID'])
        return {"message": 'Test Data Generation from User Story Failed', "status": 500}
