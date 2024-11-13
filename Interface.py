import os

from Src.BaseLayer.AutomationTestCaseBaseModel import AutomationScriptFramework
from Src.Constants import DBConstants
from Src.CoreLogicLayer.TestPlanning.ManualTestCaseGeneration.src.TestCaseCreator import TestCaseCreator
from Src.DAOLayer.MongoReadWrite import mongoReadWrite
from datetime import datetime
import time
from Src.CoreLogicLayer.TestPlanning.ManualTestCaseGeneration.src.GenerateTCS import generate
import pandas as pd
import re
import traceback

from Src.Utilities.FileHandling.EmptyDirectory import EmptyDirectory
from Src.Utilities.FileHandling.FileHandling import create_zip

mongo_obj = mongoReadWrite()

def generate_tcs(processing_json):
    print('Inside generateTCS')
    start = time.time()
    print(processing_json['jobID'])
    execution_details = {'jobID':processing_json['jobID'],'userStoryID':processing_json['userStoryID'],'description': 'Not decided yet', 'useCaseName': processing_json['useCaseName'],
                         'generationOption': str(processing_json), 'input': 1, 'output': 'N/A',
                         'executedOn': datetime.now().strftime("%dth %b, %Y %H:%M:%S"), 'timeTaken': 0,
                         'executedBy': processing_json['executedBy'], 'executionStatus': 'Generating'}

    if processing_json['isMultipleUserStory']:
        execution_details['input'] = len(processing_json['multipleUserStory'])

    execution_details_df = pd.DataFrame(execution_details, index=[0])
    mongo_obj.write_data(DBConstants.EXECUTION_SUMMARY_COLLECTION, execution_details_df)
    try:
        generate(input_param=processing_json)
        if processing_json['isSingleUserStory']:
            data = []
            tcs_df = mongo_obj.read_data_with_filter(DBConstants.TESTCASE_COLLECTION, "userStoryID::eq::" + processing_json['userStoryID'] + "<<>>jobID::eq::" + processing_json['jobID'], 0)

            # scenarios = re.split(r"Negative Test Case: |Positive Test Case: ", tcs_df.iloc[0]['generatedTCS'])[1:]
            scenarios = tcs_df.iloc[0]['generatedTCS']
            scenario_outline = ''
            scenario_name = ''
            index = 0
            for scenario in scenarios.split('\n'):
                if 'Negative Test Case' in scenario or 'Positive Test Case' in scenario:
                    if index==0:
                        index = 1
                        scenario_name = scenario
                    else:
                        data.append({
                            "TestCases": scenario_name,
                            "feature": "Test Steps: " + scenario_outline
                        })
                        scenario_outline = ''
                        scenario_name = scenario
                else:
                    scenario_outline = scenario+'\n'

            data.append({
                "TestCases": scenario_name,
                "feature": "Test Steps: " + scenario_outline
            })
            execution_details['executionStatus'] = 'Completed'
            execution_details['output'] = len(data)

            execution_details['timeTaken'] = time.time() - start
            execution_details_df = pd.DataFrame(execution_details, index=[0])

            mongo_obj.update_data_based_on_jobid(DBConstants.EXECUTION_SUMMARY_COLLECTION, execution_details_df, execution_details['jobID'])

            return {"message": 'Test Case Generation Successful', "status": 200}

        else:
            multi_us = processing_json['multipleUserStory']
            data = []
            for userstory_id in multi_us:
                tcs_df = mongo_obj.read_data_with_filter(DBConstants.TESTCASE_COLLECTION, "userStoryID::eq::" + userstory_id.split('.')[0] + "<<>>jobID::eq::" + processing_json['jobID'],0)

                scenarios = tcs_df.iloc[0]['generatedTCS']
                scenario_outline = ''
                scenario_name = ''
                index = 0
                for scenario in scenarios.split('\n'):
                    if 'Negative Test Case' in scenario or 'Positive Test Case' in scenario:
                        if index == 0:
                            index = 1
                            scenario_name = scenario
                        else:
                            data.append({
                                "TestCases": scenario_name,
                                "feature": "Test Steps: " + scenario_outline
                            })
                            scenario_outline = ''
                            scenario_name = scenario
                    else:
                        scenario_outline = scenario + '\n'

                data.append({
                    "TestCases": scenario_name,
                    "feature": "Test Steps: " + scenario_outline
                })

            print(len(data))
            execution_details['executionStatus'] = 'Completed'
            execution_details['output'] = len(data)

            execution_details['timeTaken'] = time.time() - start
            execution_details_df = pd.DataFrame(execution_details, index=[0])

            mongo_obj.update_data_based_on_jobid(DBConstants.EXECUTION_SUMMARY_COLLECTION, execution_details_df,
                                                execution_details['jobID'])

            return {"message": 'Test Case Generation Successful', "status": 200}
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        execution_details['executionStatus'] = 'Failed'
        execution_details['timeTaken'] = time.time() - start
        execution_details_df = pd.DataFrame(execution_details, index=[0])
        mongo_obj.update_data_based_on_jobid(DBConstants.EXECUTION_SUMMARY_COLLECTION, execution_details_df, execution_details['jobID'])
        return {"message": 'Test Case Generation Failed', "status": 500}

