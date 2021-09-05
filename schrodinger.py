import os
from pathlib import Path
import argparse
import pandas as pd

PROT_PREP = '/Program Files/Schrodinger2020-4/utilities/prepwizard'
PROT_ASSIGN = '/Program Files/Schrodinger2020-4/utilities/protassign'
PROT_IMPREF = '/Program Files/Schrodinger2020-4/utilities/impref'

LIG__PREP = '/Program Files/Schrodinger2020-4/ligprep'

parser = argparse.ArgumentParser()
parser.add_argument('--mode', default = 'protein', type=str, help='schrodinger mode : protein or ligand')
parser.add_argument('--input_table', default='target_pdb.csv', type=str)
parser.add_argument('--input_ligand', default='ligand.smi', type=str)
args = parser.parse_args() 

if args.mode == 'protein':
    # Open the .tsv file of Targets and PDB ids
    df = pd.read_csv(args.input_table, sep=',', header=0)
    df = df.dropna(subset = ['PDB'])
    gene_list = df['Target'].values.tolist()
    pdb_list = df['PDB'].values.tolist()
    pdb_valid = []

    # Download the PDB files (pdb-tools must be installed)
    print("Number of PDB names: ", len(pdb_list))
    for pdb, gene in zip(pdb_list, gene_list):
        PDB_PATH = f'{pdb}.pdb'
        #pdb = pdb.replace(" ", "")
        if pdb == 'SWISS': 
            print(f'This target {gene} may be available in SWISS. Please manually download and put it in your schrodinger folder')
            continue
        if not Path(PDB_PATH).is_file():
            try: 
                os.system(f'pdb_fetch {pdb} > {PDB_PATH}')
            except Exception as e: 
                print(f"Cannot fetch {pdb}", e)
                os.remove(PDB_PATH)
        if Path(PDB_PATH).is_file():
            pdb_valid.append(pdb)

    # Run Schrodinger's Protein Prep Wizard
    print("Number of valid PDBs: ", len(pdb_valid))
    #os.chdir('/opt/')
    # print(os.getcwd())
    for pdb in pdb_valid:
        PDB_PATH = f'{pdb}.pdb'
        PREP_OUT_PATH = f'{pdb}_prep.mae'
        ASSIGN_OUT_PATH = f'{pdb}_assign.mae'
        LOG_PATH = f'{pdb}.log'
        os.system(f'"{PROT_PREP}" -f 3 -fillsidechains -fillloops -delwater_hbond_cutoff 5 -minimize_adj_h {PDB_PATH} {PREP_OUT_PATH}')
        while os.path.isfile(PREP_OUT_PATH) == False:
            f = open(LOG_PATH)
            data = f.read()
            if 'Error' in data:
                print(f'{pdb}.pdb makes error. Schrodinger will skip this target')
                break
            if os.path.isfile(PREP_OUT_PATH) == True:
                break
        if os.path.isfile(PREP_OUT_PATH) == True:
            os.system(f'"{PROT_ASSIGN}" -propka_pH 7.0 -minimize {PREP_OUT_PATH} {ASSIGN_OUT_PATH}')
            while os.path.isfile(ASSIGN_OUT_PATH) == False:
                if os.path.isfile(ASSIGN_OUT_PATH) == True:
                    break
        if os.path.isfile(ASSIGN_OUT_PATH) == True:
            os.system(f'"{PROT_IMPREF}" -f 3 {ASSIGN_OUT_PATH}')
            
if args.mode == 'ligand':
    # Run Schrodinger's LigPrep
    LIG_PATH = args.input_ligand
    OUT_PATH = f'{args.input_ligand}_prep.mae'
    os.system(f'"{LIG__PREP}" -epik -ph 7.0 -pht 2.0 -s 1 -bff 16 -ismi {LIG_PATH} -omae {OUT_PATH}')
