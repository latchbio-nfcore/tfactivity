#!/usr/bin/env python3

import os
from optparse import OptionParser


def region_stitching(input_gff, stitch_window, tss_window, annot_file, remove_tss=True):
    print('Performing region stitching...')
    # first have to turn bound region file into a locus collection

    # need to make sure this names correctly... each region should have a unique name
    bound_collection = gff_to_locus_collection(input_gff)

    # filter out all bound regions that overlap the TSS of an ACTIVE GENE
    if remove_tss:
        # first make a locus collection of TSS
        start_dict = make_start_dict(annot_file)

        # now makeTSS loci for active genes
        remove_ticker = 0
        # this loop makes a locus centered around +/- tss_window of transcribed genes
        # then adds it to the list tss_loci
        tss_loci = []
        for gene_id in list(start_dict.keys()):
            tss_loci.append(make_tss_locus(gene_id, start_dict, tss_window, tss_window))

        # this turns the tss_loci list into a LocusCollection
        # 50 is the internal parameter for LocusCollection and doesn't really matter
        tss_collection = LocusCollection(tss_loci, 50)

        # gives all the loci in bound_collection
        bound_loci = bound_collection.get_loci()

        # this loop will check if each bound region is contained by the TSS exclusion zone
        # this will drop out a lot of the promoter only regions that are tiny
        # typical exclusion window is around 2kb
        for locus in bound_loci:
            if len(tss_collection.get_containers(locus, 'both')) > 0:
                # if true, the bound locus overlaps an active gene
                bound_collection.remove(locus)
                remove_ticker += 1
        print(f'Removed {remove_ticker} loci because they were contained by a TSS')

    # bound_collection is now all enriched region loci that don't overlap an active TSS
    stitched_collection = bound_collection.stitch_collection(stitch_window, 'both')

    if remove_tss:
        # now replace any stitched region that overlap 2 distinct genes
        # with the original loci that were there
        fixed_loci = []
        tss_loci = []
        for gene_id in list(start_dict.keys()):
            tss_loci.append(make_tss_locus(gene_id, start_dict, 50, 50))

        # this turns the tss_loci list into a LocusCollection
        # 50 is the internal parameter for LocusCollection and doesn't really matter
        tss_collection = LocusCollection(tss_loci, 50)
        remove_ticker = 0
        original_ticker = 0
        for stitched_locus in stitched_collection.get_loci():
            overlapping_tss_loci = tss_collection.get_overlap(stitched_locus, 'both')
            tss_names = [start_dict[tssLocus.id()]['name'] for tssLocus in overlapping_tss_loci]
            tss_names = uniquify(tss_names)
            if len(tss_names) > 2:
                original_loci = bound_collection.get_overlap(stitched_locus, 'both')
                original_ticker += len(original_loci)
                fixed_loci += original_loci
                remove_ticker += 1
            else:
                fixed_loci.append(stitched_locus)

        print(f'Removed {remove_ticker} stitched loci because they overlapped multiple TSSs')
        print(f'Added back {original_ticker} original loci')
        fixed_collection = LocusCollection(fixed_loci, 50)
        return fixed_collection
    else:
        return stitched_collection


# ==================================================================
# ==========================I/O FUNCTIONS===========================
# ==================================================================

# unparse_table 4/14/08
# takes in a table generated by parse_table and writes it to an output file
# takes as parameters (table, output, sep), where sep is how the file is delimited
# example call unparse_table(table, 'table.txt', '\t') for a tab del file

def unparse_table(table, output, sep):
    fh_out = open(output, 'w')
    if len(sep) == 0:
        for i in table:
            fh_out.write(str(i))
            fh_out.write('\n')
    else:
        for line in table:
            line = [str(x) for x in line]
            line = sep.join(line)

            fh_out.write(line)
            fh_out.write('\n')

    fh_out.close()


# parse_table 4/14/08
# takes in a table where columns are separated by a given symbol and outputs
# a nested list such that list[row][col]
# example call:
# table = parse_table('file.txt','\t')
def parse_table(fn, sep, header=False, excel=False):
    fh = open(fn)
    lines = fh.readlines()
    fh.close()
    if excel:
        lines = lines[0].split('\r')
    if lines[0].count('\r') > 0:
        lines = lines[0].split('\r')
    table = []
    if header:
        lines = lines[1:]
    for i in lines:
        table.append(i[:-1].split(sep))

    return table


