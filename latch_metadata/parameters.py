
from dataclasses import dataclass
import typing
import typing_extensions

from flytekit.core.annotation import FlyteAnnotation

from latch.types.metadata import NextflowParameter
from latch.types.file import LatchFile
from latch.types.directory import LatchDir, LatchOutputDir

# Import these into your `__init__.py` file:
#
# from .parameters import generated_parameters

generated_parameters = {
    'input': NextflowParameter(
        type=LatchFile,
        default=None,
        section_title='Input/output options',
        description='Path to comma-separated file containing information about the samples in the experiment.',
    ),
    'input_bam': NextflowParameter(
        type=typing.Optional[LatchFile],
        default=None,
        section_title=None,
        description='Path to comma-separated file containing information about the BAM files in the experiment.',
    ),
    'counts': NextflowParameter(
        type=typing.Optional[LatchFile],
        default=None,
        section_title=None,
        description='Path to comma-separated file containing the counts for the samples in the experiment. Can also be a file containing just gene identifiers. In this case, count values need to be referenced in the counts_design file.',
    ),
    'counts_design': NextflowParameter(
        type=typing.Optional[LatchFile],
        default=None,
        section_title=None,
        description='Path to comma-separated file containing information about the counts file.',
    ),
    'outdir': NextflowParameter(
        type=typing_extensions.Annotated[LatchDir, FlyteAnnotation({'output': True})],
        default=None,
        section_title=None,
        description='The output directory where the results will be saved. You have to use absolute paths to storage on Cloud infrastructure.',
    ),
    'email': NextflowParameter(
        type=typing.Optional[str],
        default=None,
        section_title=None,
        description='Email address for completion summary.',
    ),
    'multiqc_title': NextflowParameter(
        type=typing.Optional[str],
        default=None,
        section_title=None,
        description='MultiQC report title. Printed as page header, used for filename if not otherwise specified.',
    ),
    'merge_samples': NextflowParameter(
        type=typing.Optional[bool],
        default=None,
        section_title='Pipeline options',
        description='Merge samples with the same condition and assay.',
    ),
    'min_peak_occurrence': NextflowParameter(
        type=typing.Optional[int],
        default=1,
        section_title=None,
        description='Minimum number of samples that a peak has to occur in to keep it while merging.',
    ),
    'window_size': NextflowParameter(
        type=typing.Optional[int],
        default=50000,
        section_title=None,
        description='Size of the window to search for binding sites.',
    ),
    'decay': NextflowParameter(
        type=typing.Optional[bool],
        default='true',
        section_title=None,
        description='Use decay in STARE',
    ),
    'expression_aggregation': NextflowParameter(
        type=typing.Optional[str],
        default='mean',
        section_title=None,
        description='Method to aggregate expression values.',
    ),
    'affinity_aggregation': NextflowParameter(
        type=typing.Optional[str],
        default='max',
        section_title=None,
        description='Method to aggregate affinity values.',
    ),
    'chromhmm_states': NextflowParameter(
        type=typing.Optional[int],
        default=10,
        section_title=None,
        description='Number of ChromHMM states.',
    ),
    'chromhmm_threshold': NextflowParameter(
        type=typing.Optional[float],
        default=0.9,
        section_title=None,
        description='Threshold for ChromHMM enhancer detection.',
    ),
    'chromhmm_marks': NextflowParameter(
        type=typing.Optional[str],
        default='H3K27ac,H3K4me3',
        section_title=None,
        description='Comma-separated ChromHMM enhancer marks.',
    ),
    'min_count': NextflowParameter(
        type=typing.Optional[int],
        default=50,
        section_title=None,
        description='Minimum number of total counts to keep a gene in the analysis.',
    ),
    'min_tpm': NextflowParameter(
        type=typing.Optional[float],
        default=1,
        section_title=None,
        description='Minimum TPM to keep a gene in the analysis.',
    ),
    'min_count_tf': NextflowParameter(
        type=typing.Optional[int],
        default=50,
        section_title=None,
        description='Minimum number of total counts to keep a transcription factor in the analysis.',
    ),
    'min_tpm_tf': NextflowParameter(
        type=typing.Optional[float],
        default=1,
        section_title=None,
        description='Minimum TPM to keep a transcription factor in the analysis.',
    ),
    'dynamite_ofolds': NextflowParameter(
        type=typing.Optional[int],
        default=3,
        section_title=None,
        description='Number of outer folds for dynamite.',
    ),
    'dynamite_ifolds': NextflowParameter(
        type=typing.Optional[int],
        default=6,
        section_title=None,
        description='Number of inner folds for dynamite.',
    ),
    'dynamite_alpha': NextflowParameter(
        type=typing.Optional[float],
        default=0.1,
        section_title=None,
        description='Alpha value for dynamite.',
    ),
    'dynamite_randomize': NextflowParameter(
        type=typing.Optional[bool],
        default='false',
        section_title=None,
        description='Randomize the data for dynamite.',
    ),
    'dynamite_min_regression': NextflowParameter(
        type=typing.Optional[float],
        default=0.1,
        section_title=None,
        description='Minimum regression value for dynamite.',
    ),
    'alpha': NextflowParameter(
        type=typing.Optional[float],
        default=0.05,
        section_title=None,
        description='Alpha value for the Mann-Whitney U test.',
    ),
    'genome': NextflowParameter(
        type=typing.Optional[str],
        default=None,
        section_title='Reference genome options',
        description='Name of iGenomes reference.',
    ),
    'fasta': NextflowParameter(
        type=typing.Optional[LatchFile],
        default=None,
        section_title=None,
        description='Path to FASTA genome file.',
    ),
    'gtf': NextflowParameter(
        type=typing.Optional[LatchFile],
        default=None,
        section_title=None,
        description='Path to GTF gene annotation file.',
    ),
    'blacklist': NextflowParameter(
        type=typing.Optional[LatchFile],
        default=None,
        section_title=None,
        description='Path to blacklist regions file.',
    ),
    'motifs': NextflowParameter(
        type=typing.Optional[LatchFile],
        default=None,
        section_title=None,
        description='Path to transcription factor motifs file.',
    ),
    'taxon_id': NextflowParameter(
        type=typing.Optional[int],
        default=None,
        section_title=None,
        description='NCBI Taxonomy ID.',
    ),
    'multiqc_methods_description': NextflowParameter(
        type=typing.Optional[str],
        default=None,
        section_title='Generic options',
        description='Custom MultiQC yaml file containing HTML including a methods description.',
    ),
}

