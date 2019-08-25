from ..types import (
    DataAssetIdentifier,
    ValidationResultIdentifier,
)
from ..types.resource_identifiers import (
    DataContextResourceIdentifier,
)
from .types import (
    InMemoryStoreConfig,
    FilesystemStoreConfig,
    NamespacedFilesystemStoreConfig,
)
from ..util import safe_mmkdir
import pandas as pd
import six
import io
import os
import json
import logging
logger = logging.getLogger(__name__)
import importlib
import re
from six import string_types

from ..util import (
    parse_string_to_data_context_resource_identifier
)
from .store import (
    Store
)


class InMemoryStore(Store):
    """Uses an in-memory dictionary as a store.
    """

    config_class = InMemoryStoreConfig

    def _setup(self):
        self.store = {}

    def _get(self, key):
        return self.store[key]

    def _set(self, key, value):
        self.store[key] = value

    def _validate_key(self, key):
        if not isinstance(key, string_types):
            raise TypeError("Keys in {0} must be instances of {1}, not {2}".format(
                self.__class__.__name__,
                string_types,
                type(key),
            ))

    def list_keys(self):
        return list(self.store.keys())

    def has_key(self, key):
        return key in self.store


class FilesystemStore(Store):
    """Uses a local filepath as a store.

    # FIXME : It's currently possible to break this Store by passing it a ResourceIdentifier that contains '/'.
    """

    config_class = FilesystemStoreConfig

    def __init__(
        self,
        config,
        root_directory, #This argument is REQUIRED for this class
    ):
        super(FilesystemStore, self).__init__(config, root_directory)

    def _setup(self):
        self.full_base_directory = os.path.join(
            self.root_directory,
            self.config.base_directory,
        )

        safe_mmkdir(str(os.path.dirname(self.full_base_directory)))

    def _get(self, key):
        filepath = self._get_filepath_from_key(key)
        with open(filepath) as infile:
            return infile.read()

    def _set(self, key, value):
        filepath = self._get_filepath_from_key(key)
        path, filename = os.path.split(filepath)

        safe_mmkdir(str(path))
        with open(filepath, "w") as outfile:
            outfile.write(value)

    def _validate_key(self, key):
        if not isinstance(key, string_types):
            raise TypeError("Keys in {0} must be instances of {1}, not {2}".format(
                self.__class__.__name__,
                string_types,
                type(key),
            ))

    def list_keys(self):
        # TODO : Rename "keys" in this method to filepaths, for clarity
        key_list = []
        for root, dirs, files in os.walk(self.full_base_directory):
            for file_ in files:
                full_path, file_name = os.path.split(os.path.join(root, file_))
                relative_path = os.path.relpath(
                    full_path,
                    self.full_base_directory,
                )
                if relative_path == ".":
                    key = file_name
                else:
                    key = os.path.join(
                        relative_path,
                        file_name
                    )

                key_list.append(
                    self._get_key_from_filepath(key)
                )

        return key_list

    # TODO : Write tests for this method
    def has_key(self, key):
        assert isinstance(key, string_types)

        all_keys = self.list_keys()
        return key in all_keys

    def _get_filepath_from_key(self, key):
        # NOTE : This method is trivial in this class, but child classes can get pretty complex
        file_extension = self.config.get("file_extension", "")
        return os.path.join(self.full_base_directory, key)+file_extension
    
    def _get_key_from_filepath(self, filepath):
        # NOTE : This method is trivial in this class, but child classes can get pretty complex
        file_extension_length = len(self.config.file_extension)
        filepath_without_extension = filepath[:-1*file_extension_length]
        return filepath_without_extension


# class S3Store(ContextAwareStore):
#     """Uses an S3 bucket+prefix as a store
#     """

#     def _get(self, key):
#         raise NotImplementedError

#     def _set(self, key, value):
#         raise NotImplementedError

# This code is from an earlier (untested) implementation of DataContext.register_validation_results
# Storing it here in case it can be salvaged
# if isinstance(data_asset_snapshot_store, dict) and "s3" in data_asset_snapshot_store:
#     bucket = data_asset_snapshot_store["s3"]["bucket"]
#     key_prefix = data_asset_snapshot_store["s3"]["key_prefix"]
#     key = os.path.join(
#         key_prefix,
#         "validations/{run_id}/{data_asset_name}.csv.gz".format(
#             run_id=run_id,
#             data_asset_name=self._get_normalized_data_asset_name_filepath(
#                 normalized_data_asset_name,
#                 expectation_suite_name,
#                 base_path="",
#                 file_extension=".csv.gz"
#             )
#         )
#     )
#     validation_results["meta"]["data_asset_snapshot"] = "s3://{bucket}/{key}".format(
#         bucket=bucket,
#         key=key)
#
#     try:
#         import boto3
#         s3 = boto3.resource('s3')
#         result_s3 = s3.Object(bucket, key)
#         result_s3.put(Body=data_asset.to_csv(compression="gzip").encode('utf-8'))
#     except ImportError:
#         logger.error("Error importing boto3 for AWS support. Unable to save to result store.")
#     except Exception:
#         raise
