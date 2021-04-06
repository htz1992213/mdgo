# coding: utf-8
# Copyright (c) Tingzheng Hou.
# Distributed under the terms of the MIT License.

import numpy as np
from tqdm import tqdm_notebook
from MDAnalysis.analysis.distances import distance_array
from scipy.signal import savgol_filter
from mdgo.util import atom_vec

MM_of_Elements = {'H': 1.00794, 'He': 4.002602, 'Li': 6.941, 'Be': 9.012182,
                  'B': 10.811, 'C': 12.0107, 'N': 14.0067, 'O': 15.9994,
                  'F': 18.9984032, 'Ne': 20.1797, 'Na': 22.98976928,
                  'Mg': 24.305, 'Al': 26.9815386, 'Si': 28.0855, 'P': 30.973762,
                  'S': 32.065, 'Cl': 35.453, 'Ar': 39.948, 'K': 39.0983,
                  'Ca': 40.078, 'Sc': 44.955912, 'Ti': 47.867, 'V': 50.9415,
                  'Cr': 51.9961, 'Mn': 54.938045, 'Fe': 55.845, 'Co': 58.933195,
                  'Ni': 58.6934, 'Cu': 63.546, 'Zn': 65.409, 'Ga': 69.723,
                  'Ge': 72.64, 'As': 74.9216, 'Se': 78.96, 'Br': 79.904,
                  'Kr': 83.798, 'Rb': 85.4678, 'Sr': 87.62, 'Y': 88.90585,
                  'Zr': 91.224, 'Nb': 92.90638, 'Mo': 95.94, 'Tc': 98.9063,
                  'Ru': 101.07, 'Rh': 102.9055, 'Pd': 106.42, 'Ag': 107.8682,
                  'Cd': 112.411, 'In': 114.818, 'Sn': 118.71, 'Sb': 121.760,
                  'Te': 127.6, 'I': 126.90447, 'Xe': 131.293, 'Cs': 132.9054519,
                  'Ba': 137.327, 'La': 138.90547, 'Ce': 140.116,
                  'Pr': 140.90465, 'Nd': 144.242, 'Pm': 146.9151, 'Sm': 150.36,
                  'Eu': 151.964, 'Gd': 157.25, 'Tb': 158.92535, 'Dy': 162.5,
                  'Ho': 164.93032, 'Er': 167.259, 'Tm': 168.93421, 'Yb': 173.04,
                  'Lu': 174.967, 'Hf': 178.49, 'Ta': 180.9479, 'W': 183.84,
                  'Re': 186.207, 'Os': 190.23, 'Ir': 192.217, 'Pt': 195.084,
                  'Au': 196.966569, 'Hg': 200.59, 'Tl': 204.3833, 'Pb': 207.2,
                  'Bi': 208.9804, 'Po': 208.9824, 'At': 209.9871,
                  'Rn': 222.0176, 'Fr': 223.0197, 'Ra': 226.0254,
                  'Ac': 227.0278, 'Th': 232.03806, 'Pa': 231.03588,
                  'U': 238.02891, 'Np': 237.0482, 'Pu': 244.0642,
                  'Am': 243.0614, 'Cm': 247.0703, 'Bk': 247.0703,
                  'Cf': 251.0796, 'Es': 252.0829, 'Fm': 257.0951,
                  'Md': 258.0951, 'No': 259.1009, 'Lr': 262, 'Rf': 267,
                  'Db': 268, 'Sg': 271, 'Bh': 270, 'Hs': 269, 'Mt': 278,
                  'Ds': 281, 'Rg': 281, 'Cn': 285, 'Nh': 284, 'Fl': 289,
                  'Mc': 289, 'Lv': 292, 'Ts': 294, 'Og': 294, 'ZERO': 0}
__author__ = "Tingzheng Hou"
__version__ = "1.0"
__maintainer__ = "Tingzheng Hou"
__email__ = "tingzheng_hou@berkeley.edu"
__date__ = "Feb 9, 2021"


