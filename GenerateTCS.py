import os.path
import pandas as pd
import shutil
import re

from Src.Constants.DBConstants import ADDITIONAL_CONTEXT_TC
from Src.CoreLogicLayer.TestPlanning.ManualTestCaseGeneration.src.GetTestCaseResults import getTC, getTC_no_context
from Src.DAOLayer import MongoReadWrite
from Src.Constants import DBConstants
from Src.DAOLayer.ChromaDBConnector import ChromaDBConnector


def generate(input_param, no_of_ret_doc=3):
    mongo_obj = MongoReadWrite.mongoReadWrite()
    jobId = input_param['jobID']

    isMultipleUserStory = input_param['isMultipleUserStory']
    userStoryDescription = input_param['userStoryDescription']
    userStoryAC = input_param['userStoryAcceptanceCriteria']
    multipleUserStory = input_param['multipleUserStory']
    userStoryID = input_param['userStoryID']
    projectID = input_param['projectID']
    print(userStoryID)

    if isMultipleUserStory is False:
        if userStoryDescription == "" or userStoryDescription is None:
            raise Exception("Cannot Generate BDD Due to Empty User Story Description")


        if userStoryDescription.isnumeric():
            raise Exception("Cannot Generate BDD Due to error in User Story Description")


        if userStoryID == "" or userStoryID is None:
            raise Exception("Cannot Generate BDD Due to missing user story id")

        if userStoryID.isnumeric():
            raise Exception("Cannot Generate BDD Due to error in the user story id")

    chromadb = ChromaDBConnector(r"../CoreLogicLayer/TestPlanning/SharedResources/data/embed_data_tc")

    try:
        dataframes = mongo_obj.read_additional_context(projectID,ADDITIONAL_CONTEXT_TC)
        print(dataframes)

        combined_df = pd.concat(dataframes, ignore_index=True)
        if isMultipleUserStory:
            combined_df.to_csv(r'../CoreLogicLayer/TestPlanning/SharedResources/data/input/mapping.csv', index=False)
            print('mapping data cleaned')

            # if os.path.exists(r"../CoreLogicLayer/TestPlanning/SharedResources/data/embed_data_tc"):
            #     shutil.rmtree(r"../CoreLogicLayer/TestPlanning/SharedResources/data/embed_data_tc")
            #
            # if not os.path.exists(r"../CoreLogicLayer/TestPlanning/SharedResources/data/embed_data_tc"):
            #     chromadb.vector_store(r'../CoreLogicLayer/TestPlanning/SharedResources/data/input/mapping.csv')

            results = []
            for i in multipleUserStory:
                file_data = mongo_obj.read_file_from_gridfs(i)
                if file_data is not None:
                    descriptions = file_data.read().decode()
                else:
                    print(f"Error reading file: {i}")
                    return

                index = 1

                context = chromadb.retrieval_context(query=descriptions, k=no_of_ret_doc)
                output = getTC(query=descriptions, context=context, input_param=input_param)
                results.append(output)

                lines = descriptions.strip().split('\n')
                user_story_id = ""
                user_story_description = ""
                acceptance_criteria = ""
                for line in lines:
                    if "User Story ID" in line or 'UserStoryID' in line:
                        user_story_id = line.split(':')[1].strip()
                    elif "User Story Description" in line or 'UserStoryDescription' in line:
                        user_story_description = line.split(':')[1].strip()
                    elif "Acceptance Criteria" in line or 'AcceptanceCriteria' in line:
                        continue
                    else:
                        acceptance_criteria += line+'\n'
                j = [user_story_id, user_story_description, acceptance_criteria]


                result_df = pd.DataFrame(
                    {'jobID': jobId, 'userStoryID': j[0], 'inputUserstory': j[1],
                     'inputAcceptanceCriteria': j[2], 'generatedTCS': output[0],
                     'generatedAcceptanceCriteria': output[1]}, index=[0])
                mongo_obj.write_data(DBConstants.TESTCASE_COLLECTION, result_df)
                index += 1

                if not os.path.exists(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output'):
                    os.makedirs(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output')

                with open(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output/' + i.split('.')[0] + '_testcase.txt', 'w') as f:
                    f.write(output[0])

                print('Done')

        else:
            combined_df.to_csv(r'../CoreLogicLayer/TestPlanning/SharedResources/data/input/mapping.csv', index=False)
            print('mapping data cleaned')

            if os.path.exists(r"../CoreLogicLayer/TestPlanning/SharedResources/data/embed_data_tc"):
                shutil.rmtree(r"../CoreLogicLayer/TestPlanning/SharedResources/data/embed_data_tc")

            if not os.path.exists(r"../CoreLogicLayer/TestPlanning/SharedResources/data/embed_data_tc"):
                chromadb.vector_store(r'../CoreLogicLayer/TestPlanning/SharedResources/data/input/mapping.csv')


            context = chromadb.retrieval_context(query=userStoryDescription, k=no_of_ret_doc)

            output = getTC(query=userStoryDescription, context=context, input_param=input_param)
            result_df = pd.DataFrame({'jobID':jobId, 'userStoryID':userStoryID,'inputUserstory': userStoryDescription, 'generatedTCS': output[0],
                                      'inputAcceptanceCriteria':userStoryAC,'generatedAcceptanceCriteria': output[1]}, index=[0])
            mongo_obj.write_data(DBConstants.TESTCASE_COLLECTION, result_df)

            if not os.path.exists(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output'):
                os.makedirs(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output')

            with open(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output/'+userStoryID+'_testcase.txt','w') as f:
                f.write(output[0])

            print('Done')

    except:
        if isMultipleUserStory:

            results = []
            for i in multipleUserStory:
                file_data = mongo_obj.read_file_from_gridfs(i)
                if file_data is not None:
                    descriptions = file_data.read().decode()
                    for desc in descriptions.split('\n'):
                        if 'ID:' in desc or 'ID :' in desc:
                            if len(desc.split(':')[1].strip())<=1:
                                raise Exception("Sorry, User Story ID is not valid")
                        elif 'Description:' in desc or 'Description :' in desc:
                            if len(desc.split(':')[1].strip()) <= 1:
                                raise Exception("Sorry, User Story Description is not valid")

                            if desc.split(':')[1].strip().isnumeric():
                                raise Exception("Sorry, User Story description is not valid")

                            if not re.search(r"[a-zA-Z0-9]", desc.split(':')[1].strip()):
                                raise Exception("Sorry, User Story description is not valid")

                else:
                    raise Exception(f"Error reading file: {i}")
                    return

                index = 1


                output = getTC_no_context(query=descriptions, input_param=input_param)
                results.append(output)

                lines = descriptions.strip().split('\n')
                user_story_id = ""
                user_story_description = ""
                acceptance_criteria = ""
                for line in lines:
                    if "User Story ID" in line or 'UserStoryID' in line:
                        user_story_id = line.split(':')[1].strip()
                    elif "User Story Description" in line or 'UserStoryDescription' in line:
                        user_story_description = line.split(':')[1].strip()
                    elif "Acceptance Criteria" in line or 'AcceptanceCriteria' in line:
                        continue
                    else:
                        acceptance_criteria += line + '\n'
                j = [user_story_id, user_story_description, acceptance_criteria]

                result_df = pd.DataFrame(
                    {'jobID': jobId, 'userStoryID': j[0], 'inputUserstory': j[1],
                     'inputAcceptanceCriteria': j[2], 'generatedTCS': output[0],
                     'generatedAcceptanceCriteria': output[1]}, index=[0])
                mongo_obj.write_data(DBConstants.TESTCASE_COLLECTION, result_df)
                index += 1

                if not os.path.exists(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output'):
                    os.makedirs(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output')

                with open(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output/' + i.split('.')[0] + '_testcase.txt',
                          'w') as f:
                    f.write(output[0])

                print('Done')

        else:
            output = getTC_no_context(query=userStoryDescription, input_param=input_param)
            result_df = pd.DataFrame({'jobID': jobId, 'userStoryID': userStoryID, 'inputUserstory': userStoryDescription,
                                      'generatedTCS': output[0],
                                      'inputAcceptanceCriteria': userStoryAC, 'generatedAcceptanceCriteria': output[1]},
                                     index=[0])
            mongo_obj.write_data(DBConstants.TESTCASE_COLLECTION, result_df)

            if not os.path.exists(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output'):
                os.makedirs(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output')

            with open(r'../CoreLogicLayer/TestPlanning/SharedResources/data/output/' + userStoryID + '_testcase.txt',
                      'w') as f:
                f.write(output[0])

            print('Done')