def format_folder(folder_name, create=False):
    """
    makes sure a folder exists and if not makes it
    returns a bool for folder
    """

    if folder_name[-1] != '/':
        folder_name += '/'

    try:
        foo = os.listdir(folder_name)
        return folder_name
    except OSError:
        print(f'folder {folder_name} does not exist')
        if create:
            os.system(f'mkdir {folder_name}')
            return folder_name
        else:

            return False

        # ==================================================================


# ===================ANNOTATION FUNCTIONS===========================
# ==================================================================


def make_start_dict(annot_file, gene_list=[]):
    """
    makes a dictionary keyed by refseq ID that contains information about
    chrom/start/stop/strand/common name
    """

    if type(gene_list) == str:
        gene_list = parse_table(gene_list, '\t')
        gene_list = [line[0] for line in gene_list]

    if annot_file.upper().count('REFSEQ') == 1:
        refseq_table, refseq_dict = import_refseq(annot_file)
        if len(gene_list) == 0:
            gene_list = list(refseq_dict.keys())
        start_dict = {}
        for gene in gene_list:
            if gene not in refseq_dict:
                continue
            start_dict[gene] = {}
            start_dict[gene]['sense'] = refseq_table[refseq_dict[gene][0]][3]
            start_dict[gene]['chr'] = refseq_table[refseq_dict[gene][0]][2]
            start_dict[gene]['start'] = get_tsss([gene], refseq_table, refseq_dict)
            if start_dict[gene]['sense'] == '+':
                start_dict[gene]['end'] = [int(refseq_table[refseq_dict[gene][0]][5])]
            else:
                start_dict[gene]['end'] = [int(refseq_table[refseq_dict[gene][0]][4])]
            start_dict[gene]['name'] = refseq_table[refseq_dict[gene][0]][12]
    return start_dict


# generic function to get the TSS of any gene
def get_tsss(gene_list, refseq_table, refseq_dict):
    if len(gene_list) == 0:
        refseq = refseq_table
    else:
        refseq = refseq_from_key(gene_list, refseq_dict, refseq_table)
    tss = []
    for line in refseq:
        if line[3] == '+':
            tss.append(line[4])
        if line[3] == '-':
            tss.append(line[5])
    tss = list(map(int, tss))

    return tss


# 12/29/08
# refseq_from_key(refseqKeyList,refseq_dict,refseq_table)
# function that grabs refseq lines from refseq IDs
def refseq_from_key(refseq_key_list, refseq_dict, refseq_table):
    type_refseq = []
    for name in refseq_key_list:
        if name in refseq_dict:
            type_refseq.append(refseq_table[refseq_dict[name][0]])
    return type_refseq


# 10/13/08
# import_refseq
# takes in a refseq table and makes a refseq table and a refseq dictionary for keying the table

def import_refseq(refseq_file, return_multiples=False):
    """
    opens up a refseq file downloaded by UCSC
    """
    refseq_table = parse_table(refseq_file, '\t')
    refseq_dict = {}
    ticker = 1
    for line in refseq_table[1:]:
        if line[1] in refseq_dict:
            refseq_dict[line[1]].append(ticker)
        else:
            refseq_dict[line[1]] = [ticker]
        ticker = ticker + 1

    multiples = []
    for i in refseq_dict:
        if len(refseq_dict[i]) > 1:
            multiples.append(i)

    if return_multiples:
        return refseq_table, refseq_dict, multiples
    else:
        return refseq_table, refseq_dict


# ==================================================================
# ========================LOCUS INSTANCE============================
# ==================================================================

# Locus and LocusCollection instances courtesy of Graham Ruby