def trajectory(nvt_run, li_atom, run_start, run_end, species, selection_dict,
               distance):
    dist_values = {}
    time_count = 0
    trj_analysis = nvt_run.trajectory[run_start:run_end:]
    if species not in list(selection_dict):
        print('Invalid species selection')
        return None
    for ts in trj_analysis:
        selection = "(" + selection_dict[species] + ") and (around " \
                    + str(distance) + " index " \
                    + str(li_atom.id - 1) + ")"
        shell = nvt_run.select_atoms(selection, periodic=True)
        for atom in shell.atoms:
            if str(atom.id) not in dist_values:
                dist_values[str(atom.id)] = np.full(run_end-run_start, 100.)
        time_count += 1
    time_count = 0
    for ts in trj_analysis:
        for atomid in dist_values.keys():
            dist = distance_array(
                ts[li_atom.id-1], ts[(int(atomid)-1)], ts.dimensions
            )
            dist_values[atomid][time_count] = dist
        time_count += 1
    return dist_values


def find_nearest(trj, time_step, distance, hopping_cutoff, smooth=51):
    time_span = len(list(trj.values())[0])
    for kw in list(trj):
        trj[kw] = savgol_filter(trj.get(kw), smooth, 2)
    site_distance = [100 for _ in range(time_span)]
    sites = [0 for _ in range(time_span)]
    sites[0] = min(trj, key=lambda k: trj[k][0])
    site_distance[0] = trj.get(sites[0])[0]
    for time in range(1, time_span):
        if sites[time - 1] == 0:
            old_site_distance = 100
        else:
            old_site_distance = trj.get(sites[time - 1])[time]
        if old_site_distance > hopping_cutoff:
            new_site = min(trj, key=lambda k: trj[k][time])
            new_site_distance = trj.get(new_site)[time]
            if new_site_distance > distance:
                site_distance[time] = 100
            else:
                sites[time] = new_site
                site_distance[time] = new_site_distance
        else:
            sites[time] = sites[time - 1]
            site_distance[time] = old_site_distance
    sites = [int(i) for i in sites]
    sites_and_distance_array = np.array([[sites[i], site_distance[i]]
                                         for i in range(len(sites))])
    steps = []
    closest_step = 0
    previous_site = sites_and_distance_array[0][0]
    for i, step in enumerate(sites_and_distance_array):
        site = step[0]
        distance = step[1]
        if site == 0:
            pass
        else:
            if site == previous_site:
                if distance < sites_and_distance_array[closest_step][1]:
                    closest_step = i
                else:
                    pass
            else:
                steps.append(closest_step)
                closest_step = i
                previous_site = site
    if previous_site is not None:
        steps.append(closest_step)
    # change = len(steps) - 1
    change = (np.diff([i for i in sites if i != 0]) != 0).sum()
    frequency = change / (time_span * time_step)
    return sites, frequency, steps


