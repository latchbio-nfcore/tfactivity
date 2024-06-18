from dataclasses import dataclass
from enum import Enum
import os
import subprocess
import requests
import shutil
from pathlib import Path
import typing
import typing_extensions

from latch.resources.workflow import workflow
from latch.resources.tasks import nextflow_runtime_task, custom_task
from latch.types.file import LatchFile
from latch.types.directory import LatchDir, LatchOutputDir
from latch.ldata.path import LPath
from latch_cli.nextflow.workflow import get_flag
from latch_cli.nextflow.utils import _get_execution_name
from latch_cli.utils import urljoins
from latch.types import metadata
from flytekit.core.annotation import FlyteAnnotation

from latch_cli.services.register.utils import import_module_by_path

meta = Path("latch_metadata") / "__init__.py"
import_module_by_path(meta)
import latch_metadata

@custom_task(cpu=0.25, memory=0.5, storage_gib=1)
def initialize() -> str:
    token = os.environ.get("FLYTE_INTERNAL_EXECUTION_ID")
    if token is None:
        raise RuntimeError("failed to get execution token")

    headers = {"Authorization": f"Latch-Execution-Token {token}"}

    print("Provisioning shared storage volume... ", end="")
    resp = requests.post(
        "http://nf-dispatcher-service.flyte.svc.cluster.local/provision-storage",
        headers=headers,
        json={
            "storage_gib": 100,
        }
    )
    resp.raise_for_status()
    print("Done.")

    return resp.json()["name"]






@nextflow_runtime_task(cpu=4, memory=8, storage_gib=100)
def nextflow_runtime(pvc_name: str, input: LatchFile, input_bam: typing.Optional[LatchFile], counts: typing.Optional[LatchFile], counts_design: typing.Optional[LatchFile], outdir: typing_extensions.Annotated[LatchDir, FlyteAnnotation({'output': True})], email: typing.Optional[str], multiqc_title: typing.Optional[str], merge_samples: typing.Optional[bool], genome: typing.Optional[str], fasta: typing.Optional[LatchFile], gtf: typing.Optional[LatchFile], blacklist: typing.Optional[LatchFile], motifs: typing.Optional[LatchFile], taxon_id: typing.Optional[int], multiqc_methods_description: typing.Optional[str], min_peak_occurrence: typing.Optional[int], window_size: typing.Optional[int], decay: typing.Optional[bool], expression_aggregation: typing.Optional[str], affinity_aggregation: typing.Optional[str], chromhmm_states: typing.Optional[int], chromhmm_threshold: typing.Optional[float], chromhmm_marks: typing.Optional[str], min_count: typing.Optional[int], min_tpm: typing.Optional[float], min_count_tf: typing.Optional[int], min_tpm_tf: typing.Optional[float], dynamite_ofolds: typing.Optional[int], dynamite_ifolds: typing.Optional[int], dynamite_alpha: typing.Optional[float], dynamite_randomize: typing.Optional[bool], dynamite_min_regression: typing.Optional[float], alpha: typing.Optional[float]) -> None:
    try:
        shared_dir = Path("/nf-workdir")



        ignore_list = [
            "latch",
            ".latch",
            "nextflow",
            ".nextflow",
            "work",
            "results",
            "miniconda",
            "anaconda3",
            "mambaforge",
        ]

        shutil.copytree(
            Path("/root"),
            shared_dir,
            ignore=lambda src, names: ignore_list,
            ignore_dangling_symlinks=True,
            dirs_exist_ok=True,
        )

        cmd = [
            "/root/nextflow",
            "run",
            str(shared_dir / "main.nf"),
            "-work-dir",
            str(shared_dir),
            "-profile",
            "docker",
            "-c",
            "latch.config",
                *get_flag('input', input),
                *get_flag('input_bam', input_bam),
                *get_flag('counts', counts),
                *get_flag('counts_design', counts_design),
                *get_flag('outdir', outdir),
                *get_flag('email', email),
                *get_flag('multiqc_title', multiqc_title),
                *get_flag('merge_samples', merge_samples),
                *get_flag('min_peak_occurrence', min_peak_occurrence),
                *get_flag('window_size', window_size),
                *get_flag('decay', decay),
                *get_flag('expression_aggregation', expression_aggregation),
                *get_flag('affinity_aggregation', affinity_aggregation),
                *get_flag('chromhmm_states', chromhmm_states),
                *get_flag('chromhmm_threshold', chromhmm_threshold),
                *get_flag('chromhmm_marks', chromhmm_marks),
                *get_flag('min_count', min_count),
                *get_flag('min_tpm', min_tpm),
                *get_flag('min_count_tf', min_count_tf),
                *get_flag('min_tpm_tf', min_tpm_tf),
                *get_flag('dynamite_ofolds', dynamite_ofolds),
                *get_flag('dynamite_ifolds', dynamite_ifolds),
                *get_flag('dynamite_alpha', dynamite_alpha),
                *get_flag('dynamite_randomize', dynamite_randomize),
                *get_flag('dynamite_min_regression', dynamite_min_regression),
                *get_flag('alpha', alpha),
                *get_flag('genome', genome),
                *get_flag('fasta', fasta),
                *get_flag('gtf', gtf),
                *get_flag('blacklist', blacklist),
                *get_flag('motifs', motifs),
                *get_flag('taxon_id', taxon_id),
                *get_flag('multiqc_methods_description', multiqc_methods_description)
        ]

        print("Launching Nextflow Runtime")
        print(' '.join(cmd))
        print(flush=True)

        env = {
            **os.environ,
            "NXF_HOME": "/root/.nextflow",
            "NXF_OPTS": "-Xms2048M -Xmx8G -XX:ActiveProcessorCount=4",
            "K8S_STORAGE_CLAIM_NAME": pvc_name,
            "NXF_DISABLE_CHECK_LATEST": "true",
        }
        subprocess.run(
            cmd,
            env=env,
            check=True,
            cwd=str(shared_dir),
        )
    finally:
        print()

        nextflow_log = shared_dir / ".nextflow.log"
        if nextflow_log.exists():
            name = _get_execution_name()
            if name is None:
                print("Skipping logs upload, failed to get execution name")
            else:
                remote = LPath(urljoins("latch:///your_log_dir/nf_nf_core_tfactivity", name, "nextflow.log"))
                print(f"Uploading .nextflow.log to {remote.path}")
                remote.upload_from(nextflow_log)



