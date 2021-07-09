
from mendeleev import element
import os
from pylammpsmpi import LammpsLibrary
import numpy as np
import pyscal.core as pc
from calphy.helpers import create_object

"""
Conversion factors for creating initial lattices
"""
latticedict = {
    "BCC" :{"LQD": 1.00000, "BCC":1.00000, "FCC":0.79370, "HCP":1.12246, "DIA":0.62996, "SC":1.25992, "N":2},
    "FCC" :{"LQD": 1.00000, "BCC":1.25992, "FCC":1.00000, "HCP":1.78179, "DIA":0.79370, "SC":1.58740, "N":4},
    "HCP" :{"LQD": 1.00000, "BCC":0.89090, "FCC":0.79370, "HCP":1.00000, "DIA":0.62996, "SC":0.89089, "N":4},
    "DIA" :{"LQD": 1.00000, "BCC":1.58740, "FCC":0.79370, "HCP":1.25992, "DIA":1.00000, "SC":2.00000, "N":8},
    "SC"  :{"LQD": 1.00000, "BCC":0.79370, "FCC":0.62996, "HCP":1.12247, "DIA":0.50000, "SC":1.00000, "N":1},
}

def get_lattice(symbol, lat):
    """
    Find lattice constants of an element

    Parameters
    ----------
    symbol : string
        symbol of chemical element

    lattice_list : list of strings
        list of lattices

    Returns
    -------
    lattice_constants : list of floats
        list of lattice constant values

    atoms_per_cell : list of ints
        number of atoms per cell

    lammps_lattice : list of strings
        the main lattice to be used in lammps
    """

    chem = element(symbol)
    
    mainlat = chem.lattice_structure
    
    if mainlat == "HEX":
        mainlat = "HCP"

    mainalat = chem.lattice_constant

    #print(mainlat, lat)
    newlat = latticedict[mainlat][lat]*mainalat
    lattice_constant = newlat

    if lat == "LQD":
        atoms_per_cell = latticedict[mainlat]["N"]
        lammps_lattice = mainlat.lower()    
    else:
        atoms_per_cell = latticedict[lat]["N"]
        lammps_lattice = lat.lower()

    return lattice_constant, atoms_per_cell, lammps_lattice

def check_data_file(infile):
    if os.path.exists(infile):
        try:
            lmp = create_object(1, os.getcwd(), 0.001)
            lmp.read_data(infile)
            natoms = lmp.natoms
            #now we convert to a dump file and read the concentration
            trajfile = ".".join([infile, "dump"])
            lmp.command("mass * 1.0")
            lmp.dump("2 all custom", 1, trajfile,"id type x y z")
            lmp.run(0)
            lmp.undump(2)
            #now use pyscal to read it in,
            sys = pc.System()
            sys.read_inputfile(trajfile)
            atoms = sys.atoms
            types = [atom.type for atom in atoms]
            xx, xxcounts = np.unique(types, return_counts=True)
            conc = xxcounts/np.sum(xxcounts)
            lmp.close()
            return natoms, conc
        except:
            raise TypeError("LAMMPS could not read in the data file. Please check!")
    else:
        raise FileNotFoundError("File not found!")


def prepare_lattice(calc):
    #process lattice
    lattice = calc["lattice"].upper()
    
    if lattice in ["BCC", "FCC", "HCP", "DIA", "SC", "LQD"]:
        #process lattice
        #throw error for multicomponent
        if calc["nelements"] > 1:
            raise ValueError("Only files supported for multicomponent")

        alat, apc, l = get_lattice(calc["element"][0], calc["lattice"])

        #replace lattice constant
        if calc["lattice_constant"] != 0:
            alat = calc["lattice_constant"]
        
        conc = [1,]

    elif os.path.exists(calc["lattice"]):
        natoms, conc = check_data_file(calc["lattice"]) 
        #its a file - do something
        l = "file"
        alat = 1.00
        apc = natoms
    else:
        raise ValueError("Unknown lattice found. Allowed options are BCC, FCC, HCP, DIA, SC or LQD; or an input file.")
    
    if l == "dia":
        l = "diamond"

    return l, alat, apc, conc