def heat_map(nvt_run, li_atom, sites, dist_to_center, bind_atom_type,
             cartesian_by_ref, run_start, run_end):
    trj_analysis = nvt_run.trajectory[run_start:run_end:]
    coordinates = []
    for i, ts in enumerate(trj_analysis):
        if sites[i] == 0:
            pass
        else:
            center_atom = nvt_run.select_atoms("index " + str(sites[i] - 1))[0]
            selection = "(" + bind_atom_type + ") and " + "(around " \
                        + str(dist_to_center) + " index " \
                        + str(center_atom.id - 1) + ")"
            bind_atoms = nvt_run.select_atoms(selection, periodic=True)
            distances = distance_array(ts[li_atom.id - 1], bind_atoms.positions,
                                       ts.dimensions)
            idx = np.argpartition(distances[0], 3)
            vertex_atoms = bind_atoms[idx[:3]]
            vector_li = atom_vec(li_atom, center_atom, ts.dimensions)
            vector_a = atom_vec(vertex_atoms[0], center_atom, ts.dimensions)
            vector_b = atom_vec(vertex_atoms[1], center_atom, ts.dimensions)
            vector_c = atom_vec(vertex_atoms[2], center_atom, ts.dimensions)
            basis_abc = np.transpose([vector_a, vector_b, vector_c])
            abc_li = np.linalg.solve(basis_abc, vector_li)
            unit_x = np.linalg.norm(cartesian_by_ref[0, 0] * vector_a
                                    + cartesian_by_ref[0, 1] * vector_b
                                    + cartesian_by_ref[0, 2] * vector_c)
            unit_y = np.linalg.norm(cartesian_by_ref[1, 0] * vector_a
                                    + cartesian_by_ref[1, 1] * vector_b
                                    + cartesian_by_ref[1, 2] * vector_c)
            unit_z = np.linalg.norm(cartesian_by_ref[2, 0] * vector_a
                                    + cartesian_by_ref[2, 1] * vector_b
                                    + cartesian_by_ref[2, 2] * vector_c)
            vector_x = cartesian_by_ref[0] / unit_x
            vector_y = cartesian_by_ref[1] / unit_y
            vector_z = cartesian_by_ref[2] / unit_z
            basis_xyz = np.transpose([vector_x, vector_y, vector_z])
            xyz_li = np.linalg.solve(basis_xyz, abc_li)
            coordinates.append(xyz_li)
    return np.array(coordinates)


def get_full_coords(coords, reflection=None, rotation=None, inversion=None,
                    sample=None):
    coords_full = coords
    if reflection:
        for vec in reflection:
            coords_full = np.concatenate((coords, coords * vec), axis=0)
    if rotation:
        coords_copy = coords_full
        for mat in rotation:
            coords_rot = np.dot(coords_copy, mat)
            coords_full = np.concatenate((coords_full, coords_rot), axis=0)
    if inversion:
        coords_copy = coords_full
        for mat in inversion:
            coords_inv = np.dot(coords_copy, mat)
            coords_full = np.concatenate((coords_full, coords_inv), axis=0)
    if sample:
        index = np.random.choice(coords_full.shape[0], sample, replace=False)
        coords_full = coords_full[index]
    return coords_full


def cluster_coordinates(nvt_run, select_dict, run_start, run_end, species,
                        distance, basis_vectors=None, cluster_center="center"):
    trj_analysis = nvt_run.trajectory[run_start:run_end:]
    cluster_center = nvt_run.select_atoms(select_dict[cluster_center],
                                          periodic=True)[0]
    selection = "(" + " or ".join([s for s in species]) \
                + ") and (around " + str(distance) + " index " \
                + str(cluster_center.id - 1) + ")"
    print(selection)
    shell = nvt_run.select_atoms(selection, periodic=True)
    cluster = []
    for atom in shell:
        coord_list = []
        for ts in trj_analysis:
            coord_list.append(atom.position)
        cluster.append(np.mean(np.array(coord_list), axis=0))
    cluster = np.array(cluster)
    if basis_vectors:
        if len(basis_vectors) == 2:
            vec1 = basis_vectors[0]
            vec2 = basis_vectors[1]
            vec3 = np.cross(vec1, vec2)
            vec2 = np.cross(vec1, vec3)
        elif len(basis_vectors) == 3:
            vec1 = basis_vectors[0]
            vec2 = basis_vectors[1]
            vec3 = basis_vectors[2]
        else:
            raise ValueError("incorrect vector format")
        vec1 = vec1 / np.linalg.norm(vec1)
        vec2 = vec2 / np.linalg.norm(vec2)
        vec3 = vec3 / np.linalg.norm(vec3)
        basis_xyz = np.transpose([vec1, vec2, vec3])
        cluster_norm = np.linalg.solve(basis_xyz, cluster.T).T
        cluster_norm = cluster_norm - np.mean(cluster_norm, axis=0)
        return cluster_norm
    else:
        return cluster


