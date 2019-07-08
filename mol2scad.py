#!/usr/bin/env python3

"""
Tool for turning molecular coordinates into SCAD files
Takes molfile / sdf coordinates as input, outputs a scad file for OpenSCAD
"""

__author__ = "Andrew J. Bonham"
__version__ = 0.1
__status__ = "Development"

# Based on on makebucky.scad at http://www.thingiverse.com/thing:12675

# Useful tool:  http://cccbdb.nist.gov/mdlmol1.asp


# Import Dependencies

import sys
import getopt

# Main Function


def main(argv):

    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])

    except getopt.GetoptError:
        print("mol2scad.py -i <input molfile> -o <output scadfile>")
        sys.exit(2)

    if len(opts) == 0:
        print("mol2scad.py -i <input molfile> -o <output scadfile>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print("mol2scad.py -i <input molfile> -o <output scadfile>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        else:
            sys.exit(2)

    # Import file

    lines_tabbed = []

    with open(inputfile) as file_object:
        lines_list = file_object.readlines()
        for line in lines_list:
            column = line.split()
            lines_tabbed.append(column)

    # Remove unneeded lines
    index_removal_one = [i for i, v in enumerate(lines_tabbed) if len(v) < 4]

    lines_tabbed = [
        v for i, v in enumerate(lines_tabbed) if i not in (tuple(index_removal_one))
    ]

    # Split off atoms and bonds lines

    atoms_list = [v for i, v in enumerate(lines_tabbed) if v[3].isalpha() is True]

    bonds_list = [
        v
        for i, v in enumerate(lines_tabbed)
        if v[0].isdigit() is True
        and v[1].isdigit() is True
        and v[2].isdigit() is True
        and i != 0
    ]

    #  Atoms output
    output_atoms = []

    for i, row in enumerate(atoms_list):
        if row[3] == "H":
            atomsize = ".4"
        else:
            atomsize = ".6"

        output_atoms.append(
            "atom({0}, {1}, {2}, {3}); // {4} \n".format(
                atomsize, row[0], row[1], row[2], i + 1
            )
        )

    output_one = "".join(output_atoms)

    # Bonds output

    output_bonds = []

    for row in bonds_list:
        part_one = atoms_list[int(row[0]) - 1]
        part_two = atoms_list[int(row[1]) - 1]
        output_bonds.append(
            "bond( {0}, {1}, {2}, {3}, {4}, {5}); // {6} - {7} \n".format(
                part_one[0],
                part_one[1],
                part_one[2],
                part_two[0],
                part_two[1],
                part_two[2],
                str(int(row[0])),
                str(int(row[1])),
            )
        )

    output_two = "".join(output_bonds)

    COMMON_START = """/*

Creates a model of a molcule from a set
of orthogonal coordinates

*/

module atom(rx,x0,y0,z0)
{
translate(v=[x0,y0,z0])
sphere(r=rx,$fn=10);
}

/* spheres of radius rx are placed at the atomic
positions - x0,y0,z0
*/



module bond(x2,y2,z2,x1,y1,z1)

{
tx = (x2 + x1)/2;
ty = (y2 + y1)/2;
tz = (z2 + z1)/2;
ax = x2 - x1 ;
ay = y2 - y1;
az = z2 - z1;

translate(v=[tx,ty,tz])
// rotate command by d moews -
rotate(a = [-acos(az/sqrt(ax*ax+ay*ay+az*az)), 0, -atan2(ax, ay)])
cylinder(r=.2,h=sqrt(ax*ax+ay*ay+az*az),center=true,$fn=10);
}



union()
{
    """

    output = COMMON_START + output_one + output_two + """}"""

    # Write the file

    with open(outputfile, "w") as f:
        f.write(output)


# Main magic

if __name__ == "__main__":
    main(sys.argv[1:])
