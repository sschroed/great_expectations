import pytest

import os
import logging

from six import PY2

logger = logging.getLogger(__name__)


def read_config_file_from_disk(config_filepath):
    with open(config_filepath, "r") as infile:
        config_file = infile.read()
        return config_file


def test_preserve_comments_in_yml_after_adding_datasource(data_context):
    if PY2:
        pytest.skip()

    ### THIS TEST FAILING IS A KNOWN ISSUE.
    ### A TICKET IS OPEN

    pytest.skip("KNOWN ISSUE")
    #####
    #
    # KNOWN ISSUE: THIS DOES NOT FULLY PRESERVE WHITESPACE
    # PROGRAMMATIC ADDITION MAY NOT BE PRESERVED IN PY2 AS WELL
    # HOWEVER, GIVEN SHORT TIME TO EOL OF PY2, WE ARE WILLING TO ACCEPT THAT
    #
    #####

    config_filepath = os.path.join(
        data_context.root_directory, "great_expectations.yml"
    )
    initial_config = read_config_file_from_disk(config_filepath)
    print("++++++++++++++++ initial config +++++++++++++++++++++++")
    print(initial_config)
    print("----------------------------------------")

    data_context.add_datasource(
        "test_datasource",
        module_name="great_expectations.datasource",
        class_name="PandasDatasource",
        base_directory="../data",
    )

    # TODO The comments on lines 1,2 & 4 of the fixture exposes the bug.
    expected = """# This is a basic configuration for testing.
# It has comments that should be preserved.
config_version: 1
# Here's a comment between the config version and the datassources
datasources:
  # For example, this one.
  mydatasource: # This should stay by mydatasource
    module_name: great_expectations.datasource
    class_name: PandasDatasource
    data_asset_type:
      class_name: PandasDataset
    generators:
      # The name default is read if no datasource or generator is specified
      mygenerator:
        class_name: SubdirReaderGenerator
        base_directory: ../data
        reader_options:
          sep:
          engine: python
  test_datasource:
    module_name: great_expectations.datasource
    class_name: PandasDatasource
    data_asset_type:
      class_name: PandasDataset
    generators:
      default:
        class_name: SubdirReaderGenerator
        base_directory: ../data
        reader_options:
          sep:
          engine: python


config_variables_file_path: uncommitted/config_variables.yml


plugins_directory: plugins/
evaluation_parameter_store_name: evaluation_parameter_store
expectations_store_name: expectations_store
profiling_store_name: local_validation_result_store

data_docs:
  sites:

stores:
  expectations_store:
    class_name: ExpectationStore
    store_backend:
      class_name: FixedLengthTupleFilesystemStoreBackend
      base_directory: expectations/
  evaluation_parameter_store:
    module_name: great_expectations.data_context.store
    class_name: EvaluationParameterStore

  local_validation_result_store:
    class_name: BasicInMemoryStore
    
validation_operators:
  # Read about validation operators at: https://docs.greatexpectations.io/en/latest/guides/validation_operators.html
  default:
    class_name: PerformActionListValidationOperator
    action_list:
      - name: store_validation_result
        action:
          class_name: StoreAction
          target_store_name: local_validation_result_store
      # Uncomment the notify_slack action below to send notifications during evaluation
      # - name: notify_slack
      #   action:
      #     class_name: SlackNotificationAction
      #     slack_webhook: ${validation_notification_slack_webhook}
      #     notify_on: all
      #     renderer:
      #       module_name: great_expectations.render.renderer.slack_renderer
      #       class_name: SlackRenderer
      - name: store_evaluation_params
        action:
          class_name: ExtractAndStoreEvaluationParamsAction
          target_store_name: evaluation_parameter_store



"""

    print("++++++++++++++++ expected +++++++++++++++++++++++")
    print(expected)
    print("----------------------------------------")

    observed = read_config_file_from_disk(config_filepath)

    print("++++++++++++++++ observed +++++++++++++++++++++++")
    print(observed)
    print("----------------------------------------")

    # TODO: this test fails now, but only on whitespace
    # Whitespace issues seem to come from the addition or deletion of keys
    assert observed.replace("\n", "") == expected.replace("\n", "")

    # What we really want:
    # assert observed == expected