def num_of_neighbor_one_li(nvt_run, li_atom, species_dict, select_dict,
                           run_start, run_end, write=False,
                           structure_code=None, write_freq=0,
                           write_path=None, element_id_dict=None):

    time_count = 0
    trj_analysis = nvt_run.trajectory[run_start:run_end:]
    cn_values = dict()
    species = list(species_dict.keys())
    for kw in species:
        if kw in select_dict.keys():
            cn_values[kw] = np.zeros(int(len(trj_analysis)))
        else:
            print('Invalid species selection')
            return None
    cn_values["total"] = np.zeros(int(len(trj_analysis)))
    for ts in trj_analysis:
        digit_of_species = len(species) - 1
        for kw in species:
            selection = "(" + select_dict[kw] + ") and (around "\
                        + str(species_dict[kw]) + " index "\
                        + str(li_atom.id - 1) + ")"
            shell = nvt_run.select_atoms(selection, periodic=True)
            # for each atom in shell, create/add to dictionary
            # (key = atom id, value = list of values for step function)
            for _ in shell.atoms:
                cn_values[kw][time_count] += 1
                cn_values["total"][time_count] += 10**digit_of_species
            digit_of_species = digit_of_species - 1
        if write and cn_values["total"][time_count] == structure_code:
            a = np.random.random()
            if a > 1 - write_freq:
                print("writing")
                species = ' or '.join("(same resid as (" + select_dict[kw]
                                      + " and around " + str(species_dict[kw])
                                      + " index " + str(li_atom.id - 1)
                                      + "))" for kw in species)
                species = "((" + species + ")and not " \
                          + select_dict["cation"] + ")"
                structure = nvt_run.select_atoms(species,
                                                 periodic=True)
                li_pos = ts[(int(li_atom.id)-1)]
                path = write_path + str(li_atom.id) + "_" + str(int(ts.time)) \
                    + "_" + str(structure_code) + ".xyz"
                write_out(li_pos, structure, element_id_dict, path)
        time_count += 1
    return cn_values


def num_of_neighbor_one_li_simple(
        nvt_run, li_atom, species_dict, select_dict, run_start, run_end
):

    time_count = 0
    trj_analysis = nvt_run.trajectory[run_start:run_end:]
    species = species_dict.keys()[0]
    if species in select_dict.keys():
        cn_values = np.zeros(int(len(trj_analysis)))
    else:
        print('Invalid species selection')
        return None
    for ts in trj_analysis:
        selection = "(" + select_dict[species] + ") and (around "\
                    + str(species_dict.get(species)) + " index "\
                    + str(li_atom.id - 1) + ")"
        shell = nvt_run.select_atoms(selection, periodic=True)
        shell_len = len(shell)
        if shell_len == 0:
            cn_values[time_count] = 1
        elif shell_len == 1:
            selection_species = "(" + select_dict["cation"] + " and around " + \
                                str(species_dict.get(species)) + " index " + \
                                str(shell.atoms[0].id - 1) + ")"
            shell_species = nvt_run.select_atoms(selection_species,
                                                 periodic=True)
            shell_species_len = len(shell_species) - 1
            if shell_species_len == 0:
                cn_values[time_count] = 2
            else:
                cn_values[time_count] = 3
        else:
            cn_values[time_count] = 3
        time_count += 1
    cn_values = {"total": cn_values}
    return cn_values