class Locus:
    # this may save some space by reducing the number of chromosome strings
    # that are associated with Locus instances (see __init__).
    __chrDict = dict()
    __senseDict = {'+': '+', '-': '-', '.': '.'}

    # chr = chromosome name (string)
    # sense = '+' or '-' (or '.' for an ambidextrous locus)
    # start,end = ints of the start and end coords of the locus
    #      end coord is the coord of the last nucleotide.
    def __init__(self, chr, start, end, sense, id=''):
        coords = [int(start), int(end)]
        coords.sort()
        # this method for assigning chromosome should help avoid storage of
        # redundant strings.
        if chr not in self.__chrDict:
            self.__chrDict[chr] = chr
        self._chr = self.__chrDict[chr]
        self._sense = self.__senseDict[sense]
        self._start = int(coords[0])
        self._end = int(coords[1])
        self._id = id

    def id(self):
        return self._id

    def chr(self):
        return self._chr

    def start(self):
        return self._start  # returns the smallest coordinate

    def end(self):
        return self._end  # returns the biggest coordinate

    def len(self):
        return self._end - self._start + 1

    def get_antisense_locus(self):
        if self._sense == '.':
            return self
        else:
            switch = {'+': '-', '-': '+'}
            return Locus(self._chr, self._start, self._end, switch[self._sense])

    def coords(self):
        return [self._start, self._end]  # returns a sorted list of the coordinates

    def sense(self):
        return self._sense

    # returns boolean; True if two loci share any coordinates in common
    def overlaps(self, other_locus):
        if self.chr() != other_locus.chr():
            return False
        elif not (self._sense == '.' or other_locus.sense() == '.' or self.sense() == other_locus.sense()):
            return False
        elif self.start() > other_locus.end() or other_locus.start() > self.end():
            return False
        else:
            return True

    # returns boolean; True if all the nucleotides of the given locus overlap
    #      with the self locus
    def contains(self, other_locus):
        if self.chr() != other_locus.chr():
            return False
        elif not (self._sense == '.' or other_locus.sense() == '.' or self.sense() == other_locus.sense()):
            return False
        elif self.start() > other_locus.start() or other_locus.end() > self.end():
            return False
        else:
            return True

    # same as overlaps, but considers the opposite strand
    def overlaps_antisense(self, other_locus):
        return self.get_antisense_locus().overlaps(other_locus)

    # same as contains, but considers the opposite strand
    def contains_antisense(self, other_locus):
        return self.get_antisense_locus().contains(other_locus)

    def __hash__(self):
        return self._start + self._end

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        if self.chr() != other.chr():
            return False
        if self.start() != other.start():
            return False
        if self.end() != other.end():
            return False
        if self.sense() != other.sense():
            return False
        return True

    def __ne__(self, other):
        return not (self.__eq__(other))

    def __str__(self):
        return self.chr() + '(' + self.sense() + '):' + '-'.join(map(str, self.coords()))

    def check_rep(self):
        pass


