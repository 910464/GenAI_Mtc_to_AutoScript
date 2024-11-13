from langchain.embeddings import HuggingFaceEmbeddings
from langchain.prompts.prompt import PromptTemplate
from langchain import LLMChain
from langchain.chat_models import AzureChatOpenAI
from Src.CoreLogicLayer.IntelligentAutomation.FunctionalTestAutomation.SharedResources import config
from pathlib import Path

import os
import re
import pandas as pd
import datetime
import re


class TestCaseCreator:
    def __init__(self):
        os.environ["OPENAI_API_TYPE"] = "azure"
        os.environ["OPENAI_API_VERSION"] = "2023-03-15-preview"
        os.environ["OPENAI_API_BASE"] = "https://exploregenaiworkspace.openai.azure.com"
        os.environ["OPENAI_API_KEY"] = "0b1d7d099829418fb1293b97f2ae9c23"

    # def __init__(self):
    #     os.environ["OPENAI_API_TYPE"].OPENAI_API_TYPE = "azure"
    #     self.OPENAI_API_VERSION = "2023-03-15-preview"
    #     self.OPENAI_API_BASE = "https://exploregenaiworkspace.openai.azure.com"
    #     self.OPENAI_API_KEY = "0b1d7d099829418fb1293b97f2ae9c23"

    def remove_comments(self, text):
        # Remove single-line comments
        text = re.sub(r'//.*', '', text)

        # Remove multi-line comments
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

        return text

    def remove_extra_spaces(self, text):
        # Remove extra white spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def list_excl_files(self, directory):
        xls_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".xls") or file.endswith(".xlsx"):
                    xls_files.append(os.path.join(root, file))
        return xls_files

    def find_java_files(self, directory):
        java_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".java"):
                    java_files.append(os.path.join(root, file))
        return java_files

    def extract_relevant_files(self, root_directory):
        testscripts_directory = os.path.join(root_directory, "testscripts")
        page_directory = os.path.join(root_directory, "pages")

        if not os.path.exists(testscripts_directory) or not os.path.exists(page_directory):
            return "testscripts or pages packages not found"

        testscripts_java_files = TestCaseCreator.find_java_files(TestCaseCreator, testscripts_directory)
        page_java_files = TestCaseCreator.find_java_files(TestCaseCreator, page_directory)

        class_names = []
        for java_file in page_java_files:
            with open(java_file, "r") as file:
                content = file.read()
                class_matches = re.finditer(r'class\s+(\w+)', content)
                for match in class_matches:
                    class_name = match.group(1)
                    class_names.append(class_name)

        dict_runner = {}

        for java_file in testscripts_java_files:
            with open(java_file, "r") as file:
                content = file.read()
                relevant_class_files = []
                for class_name in class_names:
                    if f"import pages.{class_name}" in content:
                        relevant_class_files.append(page_java_files[class_names.index(class_name)])
                dict_runner[java_file] = relevant_class_files

        return dict_runner

    def is_method_name_present(self, file_path, method_list):
        try:
            all_methods_in_single_file = True
            with open(file_path, 'r') as file:
                content = file.read()
                content = self.remove_comments(content)
                content = self.remove_extra_spaces(content)
                # # Remove comments and whitespace to simplify method search
                # content = ' '.join(content.split())  # Remove whitespace
                # content = ''.join([line for line in content.split('\n') if
                #                    not line.strip().startswith('//')])  # Remove single-line comments
                # content = ''.join([line for line in content.split('\n') if
                #                    not line.strip().startswith('/*') and not line.strip().endswith(
                #                        '*/')])
                for method_name in method_list:
                    method_n = method_name[0].lower() + method_name[1:]
                    if method_n in content:
                        all_methods_in_single_file = True
                    else:
                        all_methods_in_single_file = False
                        return all_methods_in_single_file
                return all_methods_in_single_file
        except FileNotFoundError:
            return False

    def extract_relevant_files_for_keyword_driven_approach(self, list_of_methods, root_directory, all_data):
        print("extract_relevant_files_for_keyword_driven_approach")
        page_directory = os.path.join(root_directory, "pages")
        page_java_files = TestCaseCreator.find_java_files(TestCaseCreator, page_directory)
        class_names = []
        output_files = 0
        for java_file in page_java_files:
            with open(java_file, "r") as file:
                content = file.read()
                class_matches = re.finditer(r'class\s+(\w+)', content)
                for match in class_matches:
                    class_name = match.group(1)
                    class_names.append(class_name)

        business_components_directory = os.path.join(root_directory, "businesscomponents")
        component_groups_directory = os.path.join(root_directory, "componentgroups")
        list_of_component_classes_for_search = []
        for root, _, files in os.walk(business_components_directory):
            for file in files:
                if file.endswith(".java"):
                    list_of_component_classes_for_search.append(os.path.join(root, file))
        for root, _, files in os.walk(component_groups_directory):
            for file in files:
                if file.endswith(".java"):
                    list_of_component_classes_for_search.append(os.path.join(root, file))
        # remove top one as its name not referred as method in code
        excel_column_0 = list_of_methods[0]
        list_of_methods.pop(0)
        for component_class in list_of_component_classes_for_search:
            result = self.is_method_name_present(component_class, list_of_methods)
            if result:
                print('all methods are available in component class: ', component_class)
                # use this component class, lookout for page classes, and prepare data for MTC
                dict_runner = {}
                with open(component_class, "r") as file:
                    content = file.read()
                    relevant_class_files = []
                    for class_name in class_names:
                        if f"import pages.{class_name}" in content:
                            relevant_class_files.append(page_java_files[class_names.index(class_name)])
                    dict_runner[component_class] = relevant_class_files
                    runner_class_details = dict_runner
                    page_classes = []
                    runner_class = ''
                    for key, value in runner_class_details.items():
                        # get the code
                        runner_class = self.read_automation_script_struct(key)
                        page_classes = []
                        for page_class in value:
                            page_code = self.read_automation_script_struct(page_class)
                            page_classes.append(page_code)
                        self.prompt_to_analyze_keyword_driven_craft_script(runner_class, page_classes, key,
                                                                               list_of_methods, all_data, root_directory, excel_column_0)
                        output_files += 1
        return output_files
        # ---------------------------------------------------------------------------------------------------

    def read_automation_script_struct(self, path):
        # read and prepare the automation flow details
        file_path = path
        try:
            with open(file_path, 'r') as file:
                file_contents = file.read()
                return file_contents
        except FileNotFoundError:
            print(f"The file '{file_path}' was not found.")
        except IOError as e:
            print(f"An error occurred while reading the file: {e}")

    def prompt_to_analyze_script(self, java_selenium_code):
        # use automation flow details in prompt to create Manual Test Cases
        print('prompt - Manual Test Case Creator')
        prompt_for_test_case = """
        Generate a Manual Test Case scenario based on the analysis with the below conditions applied,
        I am giving you a java selenium code, understand and detect the flow of execution in code,
        detect the flow and write a Manual Test Case scenario, return only Manual Test Case scenario 
        with stepwise details to follow
        Java Selenium code:
        {java_selenium_code}
        """
        complete_prompt_manual_test = PromptTemplate(
            input_variables=["java_selenium_code"],
            template=prompt_for_test_case)
        request_manual_test_case = LLMChain(
            llm=AzureChatOpenAI(deployment_name="gpt35exploration", model_name="gpt-35-turbo", temperature=0.3),
            prompt=complete_prompt_manual_test)
        manual_test_case = request_manual_test_case.run(
            {'java_selenium_code': java_selenium_code})
        print("output: ", manual_test_case)

    def prompt_to_analyze_craft_script(self, runner_class, list_of_page_classes, loc, craft_root_dir):
        # use automation flow details in prompt to create Manual Test Cases
        print('prompt - Manual Test Case Creator')
        prompt_for_test_case = """
        Generate a Manual Test Case scenario based on the analysis with the below conditions applied,
        I am giving you a java selenium code based on CRAFT framework with modular driver approach, 
        In modular driven approach there is a Runner Class which contains the execution flow and invokes methods to 
        execute from page classes. 
        understand and detect the flow of execution in code,
        detect the flow and write a Manual Test Case scenario, return only Manual Test Case scenario 
        with stepwise details to follow
        Java Selenium code of Runner Class:
        {runner_class}
        Java Selenium code of Page Classes:
        {list_of_page_classes}
        """
        complete_prompt_manual_test = PromptTemplate(
            input_variables=["runner_class", "list_of_page_classes"],
            template=prompt_for_test_case)
        request_manual_test_case = LLMChain(
            llm=AzureChatOpenAI(deployment_name="gpt35exploration", model_name="gpt-35-turbo", temperature=0.3),
            prompt=complete_prompt_manual_test)
        manual_test_case = request_manual_test_case.run(
            {'runner_class': runner_class, 'list_of_page_classes': list_of_page_classes})

        #Writing manual testcase to the exisiting automation script location
        # print("output: ", manual_test_case)
        out_path = str(loc) + "ManualTestCase.txt"
        # print("out_path: " + out_path)
        # with open(out_path, "w") as file:
        #     file.write(manual_test_case)

        # Writing manual testcase to the output location for better acces for fetching results
        updated_path = craft_root_dir + '/ManualTcs' + out_path.split(craft_root_dir)[1]
        print("updated_path: + " + updated_path)
        output_file = Path(updated_path)
        output_file.parent.mkdir(exist_ok=True, parents=True)
        with open(updated_path, "w") as result_file:
            result_file.write(manual_test_case)

    def prompt_to_analyze_keyword_driven_craft_script(self, runner_class, list_of_page_classes, loc, method_list,
                                                      all_data, craft_root_dir, excel_column_0):
        # use automation flow details in prompt to create Manual Test Cases
        print('prompt - Manual Test Case Creator')
        prompt_for_test_case = """
        Generate a Manual Test Case scenario based on the analysis with the below conditions applied,
        I am giving you a java selenium code based on CRAFT framework with modular driver approach, 
        In modular driven approach there is a Runner Class which contains the execution flow and invokes methods to 
        execute from page classes. 
        understand and detect the flow of execution in code,
        detect the flow and write a Manual Test Case scenario, return only Manual Test Case scenario 
        with stepwise details to follow.
        Java Selenium code of Runner Class:
        {runner_class}
        From above Runner Class code, use only below methods to create Manual Test Case scenario:
        {method_list}
        Java Selenium code of Page Classes:
        {list_of_page_classes}
        Test Data to use as applicable:
        {all_data}
        Ensure:
        1. Given list of methods gives main execution flow and test data to use.
        2. Now analyze use of "if/else/switch case" conditions in code, detect hierarchical usage as well and prepare 
        all possible execution flows considering hierarchical usage, each execution flow consists all given list of methods
        3. Based on test data value, use only execution flow which is applicable as per test data value.
        4. Based on detected execution flows in Runner class, strictly generate separate Manual Test Case scenario
        5. For such separate Manual Test Case scenario, prepare and return Manual Test Case.
        6. For datatable use in code, identify variables used to fetch data and use same in Manual Test Case steps.
        7. Only generate Manual Test Cases for those Execution flows for whom valid data is provided
        8. Strictly use only provided Test Data and generate Manual Test Case which have all fields with valid test data from provided list of test data
        
        Make sure to return list of Manual Test Cases for each execution flow as per automation script code.
        Follow below syntax to write Manual Test Case:
        1. Summary:
        2. PreCondition:
        3. Steps of Execution:
        4. Expected Result:
        5. Test data:
        """
        complete_prompt_manual_test = PromptTemplate(
            input_variables=["runner_class", "method_list", "list_of_page_classes", "all_data"],
            template=prompt_for_test_case)
        request_manual_test_case = LLMChain(
            llm=AzureChatOpenAI(deployment_name="gpt35exploration", model_name="gpt-35-turbo", temperature=0.4),
            prompt=complete_prompt_manual_test)
        all_data_n = pd.DataFrame(all_data).to_dict(orient='records')[0]
        manual_test_case = request_manual_test_case.run(
            {'runner_class': runner_class, 'method_list': method_list, 'list_of_page_classes': list_of_page_classes,
             'all_data': all_data_n})

        # print("output: ", manual_test_case)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        out_path = str(loc).split(".java")[0] + "_" + excel_column_0 + "_ManualTestCase" + ".txt"
        # print("out_path: " + out_path)
        # with open(out_path, "w") as file:
        #     file.write(manual_test_case)

        # Writing manual testcase to the output location for better acces for fetching results
        updated_path = craft_root_dir + '/ManualTcs' + out_path.split(craft_root_dir)[1]
        print("updated_path: + " + updated_path)
        output_file = Path(updated_path)
        output_file.parent.mkdir(exist_ok=True, parents=True)
        with open(updated_path, "w") as result_file:
            result_file.write(manual_test_case)
