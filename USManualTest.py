import configparser
import os
import sys
import warnings

import pandas as pd
from colorama import Fore, Style

# from GenerateManualTest import ManualTestProcessor
from us_to_mtc_file.GenerateManualTest import ManualTestProcessor


class ManualTestGenerator:
    def __init__(self):

        warnings.filterwarnings("ignore")
        self.config_path = 'Config'
        self.config_parser_io = configparser.ConfigParser()
        self.config_parser_io.read(self.config_path + '/ConfigIO.properties')

        # Reading values from configuration file
        self.input_file_path = self.config_parser_io.get('Input', 'input_file_path')
        self.input_filename = os.path.basename(self.input_file_path)
        self.additional_context_path = self.config_parser_io.get('Input', 'additional_context_path')
        self.additional_context_name = os.path.basename(self.additional_context_path)
        self.override_context = self.config_parser_io.get('Input', 'overwrite_context')
        self.manual_test_type = self.config_parser_io.get('Output', 'manual_test_type')
        self.output_file_path = self.config_parser_io.get('Output', 'output_file_path')

    def process_user_stories(self):
        manual_test_processor = ManualTestProcessor()
        header = "MANUAL TEST GENERATOR"
        line_length = 60
        padding_length = (line_length - len(header)) // 2
        padding = " " * padding_length
        print("*" * line_length)
        print("*" + padding + header + padding + "*")
        print("*" * line_length + "\n")

        if self.input_file_path != '':
            try:
                # Reading Input file and throws exception if file not found
                input_us = pd.read_excel(self.input_file_path)
                print("Processing input User Stories from", self.input_filename, "\n")
            except FileNotFoundError:
                print(
                    Fore.RED + "Input user story File not found. Check the name of file or provide the file"
                    + Style.RESET_ALL)
                sys.exit()
        else:
            print("Please provide input user story file path in configuration file")
            sys.exit()

        if self.additional_context_path != '':
            try:
                input_context = pd.read_excel(self.additional_context_path)
                print("Processing input Additional Context from", self.additional_context_name, "\n")
                context_choice = input("\nDo you want to use the context? (Yes/No): ")
                if context_choice == "Yes" or context_choice == "yes":
                    manual_test_processor.gen_manual_test_context(input_us, self.manual_test_type, input_context,
                                                                  self.output_file_path, self.override_context)
                else:
                    print("\nGenerating manual test without using the context\n")
                    manual_test_processor.generate_manual_test(input_us, self.manual_test_type, self.output_file_path)
            except FileNotFoundError as e:

                print('Input Additional Context File not found. Check the name of file or provide the file')
                sys.exit()
        else:
            print("\nNo Additional Context file provided. Generating Manual Test without context\n")
            manual_test_processor.generate_manual_test(input_us, self.manual_test_type, self.output_file_path)


mtg = ManualTestGenerator()
mtg.process_user_stories()

sys.exit()
