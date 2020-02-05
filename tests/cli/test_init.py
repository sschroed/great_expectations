import os
import shutil

import pytest
from click.testing import CliRunner
from six import PY2

from great_expectations import DataContext
from great_expectations.cli import cli
from great_expectations.data_context.templates import CONFIG_VARIABLES_TEMPLATE
from great_expectations.data_context.util import file_relative_path
from great_expectations.util import gen_directory_tree_str
from tests.cli.test_cli import yaml
from tests.cli.utils import assert_no_logging_messages_or_tracebacks


@pytest.mark.xfail(condition=PY2, reason="legacy python")
def test_cli_init_on_existing_project_with_no_uncommitted_dirs_answering_yes_to_fixing_them(
    caplog, tmp_path_factory,
):
    """
    This test walks through the onboarding experience.

    The user just checked an existing project out of source control and does
    not yet have an uncommitted directory.
    """
    root_dir = tmp_path_factory.mktemp("hiya")
    root_dir = str(root_dir)
    os.makedirs(os.path.join(root_dir, "data"))
    data_path = os.path.join(root_dir, "data/Titanic.csv")
    fixture_path = file_relative_path(__file__, "../test_sets/Titanic.csv")
    shutil.copy(fixture_path, data_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["init", "--no-view", "-d", root_dir],
        input="Y\n1\n1\n{}\n\n\n\n".format(data_path),
    )
    stdout = result.output
    assert result.exit_code == 0
    assert "Great Expectations is now set up." in stdout

    context = DataContext(os.path.join(root_dir, DataContext.GE_DIR))
    uncommitted_dir = os.path.join(context.root_directory, "uncommitted")
    shutil.rmtree(uncommitted_dir)
    assert not os.path.isdir(uncommitted_dir)

    # Test the second invocation of init
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "-d", root_dir], input="Y\nn\n")
    stdout = result.stdout

    assert result.exit_code == 0
    assert "To run locally, we need some files that are not in source control" in stdout
    assert "Done. You may see new files in" in stdout
    assert "OK. You must run" not in stdout
    assert "great_expectations init" not in stdout
    assert "to fix the missing files!" not in stdout
    assert "Would you like to build & view this project's Data Docs!?" in stdout

    assert os.path.isdir(uncommitted_dir)
    config_var_path = os.path.join(uncommitted_dir, "config_variables.yml")
    assert os.path.isfile(config_var_path)
    with open(config_var_path, "r") as f:
        assert f.read() == CONFIG_VARIABLES_TEMPLATE

    assert_no_logging_messages_or_tracebacks(caplog, result)


@pytest.mark.xfail(condition=PY2, reason="legacy python")
def test_cli_init_on_existing_project_with_no_uncommitted_dirs_answering_no_to_fixing_them(
    caplog, tmp_path_factory,
):
    """
    This test walks through the onboarding experience.

    The user just checked an existing project out of source control and does
    not yet have an uncommitted directory, runs init and answers No to fixing.

    Therefore the disk should not be changed.
    """
    root_dir = tmp_path_factory.mktemp("hiya")
    root_dir = str(root_dir)
    os.makedirs(os.path.join(root_dir, "data"))
    data_path = os.path.join(root_dir, "data/Titanic.csv")
    fixture_path = file_relative_path(__file__, "../test_sets/Titanic.csv")
    shutil.copy(fixture_path, data_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["init", "--no-view", "-d", root_dir],
        input="Y\n1\n1\n{}\n\n\n\n".format(data_path),
    )
    stdout = result.output
    assert result.exit_code == 0
    assert "Great Expectations is now set up." in stdout

    context = DataContext(os.path.join(root_dir, DataContext.GE_DIR))
    uncommitted_dir = os.path.join(context.root_directory, "uncommitted")
    shutil.rmtree(uncommitted_dir)
    assert not os.path.isdir(uncommitted_dir)

    # Test the second invocation of init
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "-d", root_dir], input="n\nn\n")
    stdout = result.stdout

    assert result.exit_code == 0
    assert "To run locally, we need some files that are not in source control" in stdout
    assert "OK. You must run" in stdout
    assert "great_expectations init" in stdout
    assert "to fix the missing files!" in stdout

    # DataContext should not write to disk unless you explicitly tell it to
    assert not os.path.isdir(uncommitted_dir)
    assert not os.path.isfile(os.path.join(uncommitted_dir, "config_variables.yml"))