def num_of_neighbor_one_li_simple_extra(nvt_run, li_atom, species, select_dict,
                                        distance, run_start, run_end):

    time_count = 0
    emc_angle = list()
    ec_angle = list()
    trj_analysis = nvt_run.trajectory[run_start:run_end:]
    if species in select_dict.keys():
        cn_values = np.zeros(int(len(trj_analysis)))
    else:
        print('Invalid species selection')
        return None
    for ts in trj_analysis:
        selection = "(" + select_dict[species] + ") and (around " \
                    + str(distance) + " index " \
                    + str(li_atom.id - 1) + ")"
        shell = nvt_run.select_atoms(selection, periodic=True)
        shell_len = len(shell)
        if shell_len == 0:
            cn_values[time_count] = 1
        elif shell_len == 1:
            selection_species = "(" + select_dict["cation"] + " and around " + \
                                str(distance) + " index " + \
                                str(shell.atoms[0].id - 1) + ")"
            shell_species = nvt_run.select_atoms(selection_species,
                                                 periodic=True)
            shell_species_len = len(shell_species) - 1
            if shell_species_len == 0:
                cn_values[time_count] = 2
                li_pos = li_atom.position
                p_pos = shell.atoms[0].position
                ec_select = "(" + select_dict["EC"] + ") and (around "\
                    + str(3) + " index "\
                    + str(li_atom.id - 1) + ")"
                emc_select = "(" + select_dict["EMC"] + ") and (around "\
                    + str(3) + " index "\
                    + str(li_atom.id - 1) + ")"
                ec_group = nvt_run.select_atoms(ec_select, periodic=True)
                emc_group = nvt_run.select_atoms(emc_select, periodic=True)
                for atom in ec_group.atoms:
                    theta = angle(p_pos, li_pos, atom.position)
                    ec_angle.append(theta)
                for atom in emc_group.atoms:
                    theta = angle(p_pos, li_pos, atom.position)
                    emc_angle.append(theta)
            else:
                cn_values[time_count] = 3
        else:
            cn_values[time_count] = 3
        time_count += 1
    return cn_values, np.array(ec_angle), np.array(emc_angle)


def num_of_neighbor_one_li_simple_extra_two(nvt_run, li_atom, species_list,
                                            select_dict, distances, run_start,
                                            run_end):
    time_count = 0
    trj_analysis = nvt_run.trajectory[run_start:run_end:]
    cip_step = list()
    ssip_step = list()
    agg_step = list()
    cn_values = dict()
    for kw in species_list:
        if kw in select_dict.keys():
            cn_values[kw] = np.zeros(int(len(trj_analysis)))
        else:
            print('Invalid species selection')
            return None
    cn_values["total"] = np.zeros(int(len(trj_analysis)))
    for ts in trj_analysis:
        digit_of_species = len(species_list) - 1
        for kw in species_list:
            selection = "(" + select_dict[kw] + ") and (around " \
                        + str(distances[kw]) + " index " \
                        + str(li_atom.id - 1) + ")"
            shell = nvt_run.select_atoms(selection, periodic=True)
            # for each atom in shell, create/add to dictionary
            # (key = atom id, value = list of values for step function)
            for _ in shell.atoms:
                cn_values[kw][time_count] += 1
                cn_values["total"][time_count] += 10 ** digit_of_species
            digit_of_species = digit_of_species - 1

        selection = "(" + select_dict["anion"] + ") and (around "\
                    + str(distances["anion"]) + " index "\
                    + str(li_atom.id - 1) + ")"
        shell = nvt_run.select_atoms(selection, periodic=True)
        shell_len = len(shell)
        if shell_len == 0:
            ssip_step.append(time_count)
        elif shell_len == 1:
            selection_species = "(" + select_dict["cation"] + " and around " + \
                                str(distances["anion"]) + " index " + \
                                str(shell.atoms[0].id - 1) + ")"
            shell_species = nvt_run.select_atoms(selection_species,
                                                 periodic=True)
            shell_species_len = len(shell_species) - 1
            if shell_species_len == 0:
                cip_step.append(time_count)
            else:
                agg_step.append(time_count)
        else:
            agg_step.append(time_count)
        time_count += 1
    cn_ssip = dict()
    cn_cip = dict()
    cn_agg = dict()
    for kw in species_list:
        cn_ssip[kw] = np.mean(cn_values[kw][ssip_step])
        cn_cip[kw] = np.mean(cn_values[kw][cip_step])
        cn_agg[kw] = np.mean(cn_values[kw][agg_step])
    return cn_ssip, cn_cip, cn_agg