class LocusCollection:
    def __init__(self, loci, window_size):
        self.__chr_to_coord_to_loci = dict()
        self.__loci = dict()
        self.__win_size = window_size
        for lcs in loci:
            self.__add_locus(lcs)

    def __add_locus(self, lcs):
        if lcs not in self.__loci:
            self.__loci[lcs] = None
            if lcs.sense() == '.':
                chr_key_list = [lcs.chr() + '+', lcs.chr() + '-']
            else:
                chr_key_list = [lcs.chr() + lcs.sense()]
            for chr_key in chr_key_list:
                if chr_key not in self.__chr_to_coord_to_loci:
                    self.__chr_to_coord_to_loci[chr_key] = dict()
                for n in self.__get_key_range(lcs):
                    if n not in self.__chr_to_coord_to_loci[chr_key]:
                        self.__chr_to_coord_to_loci[chr_key][n] = []
                    self.__chr_to_coord_to_loci[chr_key][n].append(lcs)

    def __get_key_range(self, locus):
        start = locus.start() // self.__win_size
        # add 1 because of the range
        end = locus.end() // self.__win_size + 1
        return range(start, end)

    def __len__(self):
        return len(self.__loci)

    def append(self, new):
        self.__add_locus(new)

    def extend(self, new_list):
        for lcs in new_list:
            self.__add_locus(lcs)

    def has_locus(self, locus):
        return locus in self.__loci

    def remove(self, old):
        if old not in self.__loci:
            raise ValueError("requested locus isn't in collection")
        del self.__loci[old]
        if old.sense() == '.':
            sense_list = ['+', '-']
        else:
            sense_list = [old.sense()]
        for k in self.__get_key_range(old):
            for sense in sense_list:
                self.__chr_to_coord_to_loci[old.chr() + sense][k].remove(old)

    def get_window_size(self):
        return self.__win_size

    def get_loci(self):
        return list(self.__loci.keys())

    def get_chr_list(self):
        # i need to remove the strand info from the chromosome keys and make
        # them non-redundant.
        temp_keys = dict()
        for k in list(self.__chr_to_coord_to_loci.keys()):
            temp_keys[k[:-1]] = None
        return list(temp_keys.keys())

    def __subset_helper(self, locus, sense):
        sense = sense.lower()
        if ['sense', 'antisense', 'both'].count(sense) != 1:
            raise ValueError("sense command invalid: '" + sense + "'.")
        matches = dict()
        senses = ['+', '-']
        if locus.sense() == '.' or sense == 'both':
            lamb = lambda s: True
        elif sense == 'sense':
            lamb = lambda s: s == locus.sense()
        elif sense == 'antisense':
            lamb = lambda s: s != locus.sense()
        else:
            raise ValueError("sense value was inappropriate: '" + sense + "'.")
        for s in filter(lamb, senses):
            chr_key = locus.chr() + s
            if chr_key in self.__chr_to_coord_to_loci:
                for n in self.__get_key_range(locus):
                    if n in self.__chr_to_coord_to_loci[chr_key]:
                        for lcs in self.__chr_to_coord_to_loci[chr_key][n]:
                            matches[lcs] = None
        return list(matches.keys())

    # sense can be 'sense' (default), 'antisense', or 'both'
    # returns all members of the collection that overlap the locus
    def get_overlap(self, locus, sense='sense'):
        matches = self.__subset_helper(locus, sense)
        # now, get rid of the ones that don't really overlap
        real_matches = dict()
        if sense == 'sense' or sense == 'both':
            for i in [lcs for lcs in matches if lcs.overlaps(locus)]:
                real_matches[i] = None
        if sense == 'antisense' or sense == 'both':
            for i in [lcs for lcs in matches if lcs.overlaps_antisense(locus)]:
                real_matches[i] = None
        return list(real_matches.keys())

    # sense can be 'sense' (default), 'antisense', or 'both'
    # returns all members of the collection that are contained by the locus
    def get_contained(self, locus, sense='sense'):
        matches = self.__subset_helper(locus, sense)
        # now, get rid of the ones that don't really overlap
        real_matches = dict()
        if sense == 'sense' or sense == 'both':
            for i in [lcs for lcs in matches if locus.contains(lcs)]:
                real_matches[i] = None
        if sense == 'antisense' or sense == 'both':
            for i in [lcs for lcs in matches if locus.contains_antisense(lcs)]:
                real_matches[i] = None
        return list(real_matches.keys())

    # sense can be 'sense' (default), 'antisense', or 'both'
    # returns all members of the collection that contain the locus
    def get_containers(self, locus, sense='sense'):
        matches = self.__subset_helper(locus, sense)
        # now, get rid of the ones that don't really overlap
        real_matches = dict()
        if sense == 'sense' or sense == 'both':
            for i in [lcs for lcs in matches if lcs.contains(locus)]:
                real_matches[i] = None
        if sense == 'antisense' or sense == 'both':
            for i in [lcs for lcs in matches if lcs.contains_antisense(locus)]:
                real_matches[i] = None
        return list(real_matches.keys())

    def stitch_collection(self, stitch_window=1, sense='both'):

        """
        reduces the collection by stitching together overlapping loci
        returns a new collection
        """

        # initializing stitch_window to 1
        # this helps collect directly adjacent loci

        locus_list = self.get_loci()
        old_collection = LocusCollection(locus_list, 500)

        stitched_collection = LocusCollection([], 500)

        for locus in locus_list:
            if old_collection.has_locus(locus):
                old_collection.remove(locus)
                overlapping_loci = old_collection.get_overlap(
                    Locus(locus.chr(), locus.start() - stitch_window, locus.end() + stitch_window, locus.sense(),
                          locus.id()), sense)

                stitch_ticker = 1
                while len(overlapping_loci) > 0:
                    stitch_ticker += len(overlapping_loci)
                    overlap_coords = locus.coords()

                    for overlapping_locus in overlapping_loci:
                        overlap_coords += overlapping_locus.coords()
                        old_collection.remove(overlapping_locus)
                    if sense == 'both':
                        locus = Locus(locus.chr(), min(overlap_coords), max(overlap_coords), '.', locus.id())
                    else:
                        locus = Locus(locus.chr(), min(overlap_coords), max(overlap_coords), locus.sense(), locus.id())
                    overlapping_loci = old_collection.get_overlap(
                        Locus(locus.chr(), locus.start() - stitch_window, locus.end() + stitch_window, locus.sense()),
                        sense)
                locus._id = f'{stitch_ticker}_{locus.id()}_lociStitched'

                stitched_collection.append(locus)

            else:
                continue
        return stitched_collection