@workflow(metadata._nextflow_metadata)
def nf_nf_core_tfactivity(input: LatchFile, input_bam: typing.Optional[LatchFile], counts: typing.Optional[LatchFile], counts_design: typing.Optional[LatchFile], outdir: typing_extensions.Annotated[LatchDir, FlyteAnnotation({'output': True})], email: typing.Optional[str], multiqc_title: typing.Optional[str], merge_samples: typing.Optional[bool], genome: typing.Optional[str], fasta: typing.Optional[LatchFile], gtf: typing.Optional[LatchFile], blacklist: typing.Optional[LatchFile], motifs: typing.Optional[LatchFile], taxon_id: typing.Optional[int], multiqc_methods_description: typing.Optional[str], min_peak_occurrence: typing.Optional[int] = 1, window_size: typing.Optional[int] = 50000, decay: typing.Optional[bool] = 'true', expression_aggregation: typing.Optional[str] = 'mean', affinity_aggregation: typing.Optional[str] = 'max', chromhmm_states: typing.Optional[int] = 10, chromhmm_threshold: typing.Optional[float] = 0.9, chromhmm_marks: typing.Optional[str] = 'H3K27ac,H3K4me3', min_count: typing.Optional[int] = 50, min_tpm: typing.Optional[float] = 1, min_count_tf: typing.Optional[int] = 50, min_tpm_tf: typing.Optional[float] = 1, dynamite_ofolds: typing.Optional[int] = 3, dynamite_ifolds: typing.Optional[int] = 6, dynamite_alpha: typing.Optional[float] = 0.1, dynamite_randomize: typing.Optional[bool] = 'false', dynamite_min_regression: typing.Optional[float] = 0.1, alpha: typing.Optional[float] = 0.05) -> None:
    """
    nf-core/tfactivity

    Sample Description
    """

    pvc_name: str = initialize()
    nextflow_runtime(pvc_name=pvc_name, input=input, input_bam=input_bam, counts=counts, counts_design=counts_design, outdir=outdir, email=email, multiqc_title=multiqc_title, merge_samples=merge_samples, min_peak_occurrence=min_peak_occurrence, window_size=window_size, decay=decay, expression_aggregation=expression_aggregation, affinity_aggregation=affinity_aggregation, chromhmm_states=chromhmm_states, chromhmm_threshold=chromhmm_threshold, chromhmm_marks=chromhmm_marks, min_count=min_count, min_tpm=min_tpm, min_count_tf=min_count_tf, min_tpm_tf=min_tpm_tf, dynamite_ofolds=dynamite_ofolds, dynamite_ifolds=dynamite_ifolds, dynamite_alpha=dynamite_alpha, dynamite_randomize=dynamite_randomize, dynamite_min_regression=dynamite_min_regression, alpha=alpha, genome=genome, fasta=fasta, gtf=gtf, blacklist=blacklist, motifs=motifs, taxon_id=taxon_id, multiqc_methods_description=multiqc_methods_description)

