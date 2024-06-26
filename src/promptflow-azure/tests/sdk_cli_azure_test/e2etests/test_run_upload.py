# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

from pathlib import Path
from typing import Callable

import pytest
from _constants import PROMPTFLOW_ROOT
from sdk_cli_azure_test.conftest import DATAS_DIR, FLOWS_DIR

from promptflow._sdk._constants import Local2CloudProperties, Local2CloudUserProperties, RunStatus
from promptflow._sdk._errors import RunNotFoundError
from promptflow._sdk._pf_client import PFClient as LocalPFClient
from promptflow._sdk.entities import Run
from promptflow.azure import PFClient

from .._azure_utils import DEFAULT_TEST_TIMEOUT, PYTEST_TIMEOUT_METHOD

EAGER_FLOWS_DIR = PROMPTFLOW_ROOT / "tests/test_configs/eager_flows"
RUNS_DIR = PROMPTFLOW_ROOT / "tests/test_configs/runs"
PROMPTY_DIR = PROMPTFLOW_ROOT / "tests/test_configs/prompty"


class Local2CloudTestHelper:
    @staticmethod
    def get_local_pf(run_name: str) -> LocalPFClient:
        """For local to cloud test cases, need a local client."""
        local_pf = LocalPFClient()

        # in replay mode, `randstr` will always return the parameter
        # this will lead to run already exists error for local run
        # so add a try delete to avoid this error
        try:
            local_pf.runs.delete(run_name)
        except RunNotFoundError:
            pass

        return local_pf

    @staticmethod
    def check_local_to_cloud_run(pf: PFClient, run: Run):
        # check if local run is uploaded
        cloud_run = pf.runs.get(run.name)
        assert cloud_run.display_name == run.display_name
        assert cloud_run.description == run.description
        assert cloud_run.tags == run.tags
        assert cloud_run.status == run.status
        assert cloud_run._start_time and cloud_run._end_time
        assert cloud_run.properties["azureml.promptflow.local_to_cloud"] == "true"
        assert cloud_run.properties["azureml.promptflow.snapshot_id"]
        return cloud_run