# ==================================================================
# ========================LOCUS FUNCTIONS===========================
# ==================================================================
# 06/11/09
# turns a locusCollection into a gff
# does not write to disk though
def locus_collection_to_gff(locus_collection):
    loci_list = locus_collection.get_loci()
    gff = []
    for locus in loci_list:
        new_line = [locus.chr(), locus.id(), '', locus.coords()[0], locus.coords()[1], '', locus.sense(), '',
                    locus.id()]
        gff.append(new_line)
    return gff


def gff_to_locus_collection(gff, window=500):
    """
    opens up a gff file and turns it into a LocusCollection instance
    """

    loci_list = []
    if type(gff) == str:
        gff = parse_table(gff, '\t')

    for line in gff:
        # USE line[2] as the locus id.  If that is empty use line[8]
        if len(line[2]) > 0:
            name = line[2]
        elif len(line[8]) > 0:
            name = line[8]
        else:
            name = f'{line[0]}:{line[6]}:{line[3]}-{line[4]}'

        loci_list.append(Locus(line[0], line[3], line[4], line[6], name))
    return LocusCollection(loci_list, window)


def make_tss_locus(gene, start_dict, upstream, downstream):
    """
    given a start_dict, make a locus for any gene's TSS w/ upstream and downstream windows
    """

    start = start_dict[gene]['start'][0]
    if start_dict[gene]['sense'] == '-':
        return Locus(start_dict[gene]['chr'], start - downstream, start + upstream, '-', gene)
    else:
        return Locus(start_dict[gene]['chr'], start - upstream, start + downstream, '+', gene)


# ==================================================================
# ========================MISC FUNCTIONS============================
# ==================================================================


# uniquify function
# by Peter Bengtsson
# Used under a creative commons license
# sourced from  here: http://www.peterbe.com/plog/uniqifiers-benchmark

def uniquify(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result




def main():
    parser = OptionParser(usage="usage: %prog [options] -g [GENOME] -i [INPUT_REGION_GFF] -o [OUTPUT_FOLDER]")

    parser.add_option("-i", "--i", dest="input", nargs=1, default=None,
                      help="Enter a .gff or .bed file of binding sites used to make enhancers")
    parser.add_option("-o", "--out", dest="out", nargs=1, default=None,
                      help="Enter an output folder")
    parser.add_option("-g", "--genome", dest="genome", default=None,
                      help="Enter the genome build (MM9,MM8,HG18,HG19,HG38)")
    parser.add_option("-s", "--stitch", dest="stitch", nargs=1, default=12500,
                      help="Enter a max linking distance for stitching")
    parser.add_option("-t", "--tss", dest="tss", nargs=1, default=0,
                      help="Enter a distance from TSS to exclude. 0 = no TSS exclusion")

    options, args = parser.parse_args()

    input_gff_file = options.input

    stitch_window = int(options.stitch)

    tss_window = int(options.tss)
    if tss_window != 0:
        remove_tss = True
    else:
        remove_tss = False

    # GETTING THE BOUND REGION FILE USED TO DEFINE ENHANCERS
    print(f'Using {input_gff_file} as the input gff')
    input_name = input_gff_file.split('/')[-1].split('.')[0]

    # Get annotation file
    annot_file = options.genome
    print(f'Using {annot_file} as the genome')

    print('Making start dict')
    start_dict = make_start_dict(annot_file)

    print('Stitching regions together')
    stitched_collection = region_stitching(input_gff_file, stitch_window, tss_window, annot_file, remove_tss)

    print('Making GFF from stitched collection')
    stitched_gff = locus_collection_to_gff(stitched_collection)

    stitched_gff_file = options.out

    print(f'Writing stitched GFF to disk as {stitched_gff_file}')
    unparse_table(stitched_gff, stitched_gff_file, '\t')


if __name__ == '__main__':
    main()