def get_tcs_result(jobID):
    tcs_df = mongo_obj.read_data_with_filter(DBConstants.TESTCASE_COLLECTION, "jobID::eq::" + jobID, 50)
    results = []
    for scenarios in tcs_df[['generatedTCS','userStoryID','inputUserstory']].values:

        # print(scenarios[0])
        test_cases = []
        lines = scenarios[0].split('\n')
        lines = [i for i in lines if len(i)>1]
        steps = ''
        description = ''
        for i in lines:
            print(i)
            if 'Negative Test Case' in i or 'Positive Test Case' in i:
                if description != '':
                    try:
                        test_cases.append({'TestCase': description.split(':')[1].strip(),
                                        'Description': description+'\n'+steps})
                    except:
                        test_cases.append({'TestCase': description,
                                           'Description': description + '\n' + steps})

                description = i
                steps = ''
            else:
                steps += i + '\n'

        try:
            test_cases.append({'TestCase': description.split(':')[1].strip(),
                               'Description': description+'\n'+steps})
        except:
            test_cases.append({'TestCase': description,
                               'Description': description + '\n' + steps})

        if len(test_cases) == 0:
            results.append({"userStoryID": scenarios[1], "userStory": scenarios[2],
                        "message": 'Test Case Generation Failed', "status": 500})
        else:
            results.append({"userStoryID": scenarios[1], "userStory": scenarios[2],
                        "testCase": test_cases})
    return results

def read_tcs_data(jobID):
    tcs_df = mongo_obj.read_data_with_filter(DBConstants.TESTCASE_COLLECTION, "jobID::eq::" + jobID, 0)
    return tcs_df