@pytest.mark.timeout(timeout=DEFAULT_TEST_TIMEOUT, method=PYTEST_TIMEOUT_METHOD)
@pytest.mark.e2etest
@pytest.mark.usefixtures(
    "mock_set_headers_with_user_aml_token",
    "single_worker_thread_pool",
    "vcr_recording",
)
class TestFlowRunUpload:
    @pytest.mark.skipif(condition=not pytest.is_live, reason="Bug - 3089145 Replay failed for test 'test_upload_run'")
    @pytest.mark.usefixtures(
        "mock_isinstance_for_mock_datastore", "mock_get_azure_pf_client", "mock_trace_provider_to_cloud"
    )
    def test_upload_run(
        self,
        pf: PFClient,
        randstr: Callable[[str], str],
    ):
        name = randstr("batch_run_name_for_upload")
        local_pf = Local2CloudTestHelper.get_local_pf(name)
        # submit a local batch run
        run = local_pf.run(
            flow=f"{FLOWS_DIR}/simple_hello_world",
            data=f"{DATAS_DIR}/webClassification3.jsonl",
            name=name,
            column_mapping={"name": "${data.url}"},
            display_name="sdk-cli-test-run-local-to-cloud",
            tags={"sdk-cli-test": "true"},
            description="test sdk local to cloud",
        )
        run = local_pf.runs.stream(run.name)
        assert run.status == RunStatus.COMPLETED

        # check the run is uploaded to cloud
        Local2CloudTestHelper.check_local_to_cloud_run(pf, run)

    @pytest.mark.skipif(condition=not pytest.is_live, reason="Bug - 3089145 Replay failed for test 'test_upload_run'")
    @pytest.mark.usefixtures(
        "mock_isinstance_for_mock_datastore", "mock_get_azure_pf_client", "mock_trace_provider_to_cloud"
    )
    def test_upload_flex_flow_run_with_yaml(self, pf: PFClient, randstr: Callable[[str], str]):
        name = randstr("flex_run_name_with_yaml_for_upload")
        local_pf = Local2CloudTestHelper.get_local_pf(name)
        # submit a local flex run
        run = local_pf.run(
            flow=Path(f"{EAGER_FLOWS_DIR}/simple_with_yaml"),
            data=f"{DATAS_DIR}/simple_eager_flow_data.jsonl",
            name=name,
            display_name="sdk-cli-test-run-local-to-cloud-flex-with-yaml",
            tags={"sdk-cli-test-flex": "true"},
            description="test sdk local to cloud",
        )
        assert run.status == "Completed"
        assert "error" not in run._to_dict()

        # check the run is uploaded to cloud
        Local2CloudTestHelper.check_local_to_cloud_run(pf, run)

    @pytest.mark.skipif(condition=not pytest.is_live, reason="Bug - 3089145 Replay failed for test 'test_upload_run'")
    @pytest.mark.usefixtures(
        "mock_isinstance_for_mock_datastore", "mock_get_azure_pf_client", "mock_trace_provider_to_cloud"
    )
    def test_upload_flex_flow_run_without_yaml(self, pf: PFClient, randstr: Callable[[str], str]):
        name = randstr("flex_run_name_without_yaml_for_upload")
        local_pf = Local2CloudTestHelper.get_local_pf(name)
        # submit a local flex run
        run = local_pf.run(
            flow="entry:my_flow",
            code=f"{EAGER_FLOWS_DIR}/simple_without_yaml",
            data=f"{DATAS_DIR}/simple_eager_flow_data.jsonl",
            name=name,
            display_name="sdk-cli-test-run-local-to-cloud-flex-without-yaml",
            tags={"sdk-cli-test-flex": "true"},
            description="test sdk local to cloud",
        )
        assert run.status == "Completed"
        assert "error" not in run._to_dict()

        # check the run is uploaded to cloud.
        Local2CloudTestHelper.check_local_to_cloud_run(pf, run)

    @pytest.mark.skipif(condition=not pytest.is_live, reason="Bug - 3089145 Replay failed for test 'test_upload_run'")
    @pytest.mark.usefixtures(
        "mock_isinstance_for_mock_datastore", "mock_get_azure_pf_client", "mock_trace_provider_to_cloud"
    )
    def test_upload_prompty_run(self, pf: PFClient, randstr: Callable[[str], str]):
        # currently prompty run is skipped for upload, this test should be finished without error
        name = randstr("prompty_run_name_for_upload")
        local_pf = Local2CloudTestHelper.get_local_pf(name)
        run = local_pf.run(
            flow=f"{PROMPTY_DIR}/prompty_example.prompty",
            data=f"{DATAS_DIR}/prompty_inputs.jsonl",
            name=name,
        )
        assert run.status == "Completed"
        assert "error" not in run._to_dict()

    @pytest.mark.skipif(condition=not pytest.is_live, reason="Bug - 3089145 Replay failed for test 'test_upload_run'")
    @pytest.mark.usefixtures(
        "mock_isinstance_for_mock_datastore", "mock_get_azure_pf_client", "mock_trace_provider_to_cloud"
    )
    def test_upload_run_with_customized_run_properties(self, pf: PFClient, randstr: Callable[[str], str]):
        name = randstr("batch_run_name_for_upload_with_customized_properties")
        local_pf = Local2CloudTestHelper.get_local_pf(name)

        eval_run = "promptflow.BatchRun"
        eval_artifacts = '[{"path": "instance_results.jsonl", "type": "table"}]'

        # submit a local batch run
        run = local_pf._run(
            flow=f"{FLOWS_DIR}/simple_hello_world",
            data=f"{DATAS_DIR}/webClassification3.jsonl",
            name=name,
            column_mapping={"name": "${data.url}"},
            display_name="sdk-cli-test-run-local-to-cloud-with-properties",
            tags={"sdk-cli-test": "true"},
            description="test sdk local to cloud",
            properties={
                Local2CloudUserProperties.EVAL_RUN: eval_run,
                Local2CloudUserProperties.EVAL_ARTIFACTS: eval_artifacts,
            },
        )
        run = local_pf.runs.stream(run.name)
        assert run.status == RunStatus.COMPLETED

        # check the run is uploaded to cloud, and the properties are set correctly
        cloud_run = Local2CloudTestHelper.check_local_to_cloud_run(pf, run)
        assert cloud_run.properties[Local2CloudUserProperties.EVAL_RUN] == eval_run
        assert cloud_run.properties[Local2CloudUserProperties.EVAL_ARTIFACTS] == eval_artifacts
        # check total tokens is recorded
        assert cloud_run.properties[Local2CloudProperties.TOTAL_TOKENS]