def angle(a, b, c):
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    angle_in_radian = np.arccos(cosine_angle)
    return np.degrees(angle_in_radian)


# Depth-first traversal
def num_of_neighbor_one_li_complex(nvt_run, li_atom, species, selection_dict,
                                   distance, run_start, run_end):
    time_count = 0
    trj_analysis = nvt_run.trajectory[run_start:run_end:]
    cn_values = np.zeros((int(len(trj_analysis)), 4))
    for ts in trj_analysis:
        cation_list = [li_atom.id]
        anion_list = []
        shell = nvt_run.select_atoms("(" + selection_dict[species] +
                                     " and around " + str(distance)
                                     + " index " + str(li_atom.id - 1) + ")",
                                     periodic=True)
        for anion_1 in shell.atoms:
            if anion_1.resid not in anion_list:
                anion_list.append(anion_1.resid)
                cn_values[time_count][0] += 1
                shell_anion_1 = nvt_run.select_atoms(
                    "(type 17 and around 3 resid " + str(anion_1.resid) + ")",
                    periodic=True
                )
                for cation_2 in shell_anion_1:
                    if cation_2.id not in cation_list:
                        cation_list.append(cation_2.id)
                        cn_values[time_count][1] += 1
                        shell_cation_2 = nvt_run.select_atoms(
                            "(type 15 and around 3 index "
                            + str(cation_2.id - 1) + ")",
                            periodic=True
                        )
                        for anion_3 in shell_cation_2.atoms:
                            if anion_3.resid not in anion_list:
                                anion_list.append(anion_3.resid)
                                cn_values[time_count][2] += 1
                                shell_anion_3 = nvt_run.select_atoms(
                                    "(type 17 and around 3 resid "
                                    + str(anion_3.resid) + ")",
                                    periodic=True
                                )
                                for cation_4 in shell_anion_3:
                                    if cation_4.id not in cation_list:
                                        cation_list.append(cation_4.id)
                                        cn_values[time_count][3] += 1


def coord_shell_array(nvt_run, func, li_atoms, species_dict, select_dict,
                      run_start, run_end):
    """
    Args:
        nvt_run: MDAnalysis Universe
        func: One of the neighbor statistical method (num_of_neighbor_one_li,
            num_of_neighbor_one_li_simple)
        li_atoms: Atom group of the Li atoms.
        species_dict (dict): A dict of coordination cutoff distance
            of the interested species.
        select_dict: A dictionary of species selection.
        run_start (int): Start time step.
        run_end (int): End time step.
    """
    num_array = func(
        nvt_run, li_atoms[0], species_dict, select_dict, run_start, run_end
    )
    for li in tqdm_notebook(li_atoms[1::]):
        this_li = func(
            nvt_run, li, species_dict, select_dict, run_start, run_end
        )
        for kw in num_array.keys():
            num_array[kw] = np.concatenate((num_array.get(kw),
                                            this_li.get(kw)), axis=0)
    return num_array


def write_out(li_pos, selection, element_id_dict, path):
    lines = list()
    lines.append(str(len(selection) + 1))
    lines.append("")
    lines.append("Li 0.0000000 0.0000000 0.0000000")
    box = selection.dimensions
    half_box = np.array([box[0], box[1], box[2]])/2
    for atom in selection:
        locs = list()
        for i in range(3):
            loc = atom.position[i] - li_pos[i]
            if loc > half_box[i]:
                loc = loc - box[i]
            elif loc < -half_box[i]:
                loc = loc + box[i]
            else:
                pass
            locs.append(loc)
        line = element_id_dict.get(int(atom.type)) \
            + ' ' + ' '.join(str(loc) for loc in locs)
        lines.append(line)
    with open(path, "w") as xyz_file:
        xyz_file.write("\n".join(lines))