def test_cli_init_on_complete_existing_project_all_uncommitted_dirs_exist(
    caplog, tmp_path_factory,
):
    """
    This test walks through the onboarding experience.

    The user just checked an existing project out of source control and does
    not yet have an uncommitted directory.
    """
    root_dir = tmp_path_factory.mktemp("hiya")
    root_dir = str(root_dir)
    os.makedirs(os.path.join(root_dir, "data"))
    data_path = os.path.join(root_dir, "data/Titanic.csv")
    fixture_path = file_relative_path(__file__, "../test_sets/Titanic.csv")
    shutil.copy(fixture_path, data_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["init", "--no-view", "-d", root_dir],
        input="Y\n1\n1\n{}\n\n\n\n".format(data_path),
    )
    stdout = result.output
    assert result.exit_code == 0

    # Test the second invocation of init
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--no-view", "-d", root_dir], input="n\n")
    print(stdout)
    stdout = result.stdout

    assert result.exit_code == 0
    assert "This looks like an existing project that" in stdout
    assert "appears complete" in stdout
    assert "ready to roll" in stdout
    assert "Would you like to build & view this project's Data Docs" in stdout
    assert_no_logging_messages_or_tracebacks(caplog, result)


def test_cli_init_connection_string_non_working_postgres_connection_instructs_user_and_leaves_entries_in_config_files_for_debugging(
    caplog, tmp_path_factory,
):
    basedir = tmp_path_factory.mktemp("mssql_test")
    basedir = str(basedir)
    os.chdir(basedir)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["init", "--no-view"],
        input="Y\n2\n5\nmy_db\npostgresql+psycopg2://scott:tiger@not_a_real_host:1234/dbname\nn\n",
    )
    stdout = result.output

    assert "Always know what to expect from your data" in stdout
    assert "What data would you like Great Expectations to connect to" in stdout
    assert "Which database backend are you using" in stdout
    assert "What is the url/connection string for the sqlalchemy connection" in stdout
    assert "Give your new data source a short name" in stdout
    assert "Attempting to connect to your database. This may take a moment" in stdout
    assert "Cannot connect to the database" in stdout

    assert "Profiling" not in stdout
    assert "Building" not in stdout
    assert "Data Docs" not in stdout
    assert "Great Expectations is now set up" not in stdout

    assert result.exit_code == 1

    ge_dir = os.path.join(basedir, DataContext.GE_DIR)
    assert os.path.isdir(ge_dir)
    config_path = os.path.join(ge_dir, DataContext.GE_YML)
    assert os.path.isfile(config_path)

    # TODO this entry might not be totally right, but one needs to be here.
    config = yaml.load(open(config_path, "r"))
    assert config["datasources"] == {
        "my_db": {
            "data_asset_type": {
                "module_name": None,
                "class_name": "SqlAlchemyDataset",
            },
            "credentials": "${my_db}",
            "class_name": "SqlAlchemyDatasource",
            "module_name": "great_expectations.datasource"
        }
    }

    # TODO add entry in config_vars this entry might not be totally right, but one needs to be here.
    config_path = os.path.join(
        ge_dir, DataContext.GE_UNCOMMITTED_DIR, "config_variables.yml"
    )
    config = yaml.load(open(config_path, "r"))
    assert config["my_db"] == {
        "url": "postgresql+psycopg2://scott:tiger@not_a_real_host:1234/dbname"
    }

    obs_tree = gen_directory_tree_str(os.path.join(basedir, "great_expectations"))
    assert (
        obs_tree
        == """\
great_expectations/
    .gitignore
    great_expectations.yml
    expectations/
    notebooks/
        pandas/
            validation_playground.ipynb
        spark/
            validation_playground.ipynb
        sql/
            validation_playground.ipynb
    plugins/
        custom_data_docs/
            renderers/
            styles/
                data_docs_custom_styles.css
            views/
    uncommitted/
        config_variables.yml
        data_docs/
        samples/
        validations/
"""
    )

    assert_no_logging_messages_or_tracebacks(caplog, result)
