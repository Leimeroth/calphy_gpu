"""
Main kernel methods for pytint

There are two modes of operation:

- The basic one in which the temperature will be split on regular intervals
  and an integration calculation is done at each point.

- Reversible scaling mode in which one integration calculation will be done
  and one reversible scaling calculation will be done.

"""
import os
import numpy as np
import time
import yaml
import warnings

from pytint.input import read_yamlfile, create_identifier
import pytint.queue as pq
import argparse as ap
import pytint.lattice as pl




def run_jobs(options):
    """
    Spawn jobs which are submitted to cluster

    Parameters
    ----------
    options : dict
        dict containing input options
    
    Returns
    -------
    None
    """
    
    #the jobs are well set up in calculations dict now
    #Step 1 - loop over calcs dict
    #Step 2 - check input structure of calc and create lattice if needed
    #Step 3 - Submit job

    print("Total number of %d calculations found" % len(options["calculations"]))

    for count, calc in enumerate(options["calculations"]):
        #check lattice
        #Check lattice values
        lattice = calc["lattice"].upper()
        if lattice in ["BCC", "FCC", "HCP", "DIA", "SC", "LQD"]:
            #process lattice
            lattice_constants, atoms_per_cell, lammps_lattice = pl.get_lattice(element, lattice)
        elif os.path.exists(calc["lattice"]):
            #its a file - do something
            lammps_lattice = "file"
        else:
            raise ValueError("Unknown lattice found. Allowed options are BCC, FCC, HCP, DIA, SC or LQD; or an input file.")

        identistring = create_identifier(calc)
        scriptpath = os.path.join(os.getcwd(), ".".join([identistring, "sub"]))
        errfile = os.path.join(os.getcwd(), ".".join([identistring, "err"]))

        #get the other info which is required
        apc = atoms_per_cell[count]
        a = lattice_constants[count]
        ml = lammps_lattice[count]

        #the below part assigns the schedulers
        #now we have to write the submission scripts for the job
        #parse Queue and import module
        if options["queue"]["scheduler"] == "local":
            scheduler = pq.Local(options["queue"], cores=options["queue"]["cores"])
        elif options["queue"]["scheduler"] == "slurm":
            scheduler = pq.SLURM(options["queue"], cores=options["queue"]["cores"])
        elif options["queue"]["scheduler"] == "sge":
            scheduler = pq.SGE(options["queue"], cores=options["queue"]["cores"])
        else:
            raise ValueError("Unknown scheduler")

        #for lattice just provide the number of position
        scheduler.maincommand = "tint_kernel -i %s -t %f -p %f -l %s -apc %d -a %f -c %f -m %s"%(inputfile, 
            t, p, l, apc, a, c, ml)
        scheduler.write_script(scriptpath)
        _ = scheduler.submit()



def main():
    """
    Main method to parse arguments and run jobs

    Paramaters
    ----------
    None

    Returns
    -------
    None
    """
    arg = ap.ArgumentParser()
    
    #argument name of input file
    arg.add_argument("-i", "--input", required=True, type=str,
    help="name of the input file")
    
    #parse args
    args = vars(arg.parse_args())

    #read the input file
    options = read_yamlfile(args["input"])

    #spawn job
    run_jobs(options)
