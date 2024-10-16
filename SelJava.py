import json
import logging
import os.path
import shutil

from Src.Constants import PathConstants
from Src.CoreLogicLayer.IntelligentAutomation.FunctionalTestAutomation.SeleniumJava.CraftAzureConnect import \
    CraftAsureConnect
from Src.CoreLogicLayer.IntelligentAutomation.FunctionalTestAutomation.SharedResources.Utils.Parsers.Framework_Integration import \
    required_imports, load_dependents, load_src_vectors
from Src.CoreLogicLayer.IntelligentAutomation.FunctionalTestAutomation.SharedResources.Utils.Parsers.parseClassCodeToCsv import \
    ParseClassCodeToCsv
from Src.DAOLayer.ChromaDBConnector import ChromaDBConnector
from Src.DAOLayer.MongoReadWrite import mongoReadWrite

from Src.Utilities.FileHandling.FileHandling import get_filenames

# seleJavaPath = "../CoreLogicLayer/IntelligentAutomation/FunctionalTestAutomation/SeleniumJava"

mongo_obj = mongoReadWrite()


def java_generator(df_inter, input_param):

    # Store project data within project folder
    sele_java_data_path = PathConstants.SELE_JAVA.format(input_param['projectID'])
    sele_java_framework_path = PathConstants.SELE_JAVA_FRAMEWORK_FOLDER.format(input_param['projectID'])
    sele_java_scripts_path = PathConstants.SELE_JAVA_SCRIPTS_FOLDER.format(input_param['projectID'])
    sele_java_reviewed_path = PathConstants.SELE_JAVA_REVIEWD_SCRIPTS_FOLDER.format(input_param['projectID'])
    sele_java_output_path = PathConstants.SELE_JAVA_OUTPUT_PATH.format(input_param['projectID'])

    # check if reviewed folder is having atleast 1 file, if empty, check output folder is not empty, if not empty move files to
    # reviewed folder
    if not os.path.exists(sele_java_reviewed_path):
        os.makedirs(sele_java_reviewed_path)

    # Delete output folder, using shutil
    if os.path.exists(sele_java_output_path):
        shutil.rmtree(sele_java_output_path)

    # set reviewed exists as True in input param if files exists in reviewed folder
    input_param['reviewed_exists'] = bool(os.listdir(sele_java_reviewed_path))

    # Common folders for any framework, moved outside of CRAFT block
    class_parser = ParseClassCodeToCsv()  # To parse reusable files
    if not os.path.exists(f"{sele_java_data_path}/csv_data"):  # To create dir '/data/csv_data' if not present
        os.makedirs(f"{sele_java_data_path}/csv_data")

    if not os.path.exists(f"{sele_java_data_path}/gen_code_csv"):  # To create dir if not present
        os.makedirs(f"{sele_java_data_path}/gen_code_csv")
    # else:
        # shutil.rmtree(f"{sele_java_data_path}/gen_code_csv") # reviewed scripts should be parsed in every run
        # pass
    if not os.path.exists(f"{sele_java_data_path}/embed_data_gen"):  # To create dir if not present
        os.makedirs(f"{sele_java_data_path}/embed_data_gen")
    # else:
        # shutil.rmtree(f"{sele_java_data_path}/embed_data_gen") # reviewed scripts should be embedded in every run

    if input_param['isCRAFT']:

        mongo_obj.update_field_based_on_jobid('ExecutionSummary', input_param['jobID'], 'detailedStatus',
                                              [{"title": "Analyzing test case",
                                                "status": "completed"},
                                               {"title": "Gathering script context",
                                                "status": "inprogress"}])
        # if not os.path.exists(f"{seleJavaPath}/data/csv_data"):
        #     os.makedirs(f"{seleJavaPath}/data/csv_data")
        # parser = ParseClassCodeToCsv()

        exclude_files = class_parser.parse_data(
            sele_java_framework_path,
            f"{sele_java_data_path}/csv_data"
        )
        print("Excluded files: ", exclude_files)

        # Component names and their directory names
        components = {
            'pages': 'pages',
            'businesscomponents': 'businesscomponents',
            'testscripts': 'testscripts'
        }
        core_db = None
        if not os.path.exists(f"{sele_java_data_path}/embed_data_core"):
            core_db = ChromaDBConnector(f"{sele_java_data_path}/embed_data_core")
            core_db.vectordb_store_dir(f"{sele_java_data_path}/csv_data")

        # creating csv and code ingestor objects
        csv_ingestor = ChromaDBConnector(f"{sele_java_data_path}/embed_data_gen/csv")
        code_ingestor = ChromaDBConnector(f"{sele_java_data_path}/embed_data_gen/code")

        # Embedding reviewed scripts
        if input_param['reviewed_exists']:
            for component, source in components.items():
                load_src_vectors(sele_java_reviewed_path, source, "java", sele_java_data_path, comp_type=component, csv_ingestor=csv_ingestor, code_ingestor=code_ingestor)

        input_param['reusable_class_names'] = required_imports(
            os.path.abspath(sele_java_framework_path),
            os.path.abspath(sele_java_scripts_path),
            exclude_files,
            components.keys(),
            'java'
        )

        # Extracting dependencies
        input_param['dependency_schema'] = load_dependents(sele_java_reviewed_path, 'java')
        input_param['pages'] = get_filenames(f"{sele_java_reviewed_path}/{components['pages']}", "java")

        if input_param['dependency_schema']:
            print(f"Dependencies extracted successfully!\n{json.dumps(input_param['dependency_schema'], indent=4)}")

        # comp_code = ""
        # component_classes = []
        connector = CraftAsureConnect(input_param, source_code_store=code_ingestor, csv_store=csv_ingestor,
                                      data_path=sele_java_data_path, output_path=sele_java_output_path, core_store=core_db)
        mongo_obj.update_field_based_on_jobid('ExecutionSummary', input_param['jobID'], 'detailedStatus',
                                              [{"title": "Analyzing test case",
                                                "status": "completed"},
                                               {"title": "Gathering script context",
                                                "status": "completed"},
                                               {"title": "Determining reusability scope",
                                                "status": "inprogress"}])

        if input_param['pages']:
            connector.map_pages(existing=input_param['pages'], page_data=df_inter)

        business_components = []
        business_component_names = []
        page_wise = df_inter.groupby("page", sort=False)
        for page_name, page_data in page_wise:
            mongo_obj.update_field_based_on_jobid('ExecutionSummary', input_param['jobID'], 'detailedStatus',
                                                  [{"title": "Analyzing test case",
                                                    "status": "completed"},
                                                   {"title": "Gathering script context",
                                                    "status": "completed"},
                                                   {"title": "Determining reusability scope",
                                                    "status": "completed"},
                                                   {"title": "Prompt engineering with dynamic context",
                                                    "status": "completed"},
                                                   {"title": "Generating Automation scripts",
                                                    "status": "inprogress"}]
                                                  )
        #     print(f"Processing Group '{page_name}':")
        #     print(page_data)
        #     CraftAsureConnect(input_param)
        #     comp_code += connector.page_comp_code_generation(page_name, page_data, input_param)
        #     comp_code += "\n\n\n\n"
        #     component_classes.append(page_name)
        # connector.test_script_code_generation('Runner', component_classes, comp_code, input_param)
            page_code, page_name = connector.page_class_generator(
                page_name=page_name,
                page_data=page_data
            )
            print(f"Page Name: {page_name}")
            print(f"Page Code: {page_code}")

            business_component_code, business_component_name = connector.component_class_generator(
                page_name=page_name,
                page_code=page_code,
                page_data=page_data
            )
            print(f"Component Name: {business_component_name}")
            print(f"Component Code: {business_component_code}")

            business_components.append(business_component_code)
            business_component_names.append(business_component_name)

        test_script, test_script_name = connector.test_script_code_generation(
            business_components=business_components,
            business_component_names=business_component_names,
            page_data=df_inter
        )
        print(f"Test Script Name: {test_script_name}")
        print(f"Test Script: {test_script}")
        print("SELENIUM JAVA SCRIPT GENERATION COMPLETED")