def generate_tcs_from_automation_script(processing_json):
    start = time.time()
    print("Inside generate_tcs_from_automation_script")
    print(processing_json)
    magic_o2 = TestCaseCreator()
    # file_p = 'C:/Users/SRJSNGFST/Documents/EcomExpert.java'
    # selenium_java_dir = magic_o2.read_automation_script_struct(file_p)
    # magic_o2.prompt_to_analyze_script(selenium_java_dir)
    executedBy = processing_json["executedBy"]
    projectID = processing_json["project_id"]
    useCaseName = processing_json["useCaseName"]
    automationScriptList = processing_json["automationScriptList"]
    output_files = 0
    print(processing_json['jobID'])
    execution_details = {'jobID': processing_json['jobID'], 'userStoryID': "",
                         'description': 'Not decided yet', 'useCaseName': processing_json['useCaseName'],
                         'generationOption': str(processing_json), 'input': len(automationScriptList), 'output': 'N/A',
                         'executedOn': datetime.now().strftime("%dth %b, %Y %H:%M:%S"), 'timeTaken': 0,
                         'executedBy': processing_json['executedBy'], 'executionStatus': 'Generating'}

    timestamp = execution_details['executedOn'].replace(' ', '').replace(':', '')
    execution_details_df = pd.DataFrame(execution_details, index=[0])

    mongo_obj.write_data(DBConstants.EXECUTION_SUMMARY_COLLECTION, execution_details_df)

    for automationScriptName in automationScriptList:
        automationScriptDF = mongo_obj.read_data_with_filter(DBConstants.ASTC_COLLECTION,
                                                                  "project_id::eq::" + projectID + "<<>>name::eq::" + automationScriptName,
                                                                 1)
        automationScript_data = automationScriptDF.iloc[0, :]
        automationScript = AutomationScriptFramework(**automationScript_data.to_dict())
        framework = automationScript.framework
        module_driven = False
        keyword_driven = False
        if "keyword-driven" in framework:
            keyword_driven = True
        elif "module-driven" in framework:
            module_driven = True
        print(automationScript)
        if module_driven:
            print("Module-Driven")
            craft_root_dir = automationScript.basePath + automationScript.rootPath
            # craft_root_dir = "../dataupload/Cognizant-Reusable-Automation-Framework-for-Testing/modularDriven-maven-testng-framework/src/test/java"
            # "C:/Users/SRJSNGFST/Downloads/CRAFT_/Cognizant-Reusable-Automation-Framework-for-Testing-master/modularDriven-maven-testng-framework/src/test/java"
            # ------------------- Moduler Driven Flow ------------------------------------------------------------------ #
            runner_class_details = magic_o2.extract_relevant_files(craft_root_dir)
            page_classes = []
            runner_class = ''
            print("runner class details : ")
            print(runner_class_details)
            for key, value in runner_class_details.items():
                # get the code
                runner_class = magic_o2.read_automation_script_struct(key)
                page_classes = []
                for page_class in value:
                    page_code = magic_o2.read_automation_script_struct(page_class)
                    page_classes.append(page_code)
                magic_o2.prompt_to_analyze_craft_script(runner_class, page_classes, key, craft_root_dir)
                output_files += 1
            create_zip(
                f"{craft_root_dir}/ManualTcs",
                f"../automationScriptTc/{automationScriptName}_Generated_ManualTcs.zip")
            mongo_obj.store_zip_in_mongodb(DBConstants.MANUALTC_COLLECTION,
                                           f"../automationScriptTc/{automationScriptName}_Generated_ManualTcs.zip",
                                           execution_details['jobID'])

            # Clean up: remove the temporary ZIP file
            # os.remove(f"../automationScriptTc/{automationScriptName}_Generated_ManualTcs.zip")
            # remover = EmptyDirectory()
            # remover.remove(f"{craft_root_dir}/ManualTcs")
            #
            # return {"message": "Script generated successfully"}

        if keyword_driven:
            print("Keyword-driven")
            craft_root_dir = automationScript.basePath + automationScript.rootPath
            # craft_root_dir = "../dataupload/Cognizant-Reusable-Automation-Framework-for-Testing/keywordDriven-maven-testng-framework/src/test/java"
            # "C:/Users/SRJSNGFST/Downloads/CRAFT001/qea-tech-coe_automation-frameworks_craft_craft-maven-master/CRAFT_Maven/src/test/java"
            # ------------------- Keyword Driven Flow ------------------------------------------ #
            craft_resource_dir = automationScript.basePath + automationScript.resourcePath
            # craft_resource_dir = "../dataupload/Cognizant-Reusable-Automation-Framework-for-Testing/keywordDriven-maven-testng-framework/src/test/resources/Datatables"
            # "C:/Users/SRJSNGFST/Downloads/CRAFT001/qea-tech-coe_automation-frameworks_craft_craft-maven-master/CRAFT_Maven/src/test/resources/Datatables"
            list_of_data_files_to_run_test_scenario = magic_o2.list_excl_files(craft_resource_dir)

            for data_file in list_of_data_files_to_run_test_scenario:
                get_business_flow = pd.read_excel(data_file, sheet_name='Business_Flow')
                get_general_data = pd.read_excel(data_file, sheet_name='General_Data')
                get_business_flow.dropna(axis=1, inplace=True)
                for index, row in get_business_flow.iterrows():
                    list_of_methods = []
                    inter = get_general_data.iloc[[index]]
                    inter.dropna(axis=1, inplace=True)
                    for method in row:
                        method_n = str(method).split(',')[0]
                        list_of_methods.append(method_n)
                    print('list_of_methods: ', list_of_methods)
                    # pass this list of methods to a function which will search in component package the relevant component class
                    # and its imports from page class, pass these collected info in prompt to understand and create MTC
                    output_files += magic_o2.extract_relevant_files_for_keyword_driven_approach(list_of_methods, craft_root_dir, inter)
                    # # assuming that we will always have list of methods in valid excel, so first entry in row is key
                    # # and not related to any method name to execute, so we can delete is for further processing
                    # list_of_methods.pop(0)
                    # print(get_business_flow)

                # print(get_business_flow)
            create_zip(
                f"{craft_root_dir}/ManualTcs",
                f"../automationScriptTc/{automationScriptName}_Generated_ManualTcs.zip")
            mongo_obj.store_zip_in_mongodb(DBConstants.MANUALTC_COLLECTION,
                                           f"../automationScriptTc/{automationScriptName}_Generated_ManualTcs.zip",
                                           execution_details['jobID'])

            # ---------------------------------------------------------------------------------------------------------- #

    execution_details['executionStatus'] = 'Completed'
    execution_details['output'] = output_files

    execution_details['timeTaken'] = time.time() - start
    execution_details_df = pd.DataFrame(execution_details, index=[0])
    mongo_obj.update_data_based_on_jobid(DBConstants.EXECUTION_SUMMARY_COLLECTION, execution_details_df,
                                                execution_details['jobID'])
    return {"message": 'Automation Script to Manual Test Case Generation Successful', "status": 200}
